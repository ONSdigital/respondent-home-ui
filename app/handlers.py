import logging

import aiohttp_jinja2
from aiohttp.client_exceptions import ClientConnectionError, ClientConnectorError, ClientResponseError
from aiohttp.web import HTTPFound, RouteTableDef, View, json_response
from sdc.crypto.encrypter import encrypt
from structlog import wrap_logger

from . import BAD_CODE_MSG, BAD_RESPONSE_MSG, CODE_USED_MSG, INVALID_CODE_MSG, NOT_AUTHORIZED_MSG, VERSION
from .case import get_case, post_case_event
from .eq import EqPayloadConstructor
from .exceptions import InactiveCaseError, InvalidIACError
from .flash import flash


logger = wrap_logger(logging.getLogger("respondent-home"))
routes = RouteTableDef()


@routes.view('/info', name='info', use_prefix=False)
class Info(View):

    async def get(self):
        info = {
            "name": 'respondent-home-ui',
            "version": VERSION,
        }
        if 'check' in self.request.query:
            info["ready"] = await self.request.app.check_services()
        return json_response(info)


@routes.view('/', name='index')
class Index(View):

    def __init__(self, request):
        super(Index, self).__init__(request)
        self.client_ip = self.request.headers.get("X-Forwarded-For")
        self.iac = None

    @property
    def iac_url(self):
        return f"{self.request.app['IAC_URL']}/iacs/{self.iac}"

    @staticmethod
    def join_iac(data, expected_length=12):
        combined = "".join([v.lower() for v in data.values()][:3])
        if len(combined) < expected_length:
            raise TypeError
        return combined

    @staticmethod
    def validate_case(case_json):
        if not case_json.get("active", False):
            raise InactiveCaseError

    def redirect(self):
        raise HTTPFound(self.request.app.router['index'].url_for())

    async def get_iac_details(self):
        logger.info(f"Making GET request to {self.iac_url}", iac=self.iac, client_ip=self.client_ip)
        try:
            async with self.request.app.http_session_pool.get(self.iac_url, auth=self.request.app["IAC_AUTH"]) as resp:
                logger.info("Received response from IAC", iac=self.iac, status_code=resp.status)

                try:
                    resp.raise_for_status()
                except ClientResponseError as ex:
                    if resp.status == 404:
                        raise InvalidIACError
                    elif resp.status in (401, 403):
                        logger.info("Unauthorized access to IAC service attempted", client_ip=self.client_ip)
                        flash(self.request, NOT_AUTHORIZED_MSG)
                        return self.redirect()
                    elif 400 <= resp.status < 500:
                        logger.info(
                            "Client error when accessing IAC service",
                            client_ip=self.client_ip,
                            status=resp.status,
                        )
                        flash(self.request, BAD_RESPONSE_MSG)
                        return self.redirect()
                    else:
                        logger.error("Error in response", url=resp.url, status_code=resp.status)
                        raise ex
                else:
                    return await resp.json()
        except (ClientConnectionError, ClientConnectorError) as ex:
            logger.error("Client failed to connect to iac service", client_ip=self.client_ip)
            raise ex

    @aiohttp_jinja2.template('index.html')
    async def get(self):
        return {}

    @aiohttp_jinja2.template('index.html')
    async def post(self):
        """
        Main entry point to building an eQ payload as URL parameter.
        """
        data = await self.request.post()
        try:
            self.iac = self.join_iac(data)
        except TypeError:
            logger.warn("Attempt to use a malformed access code", client_ip=self.client_ip)
            flash(self.request, BAD_CODE_MSG)
            return self.redirect()

        try:
            iac_json = await self.get_iac_details()
        except InvalidIACError:
            logger.info("Attempt to use an invalid access code", client_ip=self.client_ip)
            flash(self.request, BAD_CODE_MSG)
            return aiohttp_jinja2.render_template("index.html", self.request, {}, status=202)

        try:
            self.validate_case(iac_json)
        except InactiveCaseError:
            logger.info("Attempt to use an inactive access code", client_ip=self.client_ip)
            flash(self.request, CODE_USED_MSG)
            return {}

        try:
            case_id = iac_json["caseId"]
        except KeyError:
            logger.error('caseId missing from IAC response', client_ip=self.client_ip)
            flash(self.request, BAD_RESPONSE_MSG)
            return {}

        case = await get_case(case_id, self.request.app)

        try:
            assert case['sampleUnitType'] == 'H'
        except AssertionError:
            logger.error('Attempt to use unexpected sample unit type', sample_unit_type=case['sampleUnitType'])
            flash(self.request, INVALID_CODE_MSG)
            return {}
        except KeyError:
            logger.error('sampleUnitType missing from case response', client_ip=self.client_ip)
            flash(self.request, BAD_RESPONSE_MSG)
            return {}

        eq_payload = await EqPayloadConstructor(case, self.request.app, self.iac).build()

        token = encrypt(eq_payload, key_store=self.request.app['key_store'], key_purpose="authentication")

        description = f"Instrument LMS launched for case {case_id}"
        await post_case_event(case_id, 'EQ_LAUNCH', description, self.request.app)

        logger.info('Redirecting to eQ', client_ip=self.client_ip)
        raise HTTPFound(f"{self.request.app['EQ_URL']}/session?token={token}")

import logging

import aiohttp_jinja2
from aiohttp.client_exceptions import ClientConnectionError, ClientConnectorError, ClientResponseError
from aiohttp.web import HTTPFound, RouteTableDef, json_response
from sdc.crypto.encrypter import encrypt
from structlog import wrap_logger

from . import (
    BAD_CODE_MSG, BAD_CODE_TYPE_MSG, BAD_RESPONSE_MSG, INVALID_CODE_MSG, NOT_AUTHORIZED_MSG, VERSION)
from .case import get_case, post_case_event
from .eq import EqPayloadConstructor
from .exceptions import CompletedCaseError, InvalidIACError, InactiveIACError
from .flash import flash


logger = wrap_logger(logging.getLogger("respondent-home"))
routes = RouteTableDef()


@routes.view('/info', use_prefix=False)
class Info:

    @staticmethod
    async def get(request):
        info = {
            "name": 'respondent-home-ui',
            "version": VERSION,
        }
        if 'check' in request.query:
            info["ready"] = await request.app.check_services()
        return json_response(info)


@routes.view('/')
class Index:

    def __init__(self):
        self.iac = None
        self.request = None

    @property
    def client_ip(self):
        if not hasattr(self, '_client_ip'):
            self._client_ip = self.request.headers.get("X-Forwarded-For")
        return self._client_ip

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
    def get_collex_id(case_json):
        try:
            return case_json['caseGroup']['collectionExerciseId']
        except KeyError:
            logger.warn("Failed to get collex_id from case_json['caseGroup']['collectionExerciseId']")

    @staticmethod
    def validate_iac_active(iac_json, case_json):
        if not iac_json.get("active", False):
            collex_id = Index.get_collex_id(case_json)

            try:
                if case_json['caseGroup']['caseGroupStatus'] == 'COMPLETE':
                    logger.info('Attempt to use inactive iac for completed case', collex_id=collex_id)
                    raise CompletedCaseError
            except KeyError:
                logger.warn("Field case_json['caseGroup']['caseGroupStatus'] not found")

            logger.info('Attempt to use inactive iac for incomplete case', collex_id=collex_id)
            raise InactiveIACError

    def check_case_sample_unit_type_valid(self, case_json):
        try:
            assert case_json['sampleUnitType'] == 'H'
        except AssertionError:
            logger.warn('Attempt to use unexpected sample unit type', sample_unit_type=case_json['sampleUnitType'])
            flash(self.request, BAD_CODE_TYPE_MSG)
            return False
        except KeyError:
            logger.error('sampleUnitType missing from case response', client_ip=self.client_ip)
            flash(self.request, BAD_RESPONSE_MSG)
            return False

        return True

    def redirect(self):
        raise HTTPFound(self.request.app.router['Index:get'].url_for())

    async def get_token(self, case_json):
        eq_payload = await EqPayloadConstructor(case_json, self.request.app, self.iac).build()
        return encrypt(eq_payload, key_store=self.request.app['key_store'], key_purpose="authentication")

    async def get_iac_details(self):
        logger.debug(f"Making GET request to {self.iac_url}", iac=self.iac, client_ip=self.client_ip)
        try:
            async with self.request.app.http_session_pool.get(self.iac_url, auth=self.request.app["IAC_AUTH"]) as resp:
                logger.debug("Received response from IAC", iac=self.iac, status_code=resp.status)

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
                        logger.warn(
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
    async def get(self, _):
        return {}

    @aiohttp_jinja2.template('index.html')
    async def post(self, request):
        """
        Main entry point to building an eQ payload as URL parameter.
        """
        self.request = request
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
            flash(self.request, INVALID_CODE_MSG)
            return aiohttp_jinja2.render_template("index.html", self.request, {}, status=202)

        try:
            case_id = iac_json["caseId"]
        except KeyError:
            logger.error('caseId missing from IAC response', client_ip=self.client_ip)
            flash(self.request, BAD_RESPONSE_MSG)
            return {}

        case_json = await get_case(case_id, self.request.app)

        self.validate_iac_active(iac_json, case_json)

        if not self.check_case_sample_unit_type_valid(case_json):
            return {}

        token = await self.get_token(case_json)

        description = f"Instrument LMS launched for case {case_id}"
        await post_case_event(case_id, 'EQ_LAUNCH', description, self.request.app)

        logger.info('Redirecting to eQ', client_ip=self.client_ip)
        raise HTTPFound(f"{self.request.app['EQ_URL']}/session?token={token}")


@routes.view('/cookies-privacy')
class CookiesPrivacy:
    @aiohttp_jinja2.template('cookies-privacy.html')
    async def get(self, _):
        return {}


@routes.view('/contact-us')
class ContactUs:
    @aiohttp_jinja2.template('contact-us.html')
    async def get(self, _):
        return {}

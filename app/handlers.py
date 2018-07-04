import logging

import aiohttp_jinja2
from aiohttp.web import HTTPFound, Response
from aiohttp.client_exceptions import ClientResponseError
from sdc.crypto.encrypter import encrypt
from structlog import wrap_logger

from .case import get_case, post_case_event
from .eq import EqPayloadConstructor
from .exceptions import InactiveCaseError
from .flash import flash


logger = wrap_logger(logging.getLogger("respondent-home"))


async def get_index(request, msg=None, redirect=False):
    if msg:
        flash(request, msg)

    if redirect:
        raise HTTPFound("/")

    response = aiohttp_jinja2.render_template("index.html", request, {})
    return response


async def get_info(request):
    return Response(text="")


def get_iac(data, expected_length=12):
    combined = "".join([v.lower() for v in data.values()][:3])
    if len(combined) < expected_length:
        raise TypeError
    return combined


async def post_index(request):
    client_ip = request.headers.get("X-Forwarded-For")
    data = await request.post()
    try:
        iac = get_iac(data)
    except TypeError:
        logger.warn("Attempt to use a malformed access code", client_ip=client_ip)
        return await get_index(
            request,
            msg="Please provide the unique access code printed on your invitation letter or form.",
            redirect=True,
        )
    iac_url = f"{request.app['IAC_URL']}/iacs/{iac}"

    async with request.app.http_session_pool.get(iac_url, auth=request.app["IAC_AUTH"]) as resp:
        logger.info("Received response from IAC", iac=iac, status_code=resp.status)

        try:
            resp.raise_for_status()
        except ClientResponseError as ex:
            if resp.status == 404:
                logger.info("Attempt to use an invalid access code", client_ip=client_ip)
                return await get_index(
                    request,
                    msg="Please provide the unique access code printed on your invitation letter or form.",
                    redirect=True,
                )
            elif resp.status == 401:
                logger.info("Unauthorized access to IAC service attempted", client_ip=client_ip)
                return await get_index(
                    request,
                    msg="You are not authorized to access this service.",
                    redirect=True,
                )
            elif 400 <= resp.status < 500:
                logger.info(
                    "Client error when accessing IAC service",
                    client_ip=client_ip,
                    status=resp.status,
                )
                flash(request, "Bad request. Please try again")
                return aiohttp_jinja2.render_template("index.html", request, {})
            else:
                raise ex

        try:
            await _validate_case(resp)
        except InactiveCaseError:
            logger.info("Attempt to use an inactive access code", client_ip=client_ip)
            flash(request, "The unique access code entered has already been used")
            return aiohttp_jinja2.render_template("index.html", request, {})

        case_json = await resp.json()
        case_id = case_json["caseId"]
        case = await get_case(case_id, request.app)

        eq_payload = await EqPayloadConstructor(case, request.app).build()

        token = encrypt(eq_payload, key_store=request.app['key_store'], key_purpose="authentication")

        description = f"Instrument LMS launched for case {case_id}"
        await post_case_event(case_id, 'EQ_LAUNCH', description, request.app)

        logger.info('Redirecting to eQ', client_ip=client_ip)
        return HTTPFound(request.app['EQ_URL'] + token)


async def _validate_case(response):
    resp_json = await response.json()
    if not resp_json["active"]:
        raise InactiveCaseError

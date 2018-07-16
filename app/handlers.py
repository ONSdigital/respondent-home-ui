import logging

import aiohttp_jinja2
from aiohttp.web import HTTPFound, Response, json_response
from aiohttp.client_exceptions import ClientConnectionError, ClientConnectorError, ClientResponseError
from sdc.crypto.encrypter import encrypt
from structlog import wrap_logger

from . import VERSION
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
    info = {
        "name": 'respondent-home-ui',
        "version": VERSION,
    }
    return json_response(info)


def join_iac(data, expected_length=12):
    combined = "".join([v.lower() for v in data.values()][:3])
    if len(combined) < expected_length:
        raise TypeError
    return combined


async def post_index(request):
    """
    Main entry point to building an eQ payload as URL parameter.
    """
    client_ip = request.headers.get("X-Forwarded-For")
    data = await request.post()
    try:
        iac = join_iac(data)
    except TypeError:
        logger.warn("Attempt to use a malformed access code", client_ip=client_ip)
        return await get_index(
            request,
            msg="Please provide the unique access code printed on your invitation letter or form.",
            redirect=True,
        )

    iac_json = await get_iac_details(request, iac, client_ip)

    try:
        validate_case(iac_json)
    except InactiveCaseError:
        logger.info("Attempt to use an inactive access code", client_ip=client_ip)
        flash(request, "The unique access code entered has already been used")
        return aiohttp_jinja2.render_template("index.html", request, {})

    try:
        case_id = iac_json["caseId"]
    except KeyError:
        logger.error('caseId missing from IAC response', client_ip=client_ip)
        flash(request, "Bad response from server. Please try again")
        return aiohttp_jinja2.render_template("index.html", request, {})

    case = await get_case(case_id, request.app)

    eq_payload = await EqPayloadConstructor(case, request.app).build()

    token = encrypt(eq_payload, key_store=request.app['key_store'], key_purpose="authentication")

    description = f"Instrument LMS launched for case {case_id}"
    await post_case_event(case_id, 'EQ_LAUNCH', description, request.app)

    logger.info('Redirecting to eQ', client_ip=client_ip)
    raise HTTPFound(request.app['EQ_URL'] + token)


def validate_case(case_json):
    if not case_json.get("active", False):
        raise InactiveCaseError


async def get_iac_details(request, iac: str, client_ip: str):
    logger.debug("Attempting to retrieve case details from iac service", iac=iac, client_ip=client_ip)
    iac_url = f"{request.app['IAC_URL']}/iacs/{iac}"
    try:
        async with request.app.http_session_pool.get(iac_url, auth=request.app["IAC_AUTH"]) as resp:
            logger.info("Received response from IAC", iac=iac, status_code=resp.status)

            try:
                resp.raise_for_status()
            except ClientResponseError as ex:
                if resp.status == 404:
                    logger.info("Attempt to use an invalid access code", client_ip=client_ip)
                    flash(request, "Please provide the unique access code printed on your invitation letter or form.")
                    raise HTTPFound("/")
                elif resp.status in (401, 403):
                    logger.info("Unauthorized access to IAC service attempted", client_ip=client_ip)
                    flash(request, "You are not authorized to access this service.")
                    raise HTTPFound("/")
                elif 400 <= resp.status < 500:
                    logger.info(
                        "Client error when accessing IAC service",
                        client_ip=client_ip,
                        status=resp.status,
                    )
                    flash(request, "Bad request. Please try again")
                    raise HTTPFound("/")
                else:
                    logger.error("Error in response", url=resp.url, status_code=resp.status)
                    raise ex
            else:
                return await resp.json()
    except (ClientConnectionError, ClientConnectorError) as ex:
        logger.error("Client failed to connect to iac service", client_ip=client_ip)
        raise ex

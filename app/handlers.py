import logging

import aiohttp_jinja2
from aiohttp.web import HTTPFound, Response
from aiohttp.client_exceptions import ClientResponseError
from structlog import wrap_logger

from .case import get_case
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


def get_iac(data):
    return "".join([v.lower() for v in data.values()][:3])


async def post_index(request):
    client_ip = request.headers.get("X-Forwarded-For")
    data = await request.post()
    iac = get_iac(data)
    iac_url = f"{request.app['IAC_URL']}/iacs/{iac}"

    async with request.app.http_session_pool.get(iac_url, auth=request.app["IAC_AUTH"]) as resp:
        logger.info("Received response from IAC", iac=f"{iac}", status_code=f"{resp.status}")

        try:
            resp.raise_for_status()
        except ClientResponseError as ex:
            if resp.status == 404:
                logger.info(f"Attempt to use an invalid access code from {client_ip}")
                rendered = await get_index(
                    request,
                    msg="Please provide the unique access code printed on your invitation letter or form.",
                    redirect=True,
                )
                return rendered
            elif resp.status == 401:
                logger.info(f"Unauthorized access to IAC service from {client_ip} attempted")
                rendered = await get_index(
                    request,
                    msg="You are not authorized to access this service.",
                    redirect=True,
                )
                return rendered
            elif 400 <= resp.status < 500:
                logger.info(
                    f"Client error when accessing IAC service from {client_ip}", status=resp.status
                )
                flash(request, "Bad request. Please try again")
                return aiohttp_jinja2.render_template("index.html", request, {})
            else:
                raise ex

        try:
            await _validate_case(resp)
        except InactiveCaseError:
            msg = f"Attempt to use an inactive access code from {client_ip}"
            logger.info(msg)
            flash(request, "The unique access code entered has already been used")
            return aiohttp_jinja2.render_template("index.html", request, {})

        case_json = await resp.json()
        case = await get_case(case_json["caseId"])
        eq_payload = await EqPayloadConstructor(case).build()

        return Response(text="Questionnaire post!")


@aiohttp_jinja2.template("base.html")
async def get_questionnaire(request):
    context = {"a_variable": 12}
    response = aiohttp_jinja2.render_template("base.html", request, context)
    return response


async def post_questionnaire(request):
    return Response(text="Questionnaire post!")


async def _validate_case(response):
    resp_json = await response.json()
    if not resp_json["active"]:
        raise InactiveCaseError

import logging

import aiohttp_jinja2
from aiohttp.web import HTTPFound
from aiohttp.web import Response
from aiohttp.client_exceptions import ClientResponseError
from structlog import wrap_logger

from .flash import flash


logger = wrap_logger(logging.getLogger("respondent-home"))


async def get_index(request):
    response = aiohttp_jinja2.render_template("index.html", request, {})
    return response


async def post_index(request):
    data = await request.post()
    iac = "".join([v.lower() for v in data.values()][:3])
    client_ip = request.headers.get("X-Forwarded-For")
    async with request.app.http_session_pool.get(
        f"{request.app['IAC_URL']}/iacs/{iac}", auth=request.app["IAC_AUTH"]
    ) as resp:
        logger.info("Received response from IAC", iac=f"{iac}", status_code=f"{resp.status}")

        try:
            resp.raise_for_status()
        except ClientResponseError as ex:
            if resp.status == 404:
                logger.info(f"Attempt to use an invalid access code from {client_ip}")
                flash(
                    request,
                    "Please provide the unique access code printed on your invitation letter or form.",
                )
                return aiohttp_jinja2.render_template("index.html", request, {})
            elif resp.status == 401:
                logger.info(f"Unauthorized access to IAC service from {client_ip} attempted")
                flash(request, "You are not authorized to access this service.")
                return aiohttp_jinja2.render_template("index.html", request, {})
            elif 400 <= resp.status < 500:
                logger.info(
                    f"Client error when accessing IAC service from {client_ip}", status=resp.status
                )
                flash(request, "Bad request. Please try again")
                return aiohttp_jinja2.render_template("index.html", request, {})
            else:
                raise ex

        return Response(text="Questionnaire post!")


@aiohttp_jinja2.template("base.html")
async def get_questionnaire(request):
    context = {"a_variable": 12}
    response = aiohttp_jinja2.render_template("base.html", request, context)
    return response


async def post_questionnaire(request):
    return Response(text="Questionnaire post!")

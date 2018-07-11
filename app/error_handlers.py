from functools import partial
import logging

import aiohttp_jinja2
from aiohttp import web
from aiohttp.client_exceptions import (
    ClientResponseError, ClientConnectorError, ClientConnectionError, ContentTypeError)
from structlog import wrap_logger

from .exceptions import InvalidEqPayLoad
from .flash import flash


logger = wrap_logger(logging.getLogger("respondent-home"))


def create_error_middleware(overrides):

    @web.middleware
    async def middleware_handler(request, handler):
        try:
            resp = await handler(request)
            override = overrides.get(resp.status)
            return await override(request) if override else resp
        except InvalidEqPayLoad as ex:
            return await eq_error(request, ex.message)
        except ClientConnectionError as ex:
            return await connection_error(request, ex.args[0])
        except ClientConnectorError as ex:
            return await connection_error(request, ex.os_error.strerror)
        except ContentTypeError as ex:
            return await payload_error(request, str(ex.request_info.url))
        except ClientResponseError as ex:
            return await response_error(request, ex.status)

    return middleware_handler


async def eq_error(request, message: str):
    logger.error("Service failed to build eQ payload", message=message)
    flash(request, "Failed to redirect to survey")
    return aiohttp_jinja2.render_template("index.html", request, {})


async def connection_error(request, message: str):
    logger.error("Service connection error", message=message)
    flash(request, "Service connection error")
    return aiohttp_jinja2.render_template("index.html", request, {})


async def payload_error(request, url: str):
    logger.error("Service failed to return expected JSON payload", url=url)
    flash(request, "Server error")
    return aiohttp_jinja2.render_template("index.html", request, {})


async def response_error(request, status: int):
    flash(request, f"{status} Server error")
    return aiohttp_jinja2.render_template("index.html", request, {})


def setup(app):
    overrides = {
        500: partial(response_error, status=500),
        503: partial(response_error, status=503)}
    error_middleware = create_error_middleware(overrides)
    app.middlewares.append(error_middleware)

import logging

import aiohttp_jinja2
from aiohttp import web
from aiohttp.client_exceptions import (
    ClientResponseError, ClientConnectorError, ClientConnectionError, ContentTypeError)
from structlog import wrap_logger

from .exceptions import ExerciseClosedError, CompletedCaseError, InvalidEqPayLoad, InactiveIACError

logger = wrap_logger(logging.getLogger("respondent-home"))


def create_error_middleware(overrides):

    @web.middleware
    async def middleware_handler(request, handler):
        try:
            resp = await handler(request)
            override = overrides.get(resp.status)
            return await override(request) if override else resp
        except web.HTTPNotFound:
            index_resource = request.app.router['Index:get']
            if request.path + '/' == index_resource.canonical:
                logger.debug('Redirecting to index', path=request.path)
                raise web.HTTPMovedPermanently(index_resource.url_for())
            return await not_found_error(request)
        except CompletedCaseError:
            return await completed_case(request)
        except InactiveIACError:
            return await inactive_iac(request)
        except ExerciseClosedError as ex:
            return await ce_closed(request, ex.collection_exercise_id)
        except InvalidEqPayLoad as ex:
            return await eq_error(request, ex.message)
        except ClientConnectionError as ex:
            return await connection_error(request, ex.args[0])
        except ClientConnectorError as ex:
            return await connection_error(request, ex.os_error.strerror)
        except ContentTypeError as ex:
            return await payload_error(request, str(ex.request_info.url))
        except ClientResponseError:
            return await response_error(request)

    return middleware_handler


async def completed_case(request):
    logger.info("Attempt to use an inactive iac for a completed case")
    return aiohttp_jinja2.render_template("completed.html", request, {})


async def inactive_iac(request):
    logger.info("Attempt to use an iac code that is inactive, malformed or iac_details missing active field")
    return aiohttp_jinja2.render_template("inactive-iac.html", request, {})


async def ce_closed(request, collex_id):
    logger.info("Attempt to access collection exercise that has already ended", collex_id=collex_id)
    return aiohttp_jinja2.render_template("closed.html", request, {})


async def eq_error(request, message: str):
    logger.error("Service failed to build eQ payload", message=message)
    return aiohttp_jinja2.render_template("error.html", request, {}, status=500)


async def connection_error(request, message: str):
    logger.error("Service connection error", message=message)
    return aiohttp_jinja2.render_template("error.html", request, {}, status=500)


async def payload_error(request, url: str):
    logger.error("Service failed to return expected JSON payload", url=url)
    return aiohttp_jinja2.render_template("error.html", request, {}, status=500)


async def response_error(request):
    return aiohttp_jinja2.render_template("error.html", request, {}, status=500)


async def not_found_error(request):
    return aiohttp_jinja2.render_template("404.html", request, {}, status=404)


def setup(app):
    overrides = {
        500: response_error,
        503: response_error,
        404: not_found_error,
    }
    error_middleware = create_error_middleware(overrides)
    app.middlewares.append(error_middleware)

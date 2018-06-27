import logging

import aiohttp_jinja2
from aiohttp import web
from aiohttp.client_exceptions import ClientResponseError

from .flash import flash

logger = logging.getLogger("respondent-home")


def create_error_middleware(overrides):

    @web.middleware
    async def middleware_handler(request, handler):
        try:
            resp = await handler(request)
            override = overrides.get(resp.status)
            if override:
                return await override(request)
            return resp
        except ClientResponseError as ex:
            override = overrides.get(ex.status)
            if override:
                return await override(request)
            raise

    return middleware_handler


async def handle_500(request):
    flash(request, "500 Server Error")
    return aiohttp_jinja2.render_template("index.html", request, {})


def setup(app):
    error_middleware = create_error_middleware({500: handle_500})
    app.middlewares.append(error_middleware)

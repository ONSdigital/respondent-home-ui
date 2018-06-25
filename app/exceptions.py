import logging

import aiohttp_jinja2
from aiohttp.client_exceptions import ServerConnectionError

from .flash import flash

logger = logging.getLogger("respondent-home")


async def error_middleware(app, handler):
    async def middleware_handler(request):
        try:
            return await handler(request)
        except ServerConnectionError as e:
            logger.error("Request {} has failed with exception: {}".format(request, repr(e)))
            flash(request, repr(e))
            return aiohttp_jinja2.render_template("index.html", request, {})
        except Exception as e:
            logger.warning("Request {} has failed with exception: {}".format(request, repr(e)))
            flash(request, repr(e))
            return aiohttp_jinja2.render_template("index.html", request, {})
    return middleware_handler

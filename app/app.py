import logging

import aiohttp_jinja2
import jinja2
from aiohttp import ClientSession
from aiohttp import web
from aiohttp_utils import negotiation
from structlog import wrap_logger

from . import config
from . import flash
from . import jwt
from . import routes
from . import session
from . import settings
from .app_logging import logger_initial_config

logger = wrap_logger(logging.getLogger("respondent-home"))
server_logger = logging.getLogger("aiohttp.server")

server_logger.setLevel("INFO")


async def on_startup(app):
    app.http_session_pool = ClientSession()


async def on_cleanup(app):
    app.http_session_pool.close()


def create_app() -> web.Application:
    """App factory. Sets up routes and all plugins.
    """
    app_config = config.Config()
    app_config.from_object(settings)

    app_config.from_object(getattr(config, app_config["ENV"]))

    app = web.Application(
        debug=settings.DEBUG, middlewares=[session.setup(), flash.flash_middleware]
    )

    # Store uppercased configuration variables on app
    app.update(app_config)

    # Bind logger
    logger_initial_config(service_name="respondent-home", log_level=app["LOG_LEVEL"])

    logger.info("Logging configured")

    # Set up routes
    routes.setup(app)

    # Use content negotiation middleware to render JSON responses
    negotiation.setup(app)

    # Setup jinja2 environment
    aiohttp_jinja2.setup(
        app,
        loader=jinja2.PackageLoader("app", "templates"),
        context_processors=[flash.context_processor, aiohttp_jinja2.request_processor],
    )

    logger.error(app["aiohttp_jinja2_context_processors"])

    logger.error(app['IAC_URL'])

    # Set static folder location
    # TODO: Only turn on in dev environment
    app["static_root_url"] = "/"
    app.router.add_static("/", "app/static", show_index=True)

    # JWT KeyStore
    app["key_store"] = jwt.key_store(app["JSON_SECRET_KEYS"])

    app.on_startup.append(on_startup)
    app.on_cleanup.append(on_cleanup)

    return app


if __name__ == "__main__":
    app = create_app()
    web.run_app(app, port=app["PORT"], access_log=logger)

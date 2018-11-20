import logging
import types

import aiohttp_jinja2
import jinja2
from aiohttp import BasicAuth, ClientSession, ClientTimeout
from aiohttp.client_exceptions import ClientConnectionError, ClientConnectorError, ClientResponseError
from aiohttp.web import Application
from aiohttp_utils import negotiation, routing
from structlog import wrap_logger

from . import config
from . import error_handlers
from . import flash
from . import google_analytics
from . import jwt
from . import routes
from . import security
from . import session
from . import settings
from .app_logging import logger_initial_config


logger = wrap_logger(logging.getLogger("respondent-home"))
server_logger = logging.getLogger("aiohttp.server")
server_logger.setLevel("INFO")


async def on_startup(app):
    app.http_session_pool = ClientSession(timeout=ClientTimeout(total=30))


async def on_cleanup(app):
    await app.http_session_pool.close()


async def check_services(app: Application) -> bool:
    for service_name in app.service_status_urls:
        url = app.service_status_urls[service_name]
        logger.info(f"Making health check GET request to {url}")
        try:
            async with app.http_session_pool.get(url) as resp:
                resp.raise_for_status()
        except (ClientConnectorError, ClientConnectionError, ClientResponseError):
            logger.error('Failed to connect to required service', config=service_name, url=url)
            return False
    else:
        logger.info('All required services are healthy')
        return True


def create_app(config_name=None) -> Application:
    """App factory. Sets up routes and all plugins.
    """
    app_config = config.Config()
    app_config.from_object(settings)

    # NB: raises ConfigurationError if an object attribute is None
    config_name = (config_name or app_config["ENV"])
    app_config.from_object(getattr(config, config_name))

    # Create basic auth for services
    [app_config.__setitem__(key, BasicAuth(*app_config[key])) for key in app_config if key.endswith('_AUTH')]

    app = Application(
        debug=settings.DEBUG,
        middlewares=[
            security.nonce_middleware,
            session.setup(app_config["SECRET_KEY"]),
            flash.flash_middleware,
        ],
        router=routing.ResourceRouter(),
    )

    # Handle 500 errors
    error_handlers.setup(app)

    # Store upper-cased configuration variables on app
    app.update(app_config)

    # Store a dict of health check urls for required services
    app.service_status_urls = app_config.get_service_urls_mapped_with_path(path='/info',
                                                                           excludes=['ACCOUNT_SERVICE_URL', 'EQ_URL'])

    # Monkey patch the check_services function as a method to the app object
    app.check_services = types.MethodType(check_services, app)

    # Bind logger
    logger_initial_config(service_name="respondent-home", log_level=app["LOG_LEVEL"])

    logger.info("Logging configured", log_level=app['LOG_LEVEL'])

    # Set up routes
    routes.setup(app, url_path_prefix=app['URL_PATH_PREFIX'])

    # Use content negotiation middleware to render JSON responses
    negotiation.setup(app)

    # Setup jinja2 environment
    env = aiohttp_jinja2.setup(
        app,
        loader=jinja2.PackageLoader("app", "templates"),
        context_processors=[
            flash.context_processor,
            aiohttp_jinja2.request_processor,
            google_analytics.ga_ua_id_processor],
        extensions=['jinja2.ext.i18n'],
    )
    # Required to add the default gettext and ngettext functions for rendering
    env.install_null_translations()

    # JWT KeyStore
    app["key_store"] = jwt.key_store(app["JSON_SECRET_KEYS"])

    app.on_startup.append(on_startup)
    app.on_cleanup.append(on_cleanup)
    if not app.debug:
        app.on_response_prepare.append(security.on_prepare)

    logger.info("App setup complete", config=config_name)

    return app

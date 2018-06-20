import logging

import aiohttp_jinja2
import jinja2
import pathlib
from aiohttp import web
from aiohttp_utils import negotiation

from . import config
from . import settings
from . import routes

logging.basicConfig()
logger = logging.getLogger(__name__)


def create_app() -> web.Application:
    """App factory. Sets up routes and all plugins.
    :param settings_obj: Object containing optional configuration overrides.
        May be a Python module or class with uppercased variables.
    """
    app_config = config.Config()
    app_config.from_object(settings)

    app_config.from_object(getattr(config, app_config["ENV"]))

    app = web.Application(debug=settings.DEBUG)

    # Store uppercased configuration variables on app
    app.update(app_config)

    # Set up routes
    routes.setup(app)

    # Use content negotiation middleware to render JSON responses
    negotiation.setup(app)

    # Setup jinja2 environment
    aiohttp_jinja2.setup(app, loader=jinja2.PackageLoader("app", "templates"))

    # Set static folder location
    # TODO: Only turn on in dev environment
    app['static_root_url'] = '/'
    app.router.add_static('/', 'app/static', show_index=True)

    return app


if __name__ == "__main__":
    app = create_app()
    web.run_app(app, port=app["PORT"])

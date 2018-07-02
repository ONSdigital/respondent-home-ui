from aiohttp import web

from .app import create_app


app = create_app()
web.run_app(app, port=app["PORT"])

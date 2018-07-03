import os

from aiohttp import web


if not os.getenv('APP_SETTINGS'):
    os.environ['APP_SETTINGS'] = 'DevelopmentConfig'


if __name__ == '__main__':
    from app.app import create_app
    app = create_app()
    web.run_app(app, port=app["PORT"])

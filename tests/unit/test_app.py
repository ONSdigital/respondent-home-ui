import os
from importlib import reload
from unittest import TestCase

from aiohttp.web_app import Application
from aiohttp.test_utils import AioHTTPTestCase, unittest_run_loop
from envparse import ConfigurationError, env

from app.app import create_app


class TestCreateApp(AioHTTPTestCase):

    config = 'TestingConfig'

    async def get_application(self):
        return create_app(self.config)

    @unittest_run_loop
    async def test_create_app(self):
        self.assertIsInstance(self.app, Application)


class TestCreateAppMissingConfig(TestCase):

    config = 'ProductionConfig'
    env_file = 'tests/test_data/local.env'

    def test_create_prod_app(self):
        from app import config

        config.ProductionConfig.ACCOUNT_SERVICE_URL = None

        with self.assertRaises(ConfigurationError) as ex:
            create_app(self.config)
        self.assertIn('not set', ex.exception.args[0])

        env.read_envfile(self.env_file)
        reload(config)
        self.assertIsInstance(create_app(self.config), Application)

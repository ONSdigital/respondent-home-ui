from importlib import reload
from unittest import TestCase

from aiohttp.test_utils import AioHTTPTestCase, unittest_run_loop
from aiohttp.web_app import Application
from aioresponses import aioresponses
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


class TestCheckServices(AioHTTPTestCase):

    config = 'TestingConfig'
    required_services = ('case', 'collection_exercise', 'collection_instrument', 'iac', 'sample', 'survey')

    async def get_application(self):
        return create_app(self.config)

    @unittest_run_loop
    async def test_service_status_urls(self):
        from app.config import TestingConfig

        self.assertEqual(len(self.required_services), len(self.app.service_status_urls))

        for service in self.required_services:
            config_name = f'{service}_url'.upper()
            self.assertIn(config_name, self.app.service_status_urls)
            self.assertEqual(getattr(TestingConfig, config_name) + '/info',
                             self.app.service_status_urls[config_name])

    @unittest_run_loop
    async def test_check_services(self):
        with aioresponses() as mocked:
            for service_url in self.app.service_status_urls.values():
                mocked.get(service_url)
            self.assertTrue(await self.app.check_services())

    @unittest_run_loop
    async def test_check_services_failed(self):
        with aioresponses():
            self.assertFalse(await self.app.check_services())

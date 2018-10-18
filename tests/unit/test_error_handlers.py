from aiohttp.test_utils import unittest_run_loop

from app.app import create_app
from . import RHTestCase


class TestErrorHandlers(RHTestCase):

    config = 'TestingConfig'

    async def get_application(self):
        from app import config

        url_prefix = '/url-path-prefix'
        config.TestingConfig.URL_PATH_PREFIX = url_prefix
        return create_app(self.config)

    @unittest_run_loop
    async def test_partial_path_redirects_to_index(self):
        with self.assertLogs('respondent-home', 'DEBUG') as cm:
            response = await self.client.request("GET", str(self.get_index).rstrip('/'))
        self.assertLogLine(cm, 'Redirecting to index')
        self.assertEqual(response.status, 200)
        contents = await response.content.read()
        self.assertIn(b'Your 12 character access code is on the letter we sent you', contents)
        self.assertEqual(contents.count(b'input-text'), 3)
        self.assertIn(b'type="submit"', contents)

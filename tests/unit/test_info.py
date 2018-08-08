from aiohttp.test_utils import AioHTTPTestCase, unittest_run_loop

from app.app import create_app


class TestInfo(AioHTTPTestCase):

    async def get_application(self):
        return create_app('TestingConfig')

    @unittest_run_loop
    async def test_get_info(self):
        response = await self.client.request("GET", "/info")
        json = await response.json()
        self.assertEqual(response.status, 200)
        self.assertIn('name', json)
        self.assertIn('version', json)

    @unittest_run_loop
    async def test_get_info_check(self):
        response = await self.client.request("GET", "/info?check=true")
        self.assertEqual(response.status, 200)
        self.assertIn('ready', await response.json())

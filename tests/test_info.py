from aiohttp.test_utils import AioHTTPTestCase, unittest_run_loop

from app.app import create_app


class TestInfo(AioHTTPTestCase):

    async def get_application(self):
        return create_app('TestingConfig')

    @unittest_run_loop
    async def test_get_info(self):
        response = await self.client.request("GET", "/info")
        self.assertEqual(response.status, 200)

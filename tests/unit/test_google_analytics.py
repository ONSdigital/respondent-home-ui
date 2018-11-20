from aiohttp.test_utils import make_mocked_request, unittest_run_loop

from app.google_analytics import ga_ua_id_processor
from . import RHTestCase


class TestGoogleAnalytics(RHTestCase):

    @unittest_run_loop
    async def test_google_analytics_context(self):
        self.app['ANALYTICS_UA_ID'] = '12345'
        request = make_mocked_request('GET', '/', app=self.app)
        context = await ga_ua_id_processor(request)
        self.assertEqual(context['analytics_ua_id'], '12345')

    @unittest_run_loop
    async def test_google_analytics_script_rendered(self):
        self.app['ANALYTICS_UA_ID'] = '12345'
        response = await self.client.request("GET", self.get_index)
        self.assertEqual(response.status, 200)
        self.assertIn(f"ga('create', '12345', 'auto');".encode(),
                      await response.content.read())

    @unittest_run_loop
    async def test_google_analytics_script_not_rendered(self):
        self.app['ANALYTICS_UA_ID'] = ''

        response = await self.client.request("GET", self.get_index)
        self.assertEqual(response.status, 200)
        self.assertNotIn(f"ga('create', '', 'auto');".encode(),
                         await response.content.read())

import logging

import requests
from aiohttp.test_utils import AioHTTPTestCase, unittest_run_loop
from aioresponses import aioresponses
from envparse import Env
from structlog import wrap_logger

from app.app import create_app
from app.case import get_case
from tests import get_single_hac_and_case_id_by_collex_id, get_collex_id


env = Env()
logger = wrap_logger(logging.getLogger(__name__))


class TestRespondentHome(AioHTTPTestCase):

    """
    Assumes services are running on the default ports with social data pre-loaded with `make setup`.
    """
    async def get_application(self):
        return create_app(env.str('APP_SETTINGS', default='DevelopmentConfig'))

    @unittest_run_loop
    async def test_can_access_respondent_home_homepage(self):
        proxy_row = get_single_hac_and_case_id_by_collex_id(get_collex_id())

        hac, case_id = proxy_row['iac'], proxy_row['id']
        hac1, hac2, hac3 = hac[:4], hac[4:8], hac[8:]
        form_data = {
            'iac1': hac1, 'iac2': hac2, 'iac3': hac3, 'action[save_continue]': '',
        }
        # fetch case ahead of time to use in mock
        case = await get_case(case_id, self.app)
        old_case_state = case['caseGroup']['caseGroupStatus']

        service_urls = [
            self.app[url]
            for url in self.app
            if url.isupper()
            and not url.startswith('CASE')  # skip on case service so we can mock the POSTing of a case event
            and url.endswith('URL')
        ]
        # allow all other service requests to keep integration test as close to normal as possible
        with aioresponses(passthrough=([str(self.server._root)] + service_urls)) as mocked:
            # mocking this prevents the transition from `NOTSTARTED` to `INPROGRESS`
            mocked.post(f"{self.app['CASE_URL']}/cases/{case_id}/events")
            mocked.get(f"{self.app['CASE_URL']}/cases/{case['id']}", payload=case)
            response = await self.client.request("POST", "/", allow_redirects=False, data=form_data)

        self.assertEqual(response.status, 302)  # Response should be a redirect to eQ
        location = response.headers['location']
        self.assertIn(self.app['EQ_URL'], location)  # Check that the redirect location is to eQ
        response = requests.get(location)  # Follow the redirect location to check contents
        self.assertIn(b'What is your name', response.content)
        self.assertIn(b'Online Household Study', response.content)
        case_response = await get_case(case_id, self.app)
        case_state = case_response['caseGroup']['caseGroupStatus']
        self.assertEqual(case_state, old_case_state)  # Ensure the case status has not transitioned

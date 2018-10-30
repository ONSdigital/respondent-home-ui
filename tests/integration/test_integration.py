import logging

import requests
from aiohttp.test_utils import AioHTTPTestCase, unittest_run_loop
from aioresponses import aioresponses
from envparse import Env
from structlog import wrap_logger

from app.app import create_app
from app.case import get_case
from tests.controllers import (get_case, get_sample_summary_id_from_kwargs, get_first_sample_summary_id,
                               get_first_sample_unit_id_by_summary, poll_for_actionable_case, poll_case_for_iacs)


env = Env()
logger = wrap_logger(logging.getLogger(__name__))


class TestRespondentHome(AioHTTPTestCase):

    """
    Assumes services are running on the default ports with social data pre-loaded with `make setup`.
    """
    async def get_application(self):
        self.live_test = env.bool('LIVE_TEST', default=False)
        # Social Test 1 can be identified with 500 sample units
        self.sample_size = env.int('SAMPLE_SIZE', default=500)
        return create_app('BaseConfig' if self.live_test else 'TestingConfig')

    @unittest_run_loop
    async def test_can_access_respondent_home_homepage(self):
        if self.live_test:
            sample_summary_id = get_sample_summary_id_from_kwargs(totalSampleUnits=self.sample_size)
        else:
            # Any old summary should do against test data
            sample_summary_id = get_first_sample_summary_id()
        if sample_summary_id is None:
            self.fail('No sample summary found')

        sample_unit_id = get_first_sample_unit_id_by_summary(sample_summary_id)
        if sample_unit_id is None:
            self.fail('No sample unit id found')

        case = poll_for_actionable_case(sample_unit_id)
        if case is None:
            self.fail('No ACTIONABLE case found')

        iacs = poll_case_for_iacs(case)
        if iacs is None:
            self.fail('No IACs for case found')

        iac = iacs[0]['iac']
        iac1, iac2, iac3 = iac[:4], iac[4:8], iac[8:]
        form_data = {
            'iac1': iac1, 'iac2': iac2, 'iac3': iac3, 'action[save_continue]': '',
        }

        service_urls = [
            self.app[url]
            for url in self.app
            if url.isupper()
            and not url.startswith('CASE')  # skip on case service so we can mock the POSTing of a case event
            and url.endswith('URL')
        ]
        # allow all other service requests to keep integration test as close to normal as possible
        with aioresponses(passthrough=([str(self.server._root)] + service_urls)) as mocked:
            # we can mock the getting of a case as the same request was already performed above
            mocked.get(f"{self.app['CASE_URL']}/cases/{case['id']}", payload=case)
            # mocking this prevents the transition from `NOTSTARTED` to `INPROGRESS`
            mocked.post(f"{self.app['CASE_URL']}/cases/{case['id']}/events")
            response = await self.client.request("POST", "/", allow_redirects=False, data=form_data)

        self.assertEqual(response.status, 302)  # Response should be a redirect to eQ
        location = response.headers['location']
        self.assertIn(self.app['EQ_URL'], location)  # Check that the redirect location is to eQ
        response = requests.get(location)  # Follow the redirect location to check contents
        self.assertIn(b'What is your name', response.content)
        self.assertIn(b'Online Household Study', response.content)
        case_response = get_case(case['id'])
        case_state = case_response['caseGroup']['caseGroupStatus']
        self.assertEqual(case_state, 'NOTSTARTED')  # Ensure the case status has not transitioned

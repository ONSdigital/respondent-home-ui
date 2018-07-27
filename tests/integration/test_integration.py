import logging
import time

import requests
from aiohttp.test_utils import AioHTTPTestCase, unittest_run_loop
from envparse import Env
from structlog import wrap_logger

from app.app import create_app
from app.case import get_case


env = Env()
logger = wrap_logger(logging.getLogger(__name__))


class TestRespondentHome(AioHTTPTestCase):

    """
    Assumes services are running on the default ports with social data pre-loaded with `make setup`.
    """
    async def get_application(self):
        self.live_test = env.bool('LIVE_TEST', default=False)
        self.sample_size = env.int('SAMPLE_SIZE', default=500)
        return create_app('BaseConfig' if self.live_test else 'TestingConfig')

    def get_sample_summary_id_from_count(self, unit_count=500):
        logger.debug('Retrieving sample summaries')
        url = f'{self.app["SAMPLE_URL"]}/samples/samplesummaries'
        response = requests.get(url, auth=self.app["SAMPLE_AUTH"][:2])
        response.raise_for_status()
        logger.debug('Successfully retrieved sample summaries')
        for sample_summary in response.json():
            if sample_summary['totalSampleUnits'] == unit_count:
                return sample_summary['id']

    def get_first_sample_summary_id(self):
        logger.debug('Retrieving sample summaries')
        url = f'{self.app["SAMPLE_URL"]}/samples/samplesummaries'
        response = requests.get(url, auth=self.app["SAMPLE_AUTH"][:2])
        response.raise_for_status()
        logger.debug('Successfully retrieved sample summaries')
        return response.json()[0]['id']

    def get_first_sample_unit_id_by_summary(self, sample_summary_id):
        logger.debug('Retrieving sample unit id', sample_summary_id=sample_summary_id)
        url = f'{self.app["SAMPLE_URL"]}/samples/{sample_summary_id}/sampleunits'
        response = requests.get(url, auth=self.app["SAMPLE_AUTH"][:2])
        response.raise_for_status()
        logger.debug('Successfully retrieved sample units', sample_summary_id=sample_summary_id)
        return response.json()[0]['id']

    def get_actionable_case_by_sample_unit_id(self, sample_unit_id):
        logger.debug('Retrieving case by id', sample_unit_id=sample_unit_id)
        url = f'{self.app["CASE_URL"]}/cases?sampleUnitId={sample_unit_id}&iac=true'
        response = requests.get(url, auth=self.app["CASE_AUTH"][:2])
        response.raise_for_status()
        logger.debug('Successfully retrieved case', sample_unit_id=sample_unit_id)
        for case in response.json():
            if case['state'] == 'ACTIONABLE':
                return case

    def get_address_by_sample_unit_id(self, sample_unit_id):
        logger.debug('Retrieving sample unit', sample_unit_id=sample_unit_id)
        url = f'{self.app["SAMPLE_URL"]}/samples/{sample_unit_id}'
        response = requests.get(url, auth=self.app["SAMPLE_AUTH"][:2])
        response.raise_for_status()
        logger.debug('Successfully retrieved sample unit', sample_unit_id=sample_unit_id)
        return response.json()['sampleAttributes']['attributes']['Prem1']

    def poll_case_for_iac(self, case, retries=20):
        for _ in range(retries):
            iac = case['iac']
            if iac is not None:
                return iac
            time.sleep(3)
            case = get_case(case['id'], self.app)

    def poll_for_actionable_case(self, sample_unit_id, retries=20):
        for _ in range(retries):
            case = self.get_actionable_case_by_sample_unit_id(sample_unit_id)
            if case is not None:
                return case
            time.sleep(3)

    @unittest_run_loop
    async def test_can_access_respondent_home_homepage(self):
        if self.live_test:
            # Social Test 1 can be identified with 500 sample units
            sample_summary_id = self.get_sample_summary_id_from_count(self.sample_size)
        else:
            # Any old summary should do against test data
            sample_summary_id = self.get_first_sample_summary_id()
        if sample_summary_id is None:
            self.fail('No sample summary found')

        sample_unit_id = self.get_first_sample_unit_id_by_summary(sample_summary_id)
        if sample_unit_id is None:
            self.fail('No sample unit id found')

        case = self.poll_for_actionable_case(sample_unit_id)
        if case is None:
            self.fail('No ACTIONABLE case found')

        iac = self.poll_case_for_iac(case)
        if iac is None:
            self.fail('No IAC for case found')
        iac1, iac2, iac3 = iac[:4], iac[4:8], iac[8:]
        form_data = {
            'iac1': iac1, 'iac2': iac2, 'iac3': iac3, 'action[save_continue]': '',
        }
        response = await self.client.request("POST", "/", allow_redirects=False, data=form_data)

        self.assertEqual(response.status, 302)
        location = response.headers['location']
        self.assertIn(self.app['EQ_URL'], location)  # Check that the redirect location is correct
        response = requests.get(location)  # Follow the redirect location to check contents
        self.assertIn(self.get_address_by_sample_unit_id(sample_unit_id).encode(), response.content)

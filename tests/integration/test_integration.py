import logging

import requests
from aiohttp.test_utils import AioHTTPTestCase, unittest_run_loop
from structlog import wrap_logger

from app.app import create_app
from tests.config import Config


logger = wrap_logger(logging.getLogger(__name__))


class TestRespondentHome(AioHTTPTestCase):

    """
    Assumes services are running on the default ports with social data pre-loaded with `make setup`.
    """

    async def get_application(self):
        return create_app('TestingConfig')

    @staticmethod
    def get_first_sample_summary_id():
        logger.debug('Retrieving sample summaries')
        url = f'{Config.SAMPLE_SERVICE}/samples/samplesummaries'
        response = requests.get(url, auth=Config.BASIC_AUTH)
        response.raise_for_status()
        logger.debug('Successfully retrieved sample summaries')
        return response.json()[0]['id']

    @staticmethod
    def get_first_sample_unit_id_by_summary(sample_summary_id):
        logger.debug('Retrieving sample unit id', sample_summary_id=sample_summary_id)
        url = f'{Config.SAMPLE_SERVICE}/samples/{sample_summary_id}/sampleunits'
        response = requests.get(url, auth=Config.BASIC_AUTH)
        response.raise_for_status()
        logger.debug('Successfully retrieved sample units', sample_summary_id=sample_summary_id)
        return response.json()[0]['id']

    @staticmethod
    def get_iac_by_sample_unit_id(sample_unit_id):
        logger.debug('Retrieving case by id', sample_unit_id=sample_unit_id)
        url = f'{Config.CASE_SERVICE}/cases?sampleUnitId={sample_unit_id}&iac=true'
        response = requests.get(url, auth=Config.BASIC_AUTH)
        response.raise_for_status()
        logger.debug('Successfully retrieved case', sample_unit_id=sample_unit_id)
        return response.json()[0]['iac']

    @staticmethod
    def get_address_by_sample_unit_id(sample_unit_id):
        logger.debug('Retrieving sample unit', sample_unit_id=sample_unit_id)
        url = f'{Config.SAMPLE_SERVICE}/samples/{sample_unit_id}'
        response = requests.get(url, auth=Config.BASIC_AUTH)
        response.raise_for_status()
        logger.debug('Successfully retrieved sample unit', sample_unit_id=sample_unit_id)
        return response.json()['sampleAttributes']['attributes']['Prem1']

    @unittest_run_loop
    async def test_can_access_respondent_home_homepage(self):
        sample_summary_id = self.get_first_sample_summary_id()
        sample_unit_id = self.get_first_sample_unit_id_by_summary(sample_summary_id)
        iac = self.get_iac_by_sample_unit_id(sample_unit_id)
        iac1, iac2, iac3 = iac[:4], iac[4:8], iac[8:]
        form_data = {
            'iac1': iac1, 'iac2': iac2, 'iac3': iac3, 'action[save_continue]': '',
        }
        response = await self.client.request("POST", "/", data=form_data)

        self.assertEqual(response.status, 200)
        self.assertIn(Config.EQ_SURVEY_RUNNER_URL, str(response.url))
        self.assertIn(self.get_address_by_sample_unit_id(sample_unit_id).encode(), await response.content.read())

import logging
import unittest

import requests
from structlog import wrap_logger

from tests.config import Config


logger = wrap_logger(logging.getLogger(__name__))


class TestRespondentHome(unittest.TestCase):

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
        return response.json()['iac']

    @staticmethod
    def get_address_by_sample_unit_id(sample_unit_id):
        logger.debug('Retrieving sample unit', sample_unit_id=sample_unit_id)
        url = f'{Config.SAMPLE_SERVICE}/samples/{sample_unit_id}'
        response = requests.get(url, auth=Config.BASIC_AUTH)
        response.raise_for_status()
        logger.debug('Successfully retrieved sample unit', sample_unit_id=sample_unit_id)
        return response.json()['sampleAttributes']['attributes']['Prem1']

    @staticmethod
    def post_to_rh(iac_code):
        logger.debug('Posting iac to respondent home', iac=iac_code)
        iac1, iac2, iac3 = iac_code[:4], iac_code[4:8], iac_code[8:]
        form_data = {
            'iac1': iac1, 'iac2': iac2, 'iac3': iac3, 'action[save_continue]': '',
        }
        url = f'{Config.RESPONDENT_HOME_SERVICE}/'
        response = requests.post(url, data=form_data)
        response.raise_for_status()
        logger.debug('Posted iac to respondent home')
        return response

    def test_can_access_respondent_home_homepage(self):
        sample_summary_id = self.get_first_sample_summary_id()
        sample_unit_id = self.get_first_sample_unit_id_by_summary(sample_summary_id)
        iac = self.get_iac_by_sample_unit_id(sample_unit_id)
        response = self.post_to_rh(iac)

        assert response.status == 200
        assert Config.EQ_SURVEY_RUNNER_URL in response.url
        assert self.get_address_by_sample_unit_id(sample_unit_id) in response.content

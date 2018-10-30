import logging
import time

import requests
from structlog import wrap_logger


from tests.config import Config

logger = wrap_logger(logging.getLogger(__name__))


def get_case(case_id):
    logger.debug('Retrieving case', case_id=case_id)
    url = f"{Config.CASE_SERVICE}/cases/{case_id}"
    response = requests.get(url, auth=Config.BASIC_AUTH)
    response.raise_for_status()
    logger.debug('Successfully retrieved case', case_id=case_id)
    return response.json()


def get_sample_summary_id_from_kwargs(**kwargs):
    logger.debug('Retrieving sample summaries')
    url = f'{Config.SAMPLE_SERVICE}/samples/samplesummaries'
    response = requests.get(url, auth=Config.BASIC_AUTH)
    response.raise_for_status()
    logger.debug('Successfully retrieved sample summaries')
    for sample_summary in response.json():
        if all(sample_summary[key] == val for key, val in kwargs.items()):
            return sample_summary['id']


def get_first_sample_summary_id():
    logger.debug('Retrieving sample summaries')
    url = f'{Config.SAMPLE_SERVICE}/samples/samplesummaries'
    response = requests.get(url, auth=Config.BASIC_AUTH)
    response.raise_for_status()
    logger.debug('Successfully retrieved sample summaries')
    return response.json()[0]['id']


def get_first_sample_unit_id_by_summary(sample_summary_id):
    logger.debug('Retrieving sample unit id', sample_summary_id=sample_summary_id)
    url = f'{Config.SAMPLE_SERVICE}/samples/{sample_summary_id}/sampleunits'
    response = requests.get(url, auth=Config.BASIC_AUTH)
    response.raise_for_status()
    logger.debug('Successfully retrieved sample units', sample_summary_id=sample_summary_id)
    return response.json()[0]['id']


def get_actionable_case_by_sample_unit_id(sample_unit_id):
    logger.debug('Retrieving case by id', sample_unit_id=sample_unit_id)
    url = f'{Config.CASE_SERVICE}/cases?sampleUnitId={sample_unit_id}&iac=true'
    response = requests.get(url, auth=Config.BASIC_AUTH)
    response.raise_for_status()
    logger.debug('Successfully retrieved case', sample_unit_id=sample_unit_id)
    for case in response.json():
        if case['state'] == 'ACTIONABLE':
            return case


def get_address_by_sample_unit_id(sample_unit_id):
    logger.debug('Retrieving sample unit', sample_unit_id=sample_unit_id)
    url = f'{Config.SAMPLE_SERVICE}/samples/{sample_unit_id}'
    response = requests.get(url, auth=Config.BASIC_AUTH)
    response.raise_for_status()
    logger.debug('Successfully retrieved sample unit', sample_unit_id=sample_unit_id)
    return response.json()['sampleAttributes']['attributes']['ADDRESS_LINE1']


def get_iacs_by_case_id(case_id):
    logger.debug('Retrieving IACs', case_id=case_id)
    url = f"{Config.CASE_SERVICE}/cases/{case_id}/iac"
    response = requests.get(url, auth=Config.BASIC_AUTH)
    response.raise_for_status()
    logger.debug('Successfully retrieved IACs for case', case_id=case_id)
    return response.json()


def poll_case_for_iacs(case_id, retries=20):
    for _ in range(retries):
        iacs = get_iacs_by_case_id(case_id)
        if iacs is not None:
            return iacs
        time.sleep(3)


def poll_for_actionable_case(sample_unit_id, retries=20):
    for _ in range(retries):
        case = get_actionable_case_by_sample_unit_id(sample_unit_id)
        if case is not None:
            return case
        time.sleep(3)

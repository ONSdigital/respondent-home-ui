import logging

import requests
from structlog import wrap_logger

from config import Config


logger = wrap_logger(logging.getLogger(__name__))


def get_iac_by_case_id(case_id):
    logger.debug('Retrieving case by id', case_id=case_id)
    url = f'{Config.CASE_SERVICE}/cases/{case_id}?iac=true'
    response = requests.get(url, auth=Config.BASIC_AUTH)
    response.raise_for_status()
    logger.debug('Successfully retrieved case', case_id=case_id)
    return response.json()['iac']


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


if __name__ == '__main__':
    iac = get_iac_by_case_id('30143c6b-b0f6-4fe7-8f23-d1f454ae06c0')
    post_to_rh(iac)

import os
import unittest

import requests


class TestRespondentHome(unittest.TestCase):

    def test_can_access_respondent_home_homepage(self):
        # Given
        respondent_home_url = os.getenv('RESPONDENT_HOME_URL')
        if not respondent_home_url:
            self.fail('RESPONDENT_HOME_URL not set')

        url_prefix = os.getenv('URL_PATH_PREFIX', '')

        url = f'{respondent_home_url}{url_prefix}'

        # When
        resp = requests.get(url, verify=False)

        # Then
        self.assertEqual(resp.status_code, 200, url)

    def test_can_access_required_services(self):
        # Given
        url = os.getenv('RESPONDENT_HOME_INTERNAL_URL')
        if not url:
            self.fail('RESPONDENT_HOME_INTERNAL_URL not set')

        # When
        resp = requests.get(f'{url}/info?check=true', verify=False).json()

        # Then
        self.assertEqual(resp['ready'], True, resp)
        self.assertEqual(resp['name'], "respondent-home-ui", resp)

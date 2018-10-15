import os
import unittest

import requests


class TestRespondentHome(unittest.TestCase):

    def test_can_access_respondent_home_homepage(self):
        # Given
        url = os.getenv('RESPONDENT_HOME_URL')
        if not url:
            self.fail('RESPONDENT_HOME_URL not set')

        # When
        resp = requests.get(url, verify=False)

        # Then
        message = f'URL: {url}, status_code: {resp.status_code}'
        self.assertEqual(resp.status_code, 200, message)

    def test_can_access_required_services(self):
        # Given
        url = os.getenv('RESPONDENT_HOME_URL')
        if not url:
            self.fail('RESPONDENT_HOME_URL not set')

        # When
        resp = requests.get(f'{url}/info?check=true', verify=False).json()

        # Then
        self.assertEqual(resp['ready'], True, resp)
        self.assertEqual(resp['name'], "respondent-home-ui", resp)

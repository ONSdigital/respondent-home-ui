import os
import unittest

import requests


class TestRespondentHome(unittest.TestCase):

    def test_can_access_respondent_home_homepage(self):
        # Given
        url = os.getenv('ACCOUNT_SERVICE_URL')
        if not url:
            self.fail('ACCOUNT_SERVICE_URL not set')

        # When
        resp = requests.get(url, verify=False)

        # Then
        self.assertEqual(resp.status_code, 200, resp.status_code)
        self.assertIn('Welcome to the Online Household Study', resp.text)

    def test_can_access_required_services(self):
        # Given
        url = os.getenv('ACCOUNT_SERVICE_URL')
        if not url:
            self.fail('ACCOUNT_SERVICE_URL not set')

        # When
        resp = requests.get(f'{url}/info?check=true', verify=False).json()

        # Then
        self.assertEqual(resp['ready'], True, resp)

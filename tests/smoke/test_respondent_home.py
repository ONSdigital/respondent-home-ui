import os
import unittest

import requests


class TestRespondentHome(unittest.TestCase):

    def test_can_access_respondent_home_homepage(self):
        # Given
        url = os.getenv('RESPONDENT_HOME_URL')

        # When
        resp = requests.get(url, verify=False)

        # Then
        assert resp.status_code == 200, resp.status_code
        assert 'Welcome to the Online Household Study' in resp.text

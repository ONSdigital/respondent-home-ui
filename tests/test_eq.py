import unittest

from aiohttp.test_utils import AioHTTPTestCase, unittest_run_loop
from aioresponses import aioresponses

from app.app import create_app
from app.eq import format_date
from app.handlers import get_iac
from app.exceptions import InvalidEqPayLoad


class TestGenerateEqURL(AioHTTPTestCase):

    async def get_application(self):
        return create_app('TestingConfig')

    @unittest_run_loop
    async def test_get_index(self):
        response = await self.client.request("GET", "/")
        self.assertEqual(response.status, 200)

    @unittest.skip('TODO')
    @unittest_run_loop
    @aioresponses(passthrough = ['http://127.0.0.1'])
    async def test_post_index(self, mocked):
        mocked.get(f"{self.app['IAC_URL']}/iacs/123456789012", payload={'active': '1', 'caseId': 'test'})
        mocked.get(f"{self.app['CASE_URL']}/cases/test")
        response = await self.client.request("POST", "/", data={'iac1': '1234', 'iac2': '5678', 'iac3': '9012', 'action[save_continue]': ''})
        self.assertEqual(response.status, 200)

    @unittest_run_loop
    async def test_get_info(self):
        response = await self.client.request("GET", "/info")
        self.assertEqual(response.status, 200)

    def test_get_iac(self):
        # Given some post data
        post_data = {'iac1': '1234', 'iac2': '5678', 'iac3': '9012', 'action[save_continue]': ''}

        # When get_iac is called
        result = get_iac(post_data)

        # Then a single string built from the iac values is returned
        self.assertEqual(result, post_data['iac1'] + post_data['iac2'] + post_data['iac3'])

    def test_get_iac_missing(self):
        # Given some missing post data
        post_data = {'action[save_continue]': ''}

        # When get_iac is called
        with self.assertRaises(TypeError):
            get_iac(post_data)
        # Then a TypeError is raised

    def test_get_iac_some_missing(self):
        # Given some missing post data
        post_data = {'iac1': '1234', 'iac2': '5678', 'iac3': '', 'action[save_continue]': ''}

        # When get_iac is called
        with self.assertRaises(TypeError):
            get_iac(post_data)
        # Then a TypeError is raised

    def test_handle_response_raises_client_error_exception(self):
        pass

    def test_correct_iso8601_date_format(self):
        # Given a valid date
        date = '2007-01-25T12:00:00Z'

        # When format_date is called
        result = format_date(date)

        # Then the date is formatted correctly
        self.assertEqual(result, '2007-01-25')

    def test_incorrect_date_format(self):
        # Given an invalid date
        date = 'invalid_date'

        # When format_date is called
        with self.assertRaises(InvalidEqPayLoad) as e:
            format_date(date)

        # Then an InvalidEqPayLoad is raised
        self.assertEqual(e.exception.message, 'Unable to format invalid_date')

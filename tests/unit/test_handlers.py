import json
from unittest import mock
from urllib.parse import urlsplit, parse_qs

from aiohttp.client_exceptions import ClientConnectionError, ClientConnectorError
from aiohttp.test_utils import unittest_run_loop
from aioresponses import aioresponses

from app import (
    BAD_CODE_MSG, BAD_RESPONSE_MSG, CODE_USED_MSG, INVALID_CODE_MSG, NOT_AUTHORIZED_MSG,
    CONNECTION_ERROR_MSG, REDIRECT_FAILED_MSG, SERVER_ERROR_MSG)
from app.exceptions import InactiveCaseError
from app.handlers import join_iac, validate_case

from . import RHTestCase, build_eq_raises, skip_build_eq, skip_encrypt


class TestHandlers(RHTestCase):

    @unittest_run_loop
    async def test_get_index(self):
        response = await self.client.request("GET", "/")
        self.assertEqual(response.status, 200)
        contents = await response.content.read()
        self.assertIn(b'Enter your unique access code below', contents)
        self.assertEqual(contents.count(b'input-text'), 3)
        self.assertIn(b'type="submit"', contents)

    @skip_build_eq
    @unittest_run_loop
    async def test_post_index(self):
        with aioresponses(passthrough=[str(self.server._root)]) as mocked:
            mocked.get(self.iac_url, payload=self.iac_json)
            mocked.get(self.case_url, payload=self.case_json)
            mocked.post(self.case_events_url)

            with self.assertLogs('respondent-home', 'INFO') as cm:
                response = await self.client.request("POST", "/", allow_redirects=False, data=self.form_data)
            self.assertLogLine(cm, 'Redirecting to eQ')

        self.assertEqual(response.status, 302)
        self.assertIn(self.app['EQ_URL'], response.headers['location'])

    @unittest_run_loop
    async def test_post_index_connector_error(self):
        with aioresponses(passthrough=[str(self.server._root)]) as mocked:
            mocked.get(self.iac_url, exception=ClientConnectorError(mock.MagicMock(), mock.MagicMock()))

            with self.assertLogs('respondent-home', 'ERROR') as cm:
                response = await self.client.request("POST", "/", allow_redirects=False, data=self.form_data)
            self.assertLogLine(cm, "Service connection error")

        self.assertEqual(response.status, 200)
        self.assertIn(CONNECTION_ERROR_MSG.encode(), await response.content.read())

    @unittest_run_loop
    async def test_post_index_no_iac_json(self):
        with aioresponses(passthrough=[str(self.server._root)]) as mocked:
            mocked.get(self.iac_url, content_type='text')

            with self.assertLogs('respondent-home', 'ERROR') as cm:
                response = await self.client.request("POST", "/", allow_redirects=False, data=self.form_data)
            self.assertLogLine(cm, "Service failed to return expected JSON payload")

        self.assertEqual(response.status, 200)
        self.assertIn(SERVER_ERROR_MSG.encode(), await response.content.read())

    @unittest_run_loop
    async def test_post_index_case_403(self):
        with aioresponses(passthrough=[str(self.server._root)]) as mocked:
            mocked.get(self.iac_url, payload=self.iac_json)
            mocked.get(self.case_url, status=403)

            with self.assertLogs('app.case', 'ERROR') as cm:
                response = await self.client.request("POST", "/", allow_redirects=False, data=self.form_data)
            self.assertLogLine(cm, "Error retrieving case", case_id=self.case_id, status_code=403)

        self.assertEqual(response.status, 200)
        self.assertIn(f'403 {SERVER_ERROR_MSG}'.encode(), await response.content.read())

    @unittest_run_loop
    async def test_post_index_case_500(self):
        with aioresponses(passthrough=[str(self.server._root)]) as mocked:
            mocked.get(self.iac_url, payload=self.iac_json)
            mocked.get(self.case_url, status=500)

            with self.assertLogs('app.case', 'ERROR') as cm:
                response = await self.client.request("POST", "/", data=self.form_data)
            self.assertLogLine(cm, "Error retrieving case", case_id=self.case_id, status_code=500)

        self.assertEqual(response.status, 200)
        self.assertIn(f'500 {SERVER_ERROR_MSG}'.encode(), await response.content.read())

    @unittest_run_loop
    async def test_post_index_case_connector_error(self):
        with aioresponses(passthrough=[str(self.server._root)]) as mocked:
            mocked.get(self.iac_url, payload=self.iac_json)
            mocked.get(self.case_url, exception=ClientConnectorError(mock.MagicMock(), mock.MagicMock()))

            with self.assertLogs('respondent-home', 'ERROR') as cm:
                response = await self.client.request("POST", "/", data=self.form_data)
            self.assertLogLine(cm, "Service connection error")

        self.assertEqual(response.status, 200)
        self.assertIn(CONNECTION_ERROR_MSG.encode(), await response.content.read())

    @unittest_run_loop
    async def test_post_index_with_build_connection_error(self):
        with aioresponses(passthrough=[str(self.server._root)]) as mocked:
            mocked.get(self.iac_url, payload=self.iac_json)
            mocked.get(self.case_url, payload=self.case_json)
            mocked.get(self.collection_instrument_url, exception=ClientConnectionError('Failed'))

            with self.assertLogs('respondent-home', 'ERROR') as cm:
                response = await self.client.request("POST", "/", allow_redirects=False, data=self.form_data)
            self.assertLogLine(cm, "Service connection error", message='Failed')

        self.assertEqual(response.status, 200)
        self.assertIn(CONNECTION_ERROR_MSG.encode(), await response.content.read())

    @skip_encrypt
    @unittest_run_loop
    async def test_post_index_with_build(self):
        with aioresponses(passthrough=[str(self.server._root)]) as mocked:
            # mocks for initial data setup in post
            mocked.get(self.iac_url, payload=self.iac_json)
            mocked.get(self.case_url, payload=self.case_json)
            mocked.post(self.case_events_url)
            # mocks for the payload builder
            mocked.get(self.collection_instrument_url, payload=self.collection_instrument_json)
            mocked.get(self.collection_exercise_url, payload=self.collection_exercise_json)
            mocked.get(self.collection_exercise_events_url, payload=self.collection_exercise_events_json)
            mocked.get(self.sample_attributes_url, payload=self.sample_attributes_json)
            mocked.get(self.survey_url, payload=self.survey_json)

            with self.assertLogs('respondent-home', 'INFO') as logs_home, self.assertLogs('app.eq', 'INFO') as logs_eq:
                response = await self.client.request("POST", "/", allow_redirects=False, data=self.form_data)
            self.assertLogLine(logs_home, 'Redirecting to eQ')

        self.assertEqual(response.status, 302)
        redirected_url = response.headers['location']
        self.assertTrue(redirected_url.startswith(self.app['EQ_URL']), redirected_url)  # outputs url on fail
        _, _, _, query, *_ = urlsplit(redirected_url)  # we only care about the query string
        token = json.loads(parse_qs(query)['token'][0])  # convert token to dict
        self.assertLogLine(logs_eq, '', payload=token)  # make sure the payload is logged somewhere
        self.assertEqual(self.eq_payload.keys(), token.keys())  # fail early if payload keys differ
        for key in self.eq_payload.keys():
            if key in ['jti', 'tx_id', 'iat', 'exp']:
                continue  # skip uuid / time generated values
            self.assertEqual(self.eq_payload[key], token[key], key)  # outputs failed key as msg

    @build_eq_raises
    @unittest_run_loop
    async def test_post_index_build_raises_InvalidEqPayLoad(self):
        with aioresponses(passthrough=[str(self.server._root)]) as mocked:
            # mocks for initial data setup in post
            mocked.get(self.iac_url, payload=self.iac_json)
            mocked.get(self.case_url, payload=self.case_json)
            mocked.post(self.case_events_url)

            with self.assertLogs('respondent-home', 'ERROR') as cm:
                # decorator makes URL constructor raise InvalidEqPayLoad when build() is called in handler
                response = await self.client.request("POST", "/", allow_redirects=False, data=self.form_data)
            self.assertLogLine(cm, "Service failed to build eQ payload")

        # then error handler catches exception and flashes message to index
        self.assertEqual(response.status, 200)
        self.assertIn(REDIRECT_FAILED_MSG.encode(), await response.content.read())

    @unittest_run_loop
    async def test_post_index_with_build_ci_500(self):
        with aioresponses(passthrough=[str(self.server._root)]) as mocked:
            # mocks for initial data setup in post
            mocked.get(self.iac_url, payload=self.iac_json)
            mocked.get(self.case_url, payload=self.case_json)
            mocked.post(self.case_events_url)
            # mocks for the payload builder
            mocked.get(self.collection_instrument_url, status=500)

            with self.assertLogs('app.eq', 'ERROR') as cm:
                response = await self.client.request("POST", "/", allow_redirects=False, data=self.form_data)
            self.assertLogLine(cm, "Error in response", status_code=500)

        self.assertEqual(response.status, 200)
        self.assertIn(f'500 {SERVER_ERROR_MSG}'.encode(), await response.content.read())

    @unittest_run_loop
    async def test_post_index_with_build_ci_400(self):
        with aioresponses(passthrough=[str(self.server._root)]) as mocked:
            # mocks for initial data setup in post
            mocked.get(self.iac_url, payload=self.iac_json)
            mocked.get(self.case_url, payload=self.case_json)
            mocked.post(self.case_events_url)
            # mocks for the payload builder
            mocked.get(self.collection_instrument_url, status=400)

            with self.assertLogs('app.eq', 'ERROR') as cm:
                response = await self.client.request("POST", "/", allow_redirects=False, data=self.form_data)
            self.assertLogLine(cm, "Error in response", status_code=400)

        self.assertEqual(response.status, 200)
        self.assertIn(f'400 {SERVER_ERROR_MSG}'.encode(), await response.content.read())

    @unittest_run_loop
    async def test_post_index_with_build_ce_503(self):
        with aioresponses(passthrough=[str(self.server._root)]) as mocked:
            # mocks for initial data setup in post
            mocked.get(self.iac_url, payload=self.iac_json)
            mocked.get(self.case_url, payload=self.case_json)
            mocked.post(self.case_events_url)
            # mocks for the payload builder
            mocked.get(self.collection_instrument_url, payload=self.collection_instrument_json)
            mocked.get(self.collection_exercise_url, status=503)

            with self.assertLogs('app.eq', 'ERROR') as cm:
                response = await self.client.request("POST", "/", allow_redirects=False, data=self.form_data)
            self.assertLogLine(cm, "Error in response", status_code=503)

        self.assertEqual(response.status, 200)
        self.assertIn(f'503 {SERVER_ERROR_MSG}'.encode(), await response.content.read())

    @unittest_run_loop
    async def test_post_index_with_build_events_404(self):
        with aioresponses(passthrough=[str(self.server._root)]) as mocked:
            # mocks for initial data setup in post
            mocked.get(self.iac_url, payload=self.iac_json)
            mocked.get(self.case_url, payload=self.case_json)
            mocked.post(self.case_events_url)
            # mocks for the payload builder
            mocked.get(self.collection_instrument_url, payload=self.collection_instrument_json)
            mocked.get(self.collection_exercise_url, payload=self.collection_exercise_json)
            mocked.get(self.collection_exercise_events_url, status=404)

            with self.assertLogs('app.eq', 'ERROR') as cm:
                response = await self.client.request("POST", "/", allow_redirects=False, data=self.form_data)
            self.assertLogLine(cm, "Error in response", status_code=404)

        self.assertEqual(response.status, 200)
        self.assertIn(f'404 {SERVER_ERROR_MSG}'.encode(), await response.content.read())

    @unittest_run_loop
    async def test_post_index_with_build_sample_403(self):
        with aioresponses(passthrough=[str(self.server._root)]) as mocked:
            # mocks for initial data setup in post
            mocked.get(self.iac_url, payload=self.iac_json)
            mocked.get(self.case_url, payload=self.case_json)
            mocked.post(self.case_events_url)
            # mocks for the payload builder
            mocked.get(self.collection_instrument_url, payload=self.collection_instrument_json)
            mocked.get(self.collection_exercise_url, payload=self.collection_exercise_json)
            mocked.get(self.collection_exercise_events_url, payload=self.collection_exercise_events_json)
            mocked.get(self.sample_attributes_url, status=403)

            with self.assertLogs('app.eq', 'ERROR') as cm:
                response = await self.client.request("POST", "/", allow_redirects=False, data=self.form_data)
            self.assertLogLine(cm, "Error in response", status_code=403)

        self.assertEqual(response.status, 200)
        self.assertIn(f'403 {SERVER_ERROR_MSG}'.encode(), await response.content.read())

    @unittest_run_loop
    async def test_post_index_with_build_case_event_500(self):
        with aioresponses(passthrough=[str(self.server._root)]) as mocked:
            # mocks for initial data setup in post
            mocked.get(self.iac_url, payload=self.iac_json)
            mocked.get(self.case_url, payload=self.case_json)
            # mocks for the payload builder
            mocked.get(self.collection_instrument_url, payload=self.collection_instrument_json)
            mocked.get(self.collection_exercise_url, payload=self.collection_exercise_json)
            mocked.get(self.collection_exercise_events_url, payload=self.collection_exercise_events_json)
            mocked.get(self.sample_attributes_url, payload=self.sample_attributes_json)
            mocked.get(self.survey_url, payload=self.survey_json)
            mocked.post(self.case_events_url, status=500)

            with self.assertLogs('app.case', 'ERROR') as cm:
                response = await self.client.request("POST", "/", allow_redirects=False, data=self.form_data)
            self.assertLogLine(cm, "Error posting case event", status_code=500, case_id=self.case_id)

        self.assertEqual(response.status, 200)
        self.assertIn(f'500 {SERVER_ERROR_MSG}'.encode(), await response.content.read())

    @unittest_run_loop
    async def test_post_index_caseid_missing(self):
        iac_json = self.iac_json.copy()
        del iac_json['caseId']

        with aioresponses(passthrough=[str(self.server._root)]) as mocked:
            mocked.get(self.iac_url, payload=iac_json)

            with self.assertLogs('respondent-home', 'ERROR') as cm:
                response = await self.client.request("POST", "/", allow_redirects=False, data=self.form_data)
            self.assertLogLine(cm, 'caseId missing from IAC response')

        self.assertEqual(response.status, 200)
        self.assertIn(BAD_RESPONSE_MSG.encode(), await response.content.read())

    @unittest_run_loop
    async def test_post_index_sampleUnitType_missing(self):
        case_json = self.case_json.copy()
        del case_json['sampleUnitType']

        with aioresponses(passthrough=[str(self.server._root)]) as mocked:
            mocked.get(self.iac_url, payload=self.iac_json)
            mocked.get(self.case_url, payload=case_json)

            with self.assertLogs('respondent-home', 'ERROR') as cm:
                response = await self.client.request("POST", "/", allow_redirects=False, data=self.form_data)
            self.assertLogLine(cm, 'sampleUnitType missing from case response')

        self.assertEqual(response.status, 200)
        self.assertIn(BAD_RESPONSE_MSG.encode(), await response.content.read())

    @unittest_run_loop
    async def test_post_index_sampleUnitType_B_error(self):
        case_json = self.case_json.copy()
        case_json['sampleUnitType'] = 'B'

        with aioresponses(passthrough=[str(self.server._root)]) as mocked:
            mocked.get(self.iac_url, payload=self.iac_json)
            mocked.get(self.case_url, payload=case_json)

            with self.assertLogs('respondent-home', 'ERROR') as cm:
                response = await self.client.request("POST", "/", allow_redirects=False, data=self.form_data)
            self.assertLogLine(cm, 'Attempt to use unexpected sample unit type', sample_unit_type='B')

        self.assertEqual(response.status, 200)
        self.assertIn(INVALID_CODE_MSG.encode(), await response.content.read())

    @unittest_run_loop
    async def test_post_index_malformed(self):
        form_data = self.form_data.copy()
        del form_data['iac3']

        with aioresponses(passthrough=[str(self.server._root)]) as mocked:
            mocked.get(self.iac_url, payload=self.iac_json)

            with self.assertLogs('respondent-home', 'WARNING') as cm:
                response = await self.client.request("POST", "/", data=form_data)
            self.assertLogLine(cm, "Attempt to use a malformed access code")

        self.assertEqual(response.status, 200)
        self.assertIn(BAD_CODE_MSG.encode(), await response.content.read())

    @unittest_run_loop
    async def test_post_index_iac_active_missing(self):
        iac_json = self.iac_json.copy()
        del iac_json['active']

        with aioresponses(passthrough=[str(self.server._root)]) as mocked:
            mocked.get(self.iac_url, payload=iac_json)

            with self.assertLogs('respondent-home', 'INFO') as cm:
                response = await self.client.request("POST", "/", data=self.form_data)
            self.assertLogLine(cm, "Attempt to use an inactive access code")

        self.assertEqual(response.status, 200)
        self.assertIn(CODE_USED_MSG.encode(), await response.content.read())

    @unittest_run_loop
    async def test_post_index_iac_inactive(self):
        iac_json = self.iac_json.copy()
        iac_json['active'] = False

        with aioresponses(passthrough=[str(self.server._root)]) as mocked:
            mocked.get(self.iac_url, payload=iac_json)

            with self.assertLogs('respondent-home', 'INFO') as cm:
                response = await self.client.request("POST", "/", data=self.form_data)
            self.assertLogLine(cm, "Attempt to use an inactive access code")

        self.assertEqual(response.status, 200)
        self.assertIn(CODE_USED_MSG.encode(), await response.content.read())

    @unittest_run_loop
    async def test_post_index_iac_service_connection_error(self):
        with aioresponses(passthrough=[str(self.server._root)]) as mocked:
            mocked.get(self.iac_url, exception=ClientConnectionError('Failed'))

            with self.assertLogs('respondent-home', 'ERROR') as cm:
                response = await self.client.request("POST", "/", data=self.form_data)
            self.assertLogLine(cm, "Client failed to connect to iac service")

        self.assertEqual(response.status, 200)
        self.assertIn(CONNECTION_ERROR_MSG.encode(), await response.content.read())

    @unittest_run_loop
    async def test_post_index_iac_service_500(self):
        with aioresponses(passthrough=[str(self.server._root)]) as mocked:
            mocked.get(self.iac_url, status=500)

            with self.assertLogs('respondent-home', 'ERROR') as cm:
                response = await self.client.request("POST", "/", data=self.form_data)
            self.assertLogLine(cm, "Error in response", status_code=500)

        self.assertEqual(response.status, 200)
        self.assertIn(f'500 {SERVER_ERROR_MSG}'.encode(), await response.content.read())

    @unittest_run_loop
    async def test_post_index_iac_service_503(self):
        with aioresponses(passthrough=[str(self.server._root)]) as mocked:
            mocked.get(self.iac_url, status=503)

            with self.assertLogs('respondent-home', 'ERROR') as cm:
                response = await self.client.request("POST", "/", data=self.form_data)
            self.assertLogLine(cm, "Error in response", status_code=503)

        self.assertEqual(response.status, 200)
        self.assertIn(f'503 {SERVER_ERROR_MSG}'.encode(), await response.content.read())

    @unittest_run_loop
    async def test_post_index_iac_service_404(self):
        with aioresponses(passthrough=[str(self.server._root)]) as mocked:
            mocked.get(self.iac_url, status=404)

            with self.assertLogs('respondent-home', 'INFO') as cm:
                response = await self.client.request("POST", "/", data=self.form_data)
            self.assertLogLine(cm, "Attempt to use an invalid access code", client_ip=None)

        self.assertEqual(response.status, 200)
        self.assertIn(BAD_CODE_MSG.encode(), await response.content.read())

    @unittest_run_loop
    async def test_post_index_iac_service_403(self):
        with aioresponses(passthrough=[str(self.server._root)]) as mocked:
            mocked.get(self.iac_url, status=403)

            with self.assertLogs('respondent-home', 'INFO') as cm:
                response = await self.client.request("POST", "/", data=self.form_data)
            self.assertLogLine(cm, "Unauthorized access to IAC service attempted", client_ip=None)

        self.assertEqual(response.status, 200)
        self.assertIn(NOT_AUTHORIZED_MSG.encode(), await response.content.read())

    @unittest_run_loop
    async def test_post_index_iac_service_401(self):
        with aioresponses(passthrough=[str(self.server._root)]) as mocked:
            mocked.get(self.iac_url, status=401)

            with self.assertLogs('respondent-home', 'INFO') as cm:
                response = await self.client.request("POST", "/", data=self.form_data)
            self.assertLogLine(cm, "Unauthorized access to IAC service attempted", client_ip=None)

        self.assertEqual(response.status, 200)
        self.assertIn(NOT_AUTHORIZED_MSG.encode(), await response.content.read())

    @unittest_run_loop
    async def test_post_index_iac_service_400(self):
        with aioresponses(passthrough=[str(self.server._root)]) as mocked:
            mocked.get(self.iac_url, status=400)

            with self.assertLogs('respondent-home', 'INFO') as cm:
                response = await self.client.request("POST", "/", data=self.form_data)
            self.assertLogLine(cm, "Client error when accessing IAC service", client_ip=None, status=400)

        self.assertEqual(response.status, 200)
        self.assertIn(BAD_RESPONSE_MSG.encode(), await response.content.read())

    def test_join_iac(self):
        # Given some post data
        post_data = {'iac1': '1234', 'iac2': '5678', 'iac3': '9012', 'action[save_continue]': ''}

        # When join_iac is called
        result = join_iac(post_data)

        # Then a single string built from the iac values is returned
        self.assertEqual(result, post_data['iac1'] + post_data['iac2'] + post_data['iac3'])

    def test_join_iac_missing(self):
        # Given some missing post data
        post_data = {'action[save_continue]': ''}

        # When join_iac is called
        with self.assertRaises(TypeError):
            join_iac(post_data)
        # Then a TypeError is raised

    def test_join_iac_some_missing(self):
        # Given some missing post data
        post_data = {'iac1': '1234', 'iac2': '5678', 'iac3': '', 'action[save_continue]': ''}

        # When join_iac is called
        with self.assertRaises(TypeError):
            join_iac(post_data)
        # Then a TypeError is raised

    def test_validate_case(self):
        # Given a dict with an active key and value
        case_json = {'active': True}

        # When validate_case is called
        validate_case(case_json)

        # Nothing happens

    def test_validate_case_inactive(self):
        # Given a dict with an active key and value
        case_json = {'active': False}

        # When validate_case is called
        with self.assertRaises(InactiveCaseError):
            validate_case(case_json)

        # Then an InactiveCaseError is raised

    def test_validate_case_empty(self):
        # Given an empty dict
        case_json = {}

        # When validate_case is called
        with self.assertRaises(InactiveCaseError):
            validate_case(case_json)

        # Then an InactiveCaseError is raised
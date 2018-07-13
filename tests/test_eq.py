import functools
import json
import time
import uuid
from unittest import mock
from urllib.parse import urlsplit, parse_qs

from aiohttp.client_exceptions import ClientConnectionError, ClientConnectorError
from aiohttp.test_utils import AioHTTPTestCase, unittest_run_loop
from aioresponses import aioresponses

from app.app import create_app
from app.eq import format_date
from app.handlers import join_iac, _validate_case
from app.exceptions import InvalidEqPayLoad, InactiveCaseError


def skip_build_eq(func, *args, **kwargs):
    """
    Helper decorator for manually patching the methods of app.eq.EqPayloadConstructor.

    This can be useful for tests that perform as a client but wish the server to skip the builder functionality.

    The test case checks for and calls when possible .setUp and .tearDown attributes on each test method
    at server setUp (setUpAsync) and server tearDown (tearDownAsync).

    :param func: test method that requires the patch
    :param args: the test method's arguments
    :param args: the test method's keyword arguments
    :return: new method with patching functions attached as attributes
    """

    async def _override_eq_payload_constructor(test_case, *_):
        from app import eq

        async def build(_):
            return test_case.eq_payload

        eq.EqPayloadConstructor._bk__init__ = eq.EqPayloadConstructor.__init__
        eq.EqPayloadConstructor.__init__ = lambda *args: None
        eq.EqPayloadConstructor._bk_build = eq.EqPayloadConstructor.build
        eq.EqPayloadConstructor.build = build

    async def _reset_eq_payload_constructor(*_):
        from app import eq

        eq.EqPayloadConstructor.__init__ = eq.EqPayloadConstructor._bk__init__
        eq.EqPayloadConstructor.build = eq.EqPayloadConstructor._bk_build

    @functools.wraps(func, *args, **kwargs)
    def new_func(self, *inner_args, **inner_kwargs):
        return func(self, *inner_args, **inner_kwargs)

    new_func.setUp = _override_eq_payload_constructor
    new_func.tearDown = _reset_eq_payload_constructor

    return new_func


def build_eq_raises(func, *args, **kwargs):
    """
    Helper decorator for manually patching the methods of app.eq.EqPayloadConstructor.

    This can be useful for tests that perform as a client but wish the server to raise InvalidEqPayLoad when .build()
    is called on an instance of app.eq.EqPayloadConstructor.

    The test case checks for and calls when possible .setUp and .tearDown attributes on each test method
    at server setUp (setUpAsync) and server tearDown (tearDownAsync).

    :param func: test method that requires the patch
    :param args: the test method's arguments
    :param args: the test method's keyword arguments
    :return: new method with patching functions attached as attributes
    """

    async def _override_eq_build_with_error(*_):
        from app import eq

        async def build(_):
            raise InvalidEqPayLoad('')

        eq.EqPayloadConstructor._bk__init__ = eq.EqPayloadConstructor.__init__
        eq.EqPayloadConstructor.__init__ = lambda *args: None
        eq.EqPayloadConstructor._bk_build = eq.EqPayloadConstructor.build
        eq.EqPayloadConstructor.build = build

    async def _reset_eq_payload_constructor(*_):
        from app import eq

        eq.EqPayloadConstructor.__init__ = eq.EqPayloadConstructor._bk__init__
        eq.EqPayloadConstructor.build = eq.EqPayloadConstructor._bk_build

    @functools.wraps(func, *args, **kwargs)
    def new_func(self, *inner_args, **inner_kwargs):
        return func(self, *inner_args, **inner_kwargs)

    new_func.setUp = _override_eq_build_with_error
    new_func.tearDown = _reset_eq_payload_constructor

    return new_func


def skip_encrypt(func, *args, **kwargs):
    """
    Helper decorator for manually patching the encrypt function in handlers.py.

    This can be useful for tests that perform as a client but wish the server to skip encrypting a payload.

    The test case checks for and calls when possible .setUp and .tearDown attributes on each test method
    at server setUp (setUpAsync) and server tearDown (tearDownAsync).

    :param func: test method that requires the patch
    :param args: the test method's arguments
    :param args: the test method's keyword arguments
    :return: new method with patching functions attached as attributes
    """

    async def _override_sdc_encrypt(*_):
        from app import handlers

        def encrypt(payload, **_):
            return json.dumps(payload)

        handlers._bk_encrypt = handlers.encrypt
        handlers.encrypt = encrypt

    async def _reset_sdc_encrypt(*_):
        from app import handlers

        handlers.encrypt = handlers._bk_encrypt

    @functools.wraps(func, *args, **kwargs)
    def new_func(self, *inner_args, **inner_kwargs):
        return func(self, *inner_args, **inner_kwargs)

    new_func.setUp = _override_sdc_encrypt
    new_func.tearDown = _reset_sdc_encrypt

    return new_func


class TestGenerateEqURL(AioHTTPTestCase):

    region_code = 'GB-ENG'
    language_code = 'en'

    start_date = '2018-04-10'
    end_date = '2020-05-31'
    return_by = '2018-05-08'

    async def get_application(self):
        return create_app('TestingConfig')

    async def setUpAsync(self):
        test_method = getattr(self, self._testMethodName)
        if hasattr(test_method, 'setUp'):
            await test_method.setUp(self)

    async def tearDownAsync(self):
        test_method = getattr(self, self._testMethodName)
        if hasattr(test_method, 'tearDown'):
            await test_method.tearDown(self)

    def assertLogLine(self, watcher, event, **kwargs):
        """
        Helper method for asserting the contents of structlog records caught by self.assertLogs.

        Fails if no match is found. A match is based on the main log message (event) and all additional
        items passed in kwargs.

        :param watcher: context manager returned by `with self.assertLogs(LOGGER, LEVEL)`
        :param event: event logged; use empty string to ignore or no message
        :param kwargs: other structlog key value pairs to assert for
        """
        for record in watcher.records:
            message_json = json.loads(record.message)
            try:
                if (
                    event in message_json.get('event', '')
                    and all(message_json[key] == val for key, val in kwargs.items())
                ):
                    break
            except KeyError:
                pass
        else:
            self.fail(f'No matching log records present: {event}')

    def setUp(self):
        super().setUp()  # NB: setUp the server first so we can use self.app
        with open('tests/test_data/case/case.json') as fp:
            self.case_json = json.load(fp)
        with open('tests/test_data/collection_exercise/collection_exercise.json') as fp:
            self.collection_exercise_json = json.load(fp)
        with open('tests/test_data/collection_exercise/collection_exercise_events.json') as fp:
            self.collection_exercise_events_json = json.load(fp)
        with open('tests/test_data/collection_instrument/collection_instrument_eq.json') as fp:
            self.collection_instrument_json = json.load(fp)
        with open('tests/test_data/party/party.json') as fp:
            self.party_json = json.load(fp)
        with open('tests/test_data/survey/survey.json') as fp:
            self.survey_json = json.load(fp)

        self.action_plan_id = self.case_json['actionPlanId']
        self.case_id = self.case_json['id']
        self.case_group_id = self.case_json['caseGroup']['id']
        self.case_ref = self.case_json['caseRef']
        self.collection_exercise_id = self.collection_exercise_json['id']
        self.collection_exercise_ref = self.collection_exercise_json['exerciseRef']
        self.collection_exercise_user_desc = self.collection_exercise_json['userDescription']
        self.collection_instrument_id = self.collection_instrument_json['id']
        self.eq_id = self.collection_instrument_json['classifiers']['eq_id']
        self.form_type = self.collection_instrument_json['classifiers']['form_type']
        self.jti = str(uuid.uuid4())
        self.iac_code = ''.join([str(n) for n in range(11)])
        self.iac1, self.iac2, self.iac3 = self.iac_code[:4], self.iac_code[4:8], self.iac_code[8:]
        self.iac_json = {'active': '1', 'caseId': self.case_id}
        self.party_id = self.party_json['id']
        self.ru_name = self.party_json['name']
        self.sample_unit_ref = self.party_json['sampleUnitRef']
        self.sample_unit_type = self.party_json['sampleUnitType']
        self.survey_id = self.survey_json['id']
        self.survey_ref = self.survey_json['surveyRef']
        self.trading_as = (
            f"{self.party_json['tradstyle1']} {self.party_json['tradstyle2']} {self.party_json['tradstyle3']}"
        )
        self.eq_payload = {
            "jti": self.jti,
            "tx_id": self.jti,
            "user_id": self.party_id,
            "iat": int(time.time()),
            "exp": int(time.time() + (5 * 60)),
            "eq_id": self.eq_id,
            "period_str": self.collection_exercise_user_desc,
            "period_id": self.collection_exercise_ref,
            "form_type": self.form_type,
            "collection_exercise_sid": self.collection_exercise_id,
            "ru_ref": self.sample_unit_ref + 'C',
            "ru_name": self.ru_name,
            "survey_id": self.survey_ref,
            "case_id": self.case_id,
            "case_ref": self.case_ref,
            "account_service_url": self.app['ACCOUNT_SERVICE_URL'],
            "trad_as": self.trading_as,
            "region_code": self.region_code,
            "language_code": self.language_code,
            "return_by": self.return_by,
            "ref_p_end_date": self.end_date,
            "ref_p_start_date": self.start_date
        }

        self.case_url = (
            f"{self.app['CASE_URL']}/cases/{self.case_id}"
        )
        self.case_events_url = (
            f"{self.app['CASE_URL']}/cases/{self.case_id}/events"
        )
        self.collection_instrument_url = (
            f"{self.app['COLLECTION_INSTRUMENT_URL']}"
            f"/collection-instrument-api/1.0.2/collectioninstrument/id/{self.collection_instrument_id}"
        )
        self.collection_exercise_url = (
            f"{self.app['COLLECTION_EXERCISE_URL']}"
            f"/collectionexercises/{self.collection_exercise_id}"
        )
        self.collection_exercise_events_url = (
            f"{self.app['COLLECTION_EXERCISE_URL']}"
            f"/collectionexercises/{self.collection_exercise_id}/events"
        )
        self.iac_url = (
            f"{self.app['IAC_URL']}/iacs/{self.iac_code}"
        )
        self.party_url = (
            f"{self.app['PARTY_URL']}/party-api/v1/businesses/id/{self.party_id}?verbose=True"
        )
        self.survey_url = (
            f"{self.app['SURVEY_URL']}/surveys/{self.survey_id}"
        )

        self.form_data = {
            'iac1': self.iac1, 'iac2': self.iac2, 'iac3': self.iac3, 'action[save_continue]': '',
        }

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
        self.assertIn(b'Service connection error', await response.content.read())

    @unittest_run_loop
    async def test_post_index_no_iac_json(self):
        with aioresponses(passthrough=[str(self.server._root)]) as mocked:
            mocked.get(self.iac_url, content_type='text')

            with self.assertLogs('respondent-home', 'ERROR') as cm:
                response = await self.client.request("POST", "/", allow_redirects=False, data=self.form_data)
            self.assertLogLine(cm, "Service failed to return expected JSON payload")

        self.assertEqual(response.status, 200)
        self.assertIn(b'Server error', await response.content.read())

    @unittest_run_loop
    async def test_post_index_case_403(self):
        with aioresponses(passthrough=[str(self.server._root)]) as mocked:
            mocked.get(self.iac_url, payload=self.iac_json)
            mocked.get(self.case_url, status=403)

            with self.assertLogs('app.case', 'ERROR') as cm:
                response = await self.client.request("POST", "/", allow_redirects=False, data=self.form_data)
            self.assertLogLine(cm, "Error retrieving case", case_id=self.case_id, status_code=403)

        self.assertEqual(response.status, 200)
        self.assertIn(b'403 Server error', await response.content.read())

    @unittest_run_loop
    async def test_post_index_case_500(self):
        with aioresponses(passthrough=[str(self.server._root)]) as mocked:
            mocked.get(self.iac_url, payload=self.iac_json)
            mocked.get(self.case_url, status=500)

            with self.assertLogs('app.case', 'ERROR') as cm:
                response = await self.client.request("POST", "/", data=self.form_data)
            self.assertLogLine(cm, "Error retrieving case", case_id=self.case_id, status_code=500)

        self.assertEqual(response.status, 200)
        self.assertIn(b'500 Server error', await response.content.read())

    @unittest_run_loop
    async def test_post_index_case_connector_error(self):
        with aioresponses(passthrough=[str(self.server._root)]) as mocked:
            mocked.get(self.iac_url, payload=self.iac_json)
            mocked.get(self.case_url, exception=ClientConnectorError(mock.MagicMock(), mock.MagicMock()))

            with self.assertLogs('respondent-home', 'ERROR') as cm:
                response = await self.client.request("POST", "/", data=self.form_data)
            self.assertLogLine(cm, "Service connection error")

        self.assertEqual(response.status, 200)
        self.assertIn(b'Service connection error', await response.content.read())

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
        self.assertIn(b'Service connection error', await response.content.read())

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
            mocked.get(self.party_url, payload=self.party_json)
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
        self.assertIn(b'Failed to redirect to survey', await response.content.read())

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
        self.assertIn(b'500 Server error', await response.content.read())

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
        self.assertIn(b'400 Server error', await response.content.read())

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
        self.assertIn(b'503 Server error', await response.content.read())

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
        self.assertIn(b'404 Server error', await response.content.read())

    @unittest_run_loop
    async def test_post_index_with_build_party_403(self):
        with aioresponses(passthrough=[str(self.server._root)]) as mocked:
            # mocks for initial data setup in post
            mocked.get(self.iac_url, payload=self.iac_json)
            mocked.get(self.case_url, payload=self.case_json)
            mocked.post(self.case_events_url)
            # mocks for the payload builder
            mocked.get(self.collection_instrument_url, payload=self.collection_instrument_json)
            mocked.get(self.collection_exercise_url, payload=self.collection_exercise_json)
            mocked.get(self.collection_exercise_events_url, payload=self.collection_exercise_events_json)
            mocked.get(self.party_url, status=403)

            with self.assertLogs('app.eq', 'ERROR') as cm:
                response = await self.client.request("POST", "/", allow_redirects=False, data=self.form_data)
            self.assertLogLine(cm, "Error in response", status_code=403)

        self.assertEqual(response.status, 200)
        self.assertIn(b'403 Server error', await response.content.read())

    @unittest_run_loop
    async def test_post_index_with_build_survey_500(self):
        with aioresponses(passthrough=[str(self.server._root)]) as mocked:
            # mocks for initial data setup in post
            mocked.get(self.iac_url, payload=self.iac_json)
            mocked.get(self.case_url, payload=self.case_json)
            mocked.post(self.case_events_url)
            # mocks for the payload builder
            mocked.get(self.collection_instrument_url, payload=self.collection_instrument_json)
            mocked.get(self.collection_exercise_url, payload=self.collection_exercise_json)
            mocked.get(self.collection_exercise_events_url, payload=self.collection_exercise_events_json)
            mocked.get(self.party_url, payload=self.party_json)
            mocked.get(self.survey_url, status=500)

            with self.assertLogs('app.eq', 'ERROR') as cm:
                response = await self.client.request("POST", "/", allow_redirects=False, data=self.form_data)
            self.assertLogLine(cm, "Error in response", status_code=500)

        self.assertEqual(response.status, 200)
        self.assertIn(b'500 Server error', await response.content.read())

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
            mocked.get(self.party_url, payload=self.party_json)
            mocked.get(self.survey_url, payload=self.survey_json)
            mocked.post(self.case_events_url, status=500)

            with self.assertLogs('app.case', 'ERROR') as cm:
                response = await self.client.request("POST", "/", allow_redirects=False, data=self.form_data)
            self.assertLogLine(cm, "Error posting case event", status_code=500, case_id=self.case_id)

        self.assertEqual(response.status, 200)
        self.assertIn(b'500 Server error', await response.content.read())

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
        self.assertIn(b'Bad response', await response.content.read())

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
        self.assertIn(b'Please provide the unique access code', await response.content.read())

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
        self.assertIn(b'already been used', await response.content.read())

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
        self.assertIn(b'already been used', await response.content.read())

    @unittest_run_loop
    async def test_post_index_iac_service_connection_error(self):
        with aioresponses(passthrough=[str(self.server._root)]) as mocked:
            mocked.get(self.iac_url, exception=ClientConnectionError('Failed'))

            with self.assertLogs('respondent-home', 'ERROR') as cm:
                response = await self.client.request("POST", "/", data=self.form_data)
            self.assertLogLine(cm, "Client failed to connect to iac service")

        self.assertEqual(response.status, 200)
        self.assertIn(b'Service connection error', await response.content.read())

    @unittest_run_loop
    async def test_post_index_iac_service_500(self):
        with aioresponses(passthrough=[str(self.server._root)]) as mocked:
            mocked.get(self.iac_url, status=500)

            with self.assertLogs('respondent-home', 'ERROR') as cm:
                response = await self.client.request("POST", "/", data=self.form_data)
            self.assertLogLine(cm, "Error in response", status_code=500)

        self.assertEqual(response.status, 200)
        self.assertIn(b'500 Server error', await response.content.read())

    @unittest_run_loop
    async def test_post_index_iac_service_503(self):
        with aioresponses(passthrough=[str(self.server._root)]) as mocked:
            mocked.get(self.iac_url, status=503)

            with self.assertLogs('respondent-home', 'ERROR') as cm:
                response = await self.client.request("POST", "/", data=self.form_data)
            self.assertLogLine(cm, "Error in response", status_code=503)

        self.assertEqual(response.status, 200)
        self.assertIn(b'503 Server error', await response.content.read())

    @unittest_run_loop
    async def test_post_index_iac_service_404(self):
        with aioresponses(passthrough=[str(self.server._root)]) as mocked:
            mocked.get(self.iac_url, status=404)

            with self.assertLogs('respondent-home', 'INFO') as cm:
                response = await self.client.request("POST", "/", data=self.form_data)
            self.assertLogLine(cm, "Attempt to use an invalid access code", client_ip=None)

        self.assertEqual(response.status, 200)
        self.assertIn(b'Please provide the unique access code', await response.content.read())

    @unittest_run_loop
    async def test_post_index_iac_service_403(self):
        with aioresponses(passthrough=[str(self.server._root)]) as mocked:
            mocked.get(self.iac_url, status=403)

            with self.assertLogs('respondent-home', 'INFO') as cm:
                response = await self.client.request("POST", "/", data=self.form_data)
            self.assertLogLine(cm, "Unauthorized access to IAC service attempted", client_ip=None)

        self.assertEqual(response.status, 200)
        self.assertIn(b'not authorized', await response.content.read())

    @unittest_run_loop
    async def test_post_index_iac_service_401(self):
        with aioresponses(passthrough=[str(self.server._root)]) as mocked:
            mocked.get(self.iac_url, status=401)

            with self.assertLogs('respondent-home', 'INFO') as cm:
                response = await self.client.request("POST", "/", data=self.form_data)
            self.assertLogLine(cm, "Unauthorized access to IAC service attempted", client_ip=None)

        self.assertEqual(response.status, 200)
        self.assertIn(b'not authorized', await response.content.read())

    @unittest_run_loop
    async def test_post_index_iac_service_400(self):
        with aioresponses(passthrough=[str(self.server._root)]) as mocked:
            mocked.get(self.iac_url, status=400)

            with self.assertLogs('respondent-home', 'INFO') as cm:
                response = await self.client.request("POST", "/", data=self.form_data)
            self.assertLogLine(cm, "Client error when accessing IAC service", client_ip=None, status=400)

        self.assertEqual(response.status, 200)
        self.assertIn(b'Bad request', await response.content.read())

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

    def test_validate_case(self):
        # Given a dict with an active key and value
        case_json = {'active': True}

        # When _validate_case is called
        _validate_case(case_json)

        # Nothing happens

    def test_validate_case_inactive(self):
        # Given a dict with an active key and value
        case_json = {'active': False}

        # When _validate_case is called
        with self.assertRaises(InactiveCaseError):
            _validate_case(case_json)

        # Then an InactiveCaseError is raised

    def test_validate_case_empty(self):
        # Given an empty dict
        case_json = {}

        # When _validate_case is called
        with self.assertRaises(InactiveCaseError):
            _validate_case(case_json)

        # Then an InactiveCaseError is raised

    def test_create_eq_constructor(self):
        from app import eq

        self.assertIsInstance(eq.EqPayloadConstructor(self.case_json, self.app), eq.EqPayloadConstructor)

    @unittest_run_loop
    async def test_build(self):
        self.maxDiff = None  # for full payload comparison when running this test
        with mock.patch('app.eq.uuid4') as mocked_uuid4, mock.patch('app.eq.time.time') as mocked_time:
            # NB: has to be mocked after setup but before import
            mocked_time.return_value = self.eq_payload['iat']
            mocked_uuid4.return_value = self.jti

            from app import eq  # NB: local import to avoid overwriting the patched version for some tests

            with aioresponses() as mocked:
                mocked.get(self.collection_instrument_url, payload=self.collection_instrument_json)
                mocked.get(self.collection_exercise_url, payload=self.collection_exercise_json)
                mocked.get(self.collection_exercise_events_url, payload=self.collection_exercise_events_json)
                mocked.get(self.party_url, payload=self.party_json)
                mocked.get(self.survey_url, payload=self.survey_json)

                with self.assertLogs('app.eq', 'INFO') as cm:
                    payload = await eq.EqPayloadConstructor(self.case_json, self.app).build()
                self.assertLogLine(cm, '', payload=payload)

        mocked_uuid4.assert_called()
        mocked_time.assert_called()
        self.assertEqual(payload, self.eq_payload)

    @unittest_run_loop
    async def test_build_raises_InvalidEqPayLoad_bad_ci_type(self):
        ci_json = self.collection_instrument_json.copy()
        ci_json['type'] = 'not_eq'

        from app import eq  # NB: local import to avoid overwriting the patched version for some tests

        with aioresponses() as mocked:
            mocked.get(self.collection_instrument_url, payload=ci_json)

            with self.assertRaises(InvalidEqPayLoad):
                await eq.EqPayloadConstructor(self.case_json, self.app).build()

    @unittest_run_loop
    async def test_build_raises_InvalidEqPayLoad_missing_ci_type(self):
        ci_json = self.collection_instrument_json.copy()
        del ci_json['type']

        from app import eq  # NB: local import to avoid overwriting the patched version for some tests

        with aioresponses() as mocked:
            mocked.get(self.collection_instrument_url, payload=ci_json)

            with self.assertRaises(InvalidEqPayLoad):
                await eq.EqPayloadConstructor(self.case_json, self.app).build()

    @unittest_run_loop
    async def test_build_raises_InvalidEqPayLoad_missing_classifiers(self):
        ci_json = self.collection_instrument_json.copy()
        del ci_json['classifiers']

        from app import eq  # NB: local import to avoid overwriting the patched version for some tests

        with aioresponses() as mocked:
            mocked.get(self.collection_instrument_url, payload=ci_json)

            with self.assertRaises(InvalidEqPayLoad):
                await eq.EqPayloadConstructor(self.case_json, self.app).build()

    @unittest_run_loop
    async def test_build_raises_InvalidEqPayLoad_missing_eq_id(self):
        ci_json = self.collection_instrument_json.copy()
        del ci_json['classifiers']['eq_id']

        from app import eq  # NB: local import to avoid overwriting the patched version for some tests

        with aioresponses() as mocked:
            mocked.get(self.collection_instrument_url, payload=ci_json)

            with self.assertRaises(InvalidEqPayLoad):
                await eq.EqPayloadConstructor(self.case_json, self.app).build()

    @unittest_run_loop
    async def test_build_raises_InvalidEqPayLoad_missing_form_type(self):
        ci_json = self.collection_instrument_json.copy()
        del ci_json['classifiers']['form_type']

        from app import eq  # NB: local import to avoid overwriting the patched version for some tests

        with aioresponses() as mocked:
            mocked.get(self.collection_instrument_url, payload=ci_json)

            with self.assertRaises(InvalidEqPayLoad):
                await eq.EqPayloadConstructor(self.case_json, self.app).build()

    @unittest_run_loop
    async def test_build_raises_InvalidEqPayLoad_missing_userDescription(self):
        ce_json = self.collection_exercise_json.copy()
        del ce_json['userDescription']

        from app import eq  # NB: local import to avoid overwriting the patched version for some tests

        with aioresponses() as mocked:
            mocked.get(self.collection_instrument_url, payload=self.collection_instrument_json)
            mocked.get(self.collection_exercise_url, payload=ce_json)

            with self.assertRaises(InvalidEqPayLoad):
                await eq.EqPayloadConstructor(self.case_json, self.app).build()

    @unittest_run_loop
    async def test_build_raises_InvalidEqPayLoad_missing_exerciseRef(self):
        ce_json = self.collection_exercise_json.copy()
        del ce_json['exerciseRef']

        from app import eq  # NB: local import to avoid overwriting the patched version for some tests

        with aioresponses() as mocked:
            mocked.get(self.collection_instrument_url, payload=self.collection_instrument_json)
            mocked.get(self.collection_exercise_url, payload=ce_json)

            with self.assertRaises(InvalidEqPayLoad):
                await eq.EqPayloadConstructor(self.case_json, self.app).build()

    @unittest_run_loop
    async def test_build_raises_InvalidEqPayLoad_missing_exercise_id(self):
        ce_json = self.collection_exercise_json.copy()
        del ce_json['id']

        from app import eq  # NB: local import to avoid overwriting the patched version for some tests

        with aioresponses() as mocked:
            mocked.get(self.collection_instrument_url, payload=self.collection_instrument_json)
            mocked.get(self.collection_exercise_url, payload=ce_json)

            with self.assertRaises(InvalidEqPayLoad):
                await eq.EqPayloadConstructor(self.case_json, self.app).build()

    @unittest_run_loop
    async def test_build_raises_InvalidEqPayLoad_missing_survey_id(self):
        ce_json = self.collection_exercise_json.copy()
        del ce_json['surveyId']

        from app import eq  # NB: local import to avoid overwriting the patched version for some tests

        with aioresponses() as mocked:
            mocked.get(self.collection_instrument_url, payload=self.collection_instrument_json)
            mocked.get(self.collection_exercise_url, payload=ce_json)

            with self.assertRaises(InvalidEqPayLoad):
                await eq.EqPayloadConstructor(self.case_json, self.app).build()

    @unittest_run_loop
    async def test_build_raises_InvalidEqPayLoad_missing_sampleUnitRef(self):
        party_json = self.party_json.copy()
        del party_json['sampleUnitRef']

        from app import eq  # NB: local import to avoid overwriting the patched version for some tests

        with aioresponses() as mocked:
            mocked.get(self.collection_instrument_url, payload=self.collection_instrument_json)
            mocked.get(self.collection_exercise_url, payload=self.collection_exercise_json)
            mocked.get(self.collection_exercise_events_url, payload=self.collection_exercise_events_json)
            mocked.get(self.party_url, payload=party_json)

            with self.assertRaises(InvalidEqPayLoad):
                await eq.EqPayloadConstructor(self.case_json, self.app).build()

    @unittest_run_loop
    async def test_build_raises_InvalidEqPayLoad_missing_checkletter(self):
        party_json = self.party_json.copy()
        del party_json['checkletter']

        from app import eq  # NB: local import to avoid overwriting the patched version for some tests

        with aioresponses() as mocked:
            mocked.get(self.collection_instrument_url, payload=self.collection_instrument_json)
            mocked.get(self.collection_exercise_url, payload=self.collection_exercise_json)
            mocked.get(self.collection_exercise_events_url, payload=self.collection_exercise_events_json)
            mocked.get(self.party_url, payload=party_json)

            with self.assertRaises(InvalidEqPayLoad):
                await eq.EqPayloadConstructor(self.case_json, self.app).build()

    @unittest_run_loop
    async def test_build_raises_InvalidEqPayLoad_missing_name(self):
        party_json = self.party_json.copy()
        del party_json['name']

        from app import eq  # NB: local import to avoid overwriting the patched version for some tests

        with aioresponses() as mocked:
            mocked.get(self.collection_instrument_url, payload=self.collection_instrument_json)
            mocked.get(self.collection_exercise_url, payload=self.collection_exercise_json)
            mocked.get(self.collection_exercise_events_url, payload=self.collection_exercise_events_json)
            mocked.get(self.party_url, payload=party_json)

            with self.assertRaises(InvalidEqPayLoad):
                await eq.EqPayloadConstructor(self.case_json, self.app).build()

    @unittest_run_loop
    async def test_build_raises_InvalidEqPayLoad_missing_tradstyle1(self):
        party_json = self.party_json.copy()
        del party_json['tradstyle1']

        from app import eq  # NB: local import to avoid overwriting the patched version for some tests

        with aioresponses() as mocked:
            mocked.get(self.collection_instrument_url, payload=self.collection_instrument_json)
            mocked.get(self.collection_exercise_url, payload=self.collection_exercise_json)
            mocked.get(self.collection_exercise_events_url, payload=self.collection_exercise_events_json)
            mocked.get(self.party_url, payload=party_json)

            with self.assertRaises(InvalidEqPayLoad):
                await eq.EqPayloadConstructor(self.case_json, self.app).build()

    @unittest_run_loop
    async def test_build_raises_InvalidEqPayLoad_missing_tradstyle2(self):
        party_json = self.party_json.copy()
        del party_json['tradstyle2']

        from app import eq  # NB: local import to avoid overwriting the patched version for some tests

        with aioresponses() as mocked:
            mocked.get(self.collection_instrument_url, payload=self.collection_instrument_json)
            mocked.get(self.collection_exercise_url, payload=self.collection_exercise_json)
            mocked.get(self.collection_exercise_events_url, payload=self.collection_exercise_events_json)
            mocked.get(self.party_url, payload=party_json)

            with self.assertRaises(InvalidEqPayLoad):
                await eq.EqPayloadConstructor(self.case_json, self.app).build()

    @unittest_run_loop
    async def test_build_raises_InvalidEqPayLoad_missing_tradstyle3(self):
        party_json = self.party_json.copy()
        del party_json['tradstyle3']

        from app import eq  # NB: local import to avoid overwriting the patched version for some tests

        with aioresponses() as mocked:
            mocked.get(self.collection_instrument_url, payload=self.collection_instrument_json)
            mocked.get(self.collection_exercise_url, payload=self.collection_exercise_json)
            mocked.get(self.collection_exercise_events_url, payload=self.collection_exercise_events_json)
            mocked.get(self.party_url, payload=party_json)

            with self.assertRaises(InvalidEqPayLoad):
                await eq.EqPayloadConstructor(self.case_json, self.app).build()

    @unittest_run_loop
    async def test_build_raises_InvalidEqPayLoad_missing_surveyRef(self):
        survey_json = self.survey_json.copy()
        del survey_json['surveyRef']

        from app import eq  # NB: local import to avoid overwriting the patched version for some tests

        with aioresponses() as mocked:
            mocked.get(self.collection_instrument_url, payload=self.collection_instrument_json)
            mocked.get(self.collection_exercise_url, payload=self.collection_exercise_json)
            mocked.get(self.collection_exercise_events_url, payload=self.collection_exercise_events_json)
            mocked.get(self.party_url, payload=self.party_json)
            mocked.get(self.survey_url, payload=survey_json)

            with self.assertRaises(InvalidEqPayLoad):
                await eq.EqPayloadConstructor(self.case_json, self.app).build()

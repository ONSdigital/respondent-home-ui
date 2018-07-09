import functools
import json
import time
import urllib
import uuid
from unittest import mock

from aiohttp.client_exceptions import ClientConnectorError
from aiohttp.test_utils import AioHTTPTestCase, unittest_run_loop
from aioresponses import aioresponses

from app.app import create_app
from app.eq import format_date
from app.handlers import get_iac
from app.exceptions import InvalidEqPayLoad


def skip_build_eq(func, *args, **kwargs):

    @functools.wraps(func, *args, **kwargs)
    def new_func(self, *inner_args, **inner_kwargs):
        return func(self, *inner_args, **inner_kwargs)

    new_func._skip_eq = True
    return new_func


def skip_encrypt(func, *args, **kwargs):

    @functools.wraps(func, *args, **kwargs)
    def new_func(self, *inner_args, **inner_kwargs):
        return func(self, *inner_args, **inner_kwargs)

    new_func._skip_encrypt = True
    return new_func


class TestGenerateEqURL(AioHTTPTestCase):

    region_code = 'GB-ENG'
    language_code = 'en'

    start_date = '2018-04-10'
    end_date = '2020-05-31'
    return_by = '2018-05-08'

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
            f"{self.app['PARTY_URL']}/party-api/v1/businesses/id/{self.party_id}"
        )
        self.survey_url = (
            f"{self.app['SURVEY_URL']}/surveys/{self.survey_id}"
        )

        self.form_data = {
            'iac1': self.iac1, 'iac2': self.iac2, 'iac3': self.iac3, 'action[save_continue]': '',
        }

    async def _override_eq_payload_constructor(self):
        from app import eq

        async def build(_):
            return self.eq_payload

        eq.EqPayloadConstructor._bk__init__ = eq.EqPayloadConstructor.__init__
        eq.EqPayloadConstructor.__init__ = lambda *args: None
        eq.EqPayloadConstructor._bk_build = eq.EqPayloadConstructor.build
        eq.EqPayloadConstructor.build = build

    async def _override_sdc_encrypt(self):
        from app import handlers

        def encrypt(payload, **_):
            return json.dumps(payload)

        handlers._bk_encrypt = handlers.encrypt
        handlers.encrypt = encrypt

    async def _reset_eq_payload_constructor(self):
        from app import eq

        eq.EqPayloadConstructor.__init__ = eq.EqPayloadConstructor._bk__init__
        eq.EqPayloadConstructor.build = eq.EqPayloadConstructor._bk_build

    async def _reset_sdc_encrypt(self):
        from app import handlers

        handlers.encrypt = handlers._bk_encrypt

    async def setUpAsync(self):
        test_method = getattr(self, self._testMethodName)
        if hasattr(test_method, '_skip_eq'):
            await self._override_eq_payload_constructor()
        if hasattr(test_method, '_skip_encrypt'):
            await self._override_sdc_encrypt()

    async def tearDownAsync(self):
        test_method = getattr(self, self._testMethodName)
        if hasattr(test_method, '_skip_eq'):
            await self._reset_eq_payload_constructor()
        if hasattr(test_method, '_skip_encrypt'):
            await self._reset_sdc_encrypt()

    async def get_application(self):
        return create_app('TestingConfig')

    @unittest_run_loop
    async def test_get_index(self):
        response = await self.client.request("GET", "/")
        self.assertEqual(response.status, 200)

    @skip_build_eq
    @unittest_run_loop
    async def test_post_index(self):
        with aioresponses(passthrough=[str(self.server._root)]) as mocked:
            mocked.get(self.iac_url, payload=self.iac_json)
            mocked.get(self.case_url, payload=self.case_json)
            mocked.post(self.case_events_url)

            response = await self.client.request("POST", "/", allow_redirects=False, data=self.form_data)

        self.assertEqual(response.status, 302)
        self.assertIn(self.app['EQ_URL'], response.headers['location'])

    @unittest_run_loop
    async def test_post_index_with_build_no_mocks(self):
        with aioresponses(passthrough=[str(self.server._root)]) as mocked:
            mocked.get(self.iac_url, payload=self.iac_json)
            mocked.get(self.case_url, payload=self.case_json)
            mocked.post(self.case_events_url)

            response = await self.client.request("POST", "/", allow_redirects=False, data=self.form_data)

        self.assertEqual(response.status, 500)
        self.assertIn(b'500 Internal Server Error', await response.content.read())

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

            response = await self.client.request("POST", "/", allow_redirects=False, data=self.form_data)

        self.assertEqual(response.status, 302)
        redirected_url = response.headers['location']
        self.assertTrue(redirected_url.startswith(self.app['EQ_URL']), redirected_url)  # outputs url on fail
        _, _, _, query, *_ = urllib.parse.urlsplit(redirected_url)  # we only care about the query string
        token = json.loads(urllib.parse.parse_qs(query)['token'][0])  # convert token to dict
        self.assertEqual(self.eq_payload.keys(), token.keys())  # fail early if payload keys differ
        for key in self.eq_payload.keys():
            if key in ['jti', 'tx_id', 'iat', 'exp']:
                continue  # skip uuid / time generated values
            self.assertEqual(self.eq_payload[key], token[key], key)  # outputs failed key as msg

    @unittest_run_loop
    async def test_post_index_caseid_missing(self):
        iac_json = self.iac_json.copy()
        del iac_json['caseId']

        with aioresponses(passthrough=[str(self.server._root)]) as mocked:
            mocked.get(self.iac_url, payload=iac_json)

            response = await self.client.request("POST", "/", allow_redirects=False, data=self.form_data)

        self.assertEqual(response.status, 200)
        self.assertIn(b'Bad response', await response.content.read())

    @unittest_run_loop
    async def test_post_index_malformed(self):
        form_data = self.form_data.copy()
        del form_data['iac3']

        with aioresponses(passthrough=[str(self.server._root)]) as mocked:
            mocked.get(self.iac_url, payload=self.iac_json)

            response = await self.client.request("POST", "/", data=form_data)

        self.assertEqual(response.status, 200)
        self.assertIn(b'Please provide the unique access code', await response.content.read())

    @unittest_run_loop
    async def test_post_index_iac_active_missing(self):
        iac_json = self.iac_json.copy()
        del iac_json['active']

        with aioresponses(passthrough=[str(self.server._root)]) as mocked:

            mocked.get(self.iac_url, payload=iac_json)

            response = await self.client.request("POST", "/", data=self.form_data)

        self.assertEqual(response.status, 200)
        self.assertIn(b'already been used', await response.content.read())

    @unittest_run_loop
    async def test_post_index_iac_inactive(self):
        iac_json = self.iac_json.copy()
        iac_json['active'] = False

        with aioresponses(passthrough=[str(self.server._root)]) as mocked:

            mocked.get(self.iac_url, payload=iac_json)

            response = await self.client.request("POST", "/", data=self.form_data)

        self.assertEqual(response.status, 200)
        self.assertIn(b'already been used', await response.content.read())

    @unittest_run_loop
    async def test_post_index_iac_service_500(self):
        with aioresponses(passthrough=[str(self.server._root)]) as mocked:
            mocked.get(self.iac_url, status=500)

            response = await self.client.request("POST", "/", data=self.form_data)

        self.assertEqual(response.status, 200)
        self.assertIn(b'500 Server Error', await response.content.read())

    @unittest_run_loop
    async def test_post_index_iac_service_503(self):
        with aioresponses(passthrough=[str(self.server._root)]) as mocked:
            mocked.get(self.iac_url, status=503)

            response = await self.client.request("POST", "/", data=self.form_data)

        self.assertEqual(response.status, 200)
        self.assertIn(b'503 Server Error', await response.content.read())

    @unittest_run_loop
    async def test_post_index_iac_service_404(self):
        with aioresponses(passthrough=[str(self.server._root)]) as mocked:
            mocked.get(self.iac_url, status=404)

            response = await self.client.request("POST", "/", data=self.form_data)

        self.assertEqual(response.status, 200)
        self.assertIn(b'Please provide the unique access code', await response.content.read())

    @unittest_run_loop
    async def test_post_index_iac_service_403(self):
        with aioresponses(passthrough=[str(self.server._root)]) as mocked:
            mocked.get(self.iac_url, status=403)

            response = await self.client.request("POST", "/", data=self.form_data)

        self.assertEqual(response.status, 200)
        self.assertIn(b'not authorized', await response.content.read())

    @unittest_run_loop
    async def test_post_index_iac_service_401(self):
        with aioresponses(passthrough=[str(self.server._root)]) as mocked:
            mocked.get(self.iac_url, status=401)

            response = await self.client.request("POST", "/", data=self.form_data)

        self.assertEqual(response.status, 200)
        self.assertIn(b'not authorized', await response.content.read())

    @unittest_run_loop
    async def test_post_index_iac_service_400(self):
        with aioresponses(passthrough=[str(self.server._root)]) as mocked:
            mocked.get(self.iac_url, status=400)

            response = await self.client.request("POST", "/", data=self.form_data)

        self.assertEqual(response.status, 200)
        self.assertIn(b'Bad request', await response.content.read())

    @unittest_run_loop
    async def test_post_index_case_service_500(self):
        with aioresponses(passthrough=[str(self.server._root)]) as mocked:
            mocked.get(self.iac_url, payload=self.iac_json)
            mocked.get(self.case_url, status=500)

            response = await self.client.request("POST", "/", data=self.form_data)

        self.assertEqual(response.status, 200)
        self.assertIn(b'500 Server Error', await response.content.read())

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

    def test_create_eq_constructor(self):
        from app import eq

        self.assertIsInstance(eq.EqPayloadConstructor(self.case_json, self.app), eq.EqPayloadConstructor)

    @unittest_run_loop
    async def test_build_no_mocks(self):
        from app import eq

        with self.assertRaises(ClientConnectorError):
            await eq.EqPayloadConstructor(self.case_json, self.app).build()

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

                payload = await eq.EqPayloadConstructor(self.case_json, self.app).build()

        mocked_uuid4.assert_called()
        mocked_time.assert_called()
        self.assertEqual(payload, self.eq_payload)

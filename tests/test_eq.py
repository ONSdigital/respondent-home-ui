import functools
import time
from uuid import uuid4

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


class TestGenerateEqURL(AioHTTPTestCase):

    action_plan_id = 'e6ce828c-ed94-457e-85a6-bcef784f4160'
    case_id = '8849c299-5014-4637-bd2b-fc866aeccdf5'
    case_group_id = '26d65fa5-c8c3-4cad-bab0-44a52f81ca42'
    case_ref = "1000000000000001"
    collection_exercise_id = '6553d121-df61-4b3a-8f43-e0726666b8cc'
    collection_instrument_id = '724f7d1c-4343-408b-be06-725422a2e223'
    iac_code = '123456789012'
    iac1, iac2, iac3 = iac_code[:4], iac_code[4:8], iac_code[8:]
    iac_json = {'active': '1', 'caseId': case_id}
    party_id = '89e0d37d-1564-4696-9873-abb5b9b4312e'
    case_json = {
        "state": "ACTIONABLE",
        "id": case_id,
        "actionPlanId": action_plan_id,
        "collectionInstrumentId": collection_instrument_id,
        "partyId": party_id,
        "iac": "null",
        "caseRef": case_ref,
        "createdBy": "SYSTEM",
        "sampleUnitType": "B",  # TODO: will this be different for social?
        "createdDateTime": "2018-06-28T08:36:44.904Z",
        "caseGroup": {
            "collectionExerciseId": collection_exercise_id,
            "id": case_group_id,
            "partyId": party_id,
            "sampleUnitRef": "49900000001",
            "sampleUnitType": "B",  # TODO: will this be different for social?
            "caseGroupStatus": "NOTSTARTED"
        },
        "responses": [],
        "caseEvents": "null"
    }
    eq_payload = {
        "jti": str(uuid4()),
        # "tx_id": self._tx_id,
        "user_id": party_id,
        "iat": int(time.time()),
        "exp": int(time.time() + (5 * 60)),
        # "eq_id": self._eq_id,
        # "period_str": self._collex_user_description,
        # "period_id": self._collex_period_id,
        # "form_type": self._form_type,
        "collection_exercise_sid": collection_exercise_id,
        # "ru_ref": self._sample_unit_ref + self._checkletter,
        # "ru_name": self._ru_name,
        # "survey_id": self._survey_ref,
        "case_id": case_id,
        "case_ref": case_ref,
        # "account_service_url": self._account_service_url,
        # "trad_as": self._trading_as,
        # "region_code": self._region_code,
        # "language_code": self._language_code
    }

    async def _override_eq_payload_constructor(self):
        from app import eq

        async def build(s):
            return self.eq_payload

        eq.EqPayloadConstructor._bk__init__ = eq.EqPayloadConstructor.__init__
        eq.EqPayloadConstructor.__init__ = lambda *args: None
        eq.EqPayloadConstructor._bk_build = eq.EqPayloadConstructor.build
        eq.EqPayloadConstructor.build = build

    async def _reset_eq_payload_constructor(self):
        from app import eq

        eq.EqPayloadConstructor.__init__ = eq.EqPayloadConstructor._bk__init__
        eq.EqPayloadConstructor.build = eq.EqPayloadConstructor._bk_build

    async def setUpAsync(self):
        test_method = getattr(self, self._testMethodName)
        if hasattr(test_method, '_skip_eq'):
            await self._override_eq_payload_constructor()

    async def tearDownAsync(self):
        test_method = getattr(self, self._testMethodName)
        if hasattr(test_method, '_skip_eq'):
            await self._reset_eq_payload_constructor()

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
            mocked.get(f"{self.app['IAC_URL']}/iacs/{self.iac_code}", payload=self.iac_json)
            mocked.get(f"{self.app['CASE_URL']}/cases/{self.case_id}", payload=self.case_json)
            mocked.post(f"{self.app['CASE_URL']}/cases/{self.case_id}/events")

            response = await self.client.request("POST", "/", allow_redirects=False, data={
                'iac1': self.iac1, 'iac2': self.iac2, 'iac3': self.iac3, 'action[save_continue]': '',
            })

        self.assertEqual(response.status, 302)
        self.assertIn(self.app['EQ_URL'], response.headers['location'])

    @unittest_run_loop
    async def test_post_index_no_skip(self):
        with aioresponses(passthrough=[str(self.server._root)]) as mocked:
            mocked.get(f"{self.app['IAC_URL']}/iacs/{self.iac_code}", payload=self.iac_json)
            mocked.get(f"{self.app['CASE_URL']}/cases/{self.case_id}", payload=self.case_json)
            mocked.post(f"{self.app['CASE_URL']}/cases/{self.case_id}/events")

            response = await self.client.request("POST", "/", allow_redirects=False, data={
                'iac1': self.iac1, 'iac2': self.iac2, 'iac3': self.iac3, 'action[save_continue]': '',
            })

        self.assertEqual(response.status, 500)

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

import functools
from unittest import mock

from aiohttp.test_utils import unittest_run_loop
from aioresponses import aioresponses

from app.eq import format_date, find_event_date_by_tag
from app.exceptions import InvalidEqPayLoad

from . import RHTestCase


class TestEq(RHTestCase):

    def test_create_eq_constructor(self):
        from app import eq

        self.assertIsInstance(eq.EqPayloadConstructor(self.case_json, self.app), eq.EqPayloadConstructor)

    def test_create_eq_constructor_missing_case_id(self):
        from app import eq

        case_json = self.case_json.copy()
        del case_json['id']

        with self.assertRaises(InvalidEqPayLoad) as ex:
            eq.EqPayloadConstructor(case_json, self.app)
        self.assertIn('No case id in supplied case JSON', ex.exception.message)

    def test_create_eq_constructor_missing_caseRef(self):
        from app import eq

        case_json = self.case_json.copy()
        del case_json['caseRef']

        with self.assertRaises(InvalidEqPayLoad) as ex:
            eq.EqPayloadConstructor(case_json, self.app)
        self.assertIn('No case ref in supplied case JSON', ex.exception.message)

    def test_create_eq_constructor_missing_sample_unit_ref(self):
        from app import eq

        case_json = self.case_json.copy()
        del case_json['caseGroup']['sampleUnitRef']

        with self.assertRaises(InvalidEqPayLoad) as ex:
            eq.EqPayloadConstructor(case_json, self.app)
        self.assertIn(f'Could not retrieve sample unit ref for case {self.case_id}', ex.exception.message)

    def test_create_eq_constructor_missing_ci_id(self):
        from app import eq

        case_json = self.case_json.copy()
        del case_json['collectionInstrumentId']

        with self.assertRaises(InvalidEqPayLoad) as ex:
            eq.EqPayloadConstructor(case_json, self.app)
        self.assertIn(f'No collectionInstrumentId value for case id {self.case_id}', ex.exception.message)

    def test_create_eq_constructor_missing_ce_id(self):
        from app import eq

        case_json = self.case_json.copy()
        del case_json["caseGroup"]["collectionExerciseId"]

        with self.assertRaises(InvalidEqPayLoad) as ex:
            eq.EqPayloadConstructor(case_json, self.app)
        self.assertIn(f'No collection id for case id {self.case_id}', ex.exception.message)

    def test_create_eq_constructor_missing_sample_unit_id(self):
        from app import eq

        case_json = self.case_json.copy()
        del case_json["sampleUnitId"]

        with self.assertRaises(InvalidEqPayLoad) as ex:
            eq.EqPayloadConstructor(case_json, self.app)
        self.assertIn(f'No sample unit id for case {self.case_id}', ex.exception.message)

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
                mocked.get(self.sample_attributes_url, payload=self.sample_attributes_json)
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
    async def test_build_raises_InvalidEqPayLoad_missing_name(self):
        sample_json = self.sample_attributes_json.copy()
        del sample_json['attributes']['Prem1']

        from app import eq  # NB: local import to avoid overwriting the patched version for some tests

        with aioresponses() as mocked:
            mocked.get(self.collection_instrument_url, payload=self.collection_instrument_json)
            mocked.get(self.collection_exercise_url, payload=self.collection_exercise_json)
            mocked.get(self.collection_exercise_events_url, payload=self.collection_exercise_events_json)
            mocked.get(self.sample_attributes_url, payload=sample_json)

            with self.assertRaises(InvalidEqPayLoad):
                await eq.EqPayloadConstructor(self.case_json, self.app).build()

    @unittest_run_loop
    async def test_build_raises_InvalidEqPayLoad_missing_attributes(self):
        sample_json = self.sample_attributes_json.copy()
        del sample_json['attributes']

        from app import eq  # NB: local import to avoid overwriting the patched version for some tests

        with aioresponses() as mocked:
            mocked.get(self.collection_instrument_url, payload=self.collection_instrument_json)
            mocked.get(self.collection_exercise_url, payload=self.collection_exercise_json)
            mocked.get(self.collection_exercise_events_url, payload=self.collection_exercise_events_json)
            mocked.get(self.sample_attributes_url, payload=sample_json)

            with self.assertRaises(InvalidEqPayLoad) as ex:
                await eq.EqPayloadConstructor(self.case_json, self.app).build()
            self.assertIn(f'Could not retrieve attributes for case {self.case_id}', ex.exception.message)

    def test_find_event_date_by_tag(self):
        find_mandatory_date = functools.partial(find_event_date_by_tag,
                                                collex_events=self.collection_exercise_events_json,
                                                collex_id=self.collection_exercise_id,
                                                mandatory=True)
        for tag, expected in [
            ("ref_period_start", self.start_date),
            ("ref_period_end", self.end_date),
            ("return_by", self.return_by)
        ]:
            self.assertEqual(find_mandatory_date(tag), expected)

    def test_find_event_date_by_tag_missing(self):
        result = find_event_date_by_tag("ref_period_start",
                                        [],
                                        self.collection_exercise_id,
                                        False)
        self.assertIsNone(result)

    def test_find_event_date_by_tag_missing_mandatory(self):
        with self.assertRaises(InvalidEqPayLoad) as e:
            find_event_date_by_tag("ref_period_start",
                                   [],
                                   self.collection_exercise_id,
                                   True)
        self.assertIn("ref_period_start", e.exception.message)

    def test_find_event_date_by_tag_unexpected_mandatory(self):
        with self.assertRaises(InvalidEqPayLoad) as e:
            find_event_date_by_tag("unexpected",
                                   self.collection_exercise_events_json,
                                   self.collection_exercise_id,
                                   True)
        self.assertIn("unexpected", e.exception.message)

    def test_camel_to_snake(self):
        from app import eq

        result = eq.EqPayloadConstructor.camel_to_snake('TestCase')
        self.assertEqual(result, 'test_case')

    def test_camel_to_snake_numbers(self):
        from app import eq

        result = eq.EqPayloadConstructor.camel_to_snake('Prem1')
        self.assertEqual(result, 'prem_1')

    def test_camel_to_snake_empty(self):
        from app import eq

        result = eq.EqPayloadConstructor.camel_to_snake('')
        self.assertEqual(result, '')

    def test_build_display_address(self):
        from app import eq

        result = eq.EqPayloadConstructor.build_display_address(self.sample_attributes_json['attributes'])
        self.assertEqual(result, self.eq_payload['display_address'])

    def test_build_display_address_raises(self):
        from app import eq

        attributes = {}

        with self.assertRaises(InvalidEqPayLoad):
            eq.EqPayloadConstructor.build_display_address(attributes)

    def test_build_display_address_prems(self):
        from app import eq

        for attributes, expected in [
            ({
                "Prem1": "A House",
                "Prem2": "",
                "Prem3": "",
                "Prem4": "",
            }, "A House"),
            ({
                 "Prem1": "",
                 "Prem2": "A Second House",
                 "Prem3": "",
                 "Prem4": "",
            }, "A Second House"),
            ({
                 "Prem1": "",
                 "Prem2": "",
                 "Prem3": "A Third House",
                 "Prem4": "",
            }, "A Third House"),
            ({
                 "Prem1": "",
                 "Prem2": "",
                 "Prem3": "",
                 "Prem4": "A Fourth House",
            }, "A Fourth House"),
            ({
                "Prem1": "A House",
                "Prem2": "On The Second Hill",
                "Prem3": "",
                "Prem4": "",
            }, "A House, On The Second Hill"),
            ({
                "Prem1": "A House",
                "Prem2": "",
                "Prem3": "On The Third Hill",
                "Prem4": "",
            }, "A House, On The Third Hill"),
            ({
                "Prem1": "A House",
                "Prem2": "",
                "Prem3": "",
                "Prem4": "On The Fourth Hill",
            }, "A House, On The Fourth Hill"),
            ({
                 "Prem1": "",
                 "Prem2": "A Second House",
                 "Prem3": "On The Third Hill",
                 "Prem4": "",
            }, "A Second House, On The Third Hill"),
            ({
                 "Prem1": "",
                 "Prem2": "A Second House",
                 "Prem3": "",
                 "Prem4": "On The Fourth Hill",
            }, "A Second House, On The Fourth Hill"),
            ({
                 "Prem1": "",
                 "Prem2": "",
                 "Prem3": "A Third House",
                 "Prem4": "On The Fourth Hill",
            }, "A Third House, On The Fourth Hill"),
            ({
                 "Prem1": "A House",
                 "Prem2": "On The Second Hill",
                 "Prem3": "Down The Third Lane",
                 "Prem4": "",
            }, "A House, On The Second Hill"),
            ({
                 "Prem1": "A House",
                 "Prem4": "",
                 "Prem2": "On The Third Hill",
                 "Prem3": "Down The Fourth Lane",
            }, "A House, On The Third Hill"),
            ({
                 "Prem1": "",
                 "Prem2": "A Second House",
                 "Prem3": "On The Third Hill",
                 "Prem4": "Down The Fourth Lane",
             }, "A Second House, On The Third Hill"),
            ({
                 "Prem1": "",
                 "Prem2": "",
                 "Prem3": "",
                 "Prem4": "Another House",
                 "District": "",
                 "PostTown": "",
                 "Postcode": "AA1 2BB"
             }, "Another House, AA1 2BB"),
            ({
                 "Prem1": "",
                 "Prem2": "",
                 "Prem3": "",
                 "Prem4": "Another House",
                 "District": "",
                 "PostTown": "In Brizzle",
                 "Postcode": ""
             }, "Another House, In Brizzle"),
            ({
                 "Prem1": "",
                 "Prem2": "",
                 "Prem3": "",
                 "Prem4": "Another House",
                 "District": "In The Shire",
                 "PostTown": "",
                 "Postcode": ""
             }, "Another House, In The Shire"),
        ]:
            self.assertEqual(eq.EqPayloadConstructor.build_display_address(attributes), expected)

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

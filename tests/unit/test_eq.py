import functools
from unittest import mock

from aiohttp.test_utils import unittest_run_loop
from aioresponses import aioresponses

from app.eq import EqPayloadConstructor, build_response_id, format_date, parse_date
from app.exceptions import ExerciseClosedError, InvalidEqPayLoad

from . import RHTestCase


class TestEq(RHTestCase):

    def test_create_eq_constructor(self):
        self.assertIsInstance(EqPayloadConstructor(self.case_json, self.app, self.iac_code), EqPayloadConstructor)

    def test_create_eq_constructor_missing_iac(self):
        iac_code = ''

        with self.assertRaises(InvalidEqPayLoad) as ex:
            EqPayloadConstructor(self.case_json, self.app, iac_code)
        self.assertIn('IAC is empty', ex.exception.message)

    def test_create_eq_constructor_missing_case_id(self):
        case_json = self.case_json.copy()
        del case_json['id']

        with self.assertRaises(InvalidEqPayLoad) as ex:
            EqPayloadConstructor(case_json, self.app, self.iac_code)
        self.assertIn('No case id in supplied case JSON', ex.exception.message)

    def test_create_eq_constructor_missing_case_ref(self):
        case_json = self.case_json.copy()
        del case_json['caseRef']

        with self.assertRaises(InvalidEqPayLoad) as ex:
            EqPayloadConstructor(case_json, self.app, self.iac_code)
        self.assertIn('No case ref in supplied case JSON', ex.exception.message)

    def test_create_eq_constructor_missing_sample_unit_ref(self):
        case_json = self.case_json.copy()
        del case_json['caseGroup']['sampleUnitRef']

        with self.assertRaises(InvalidEqPayLoad) as ex:
            EqPayloadConstructor(case_json, self.app, self.iac_code)
        self.assertIn(f'Could not retrieve sample unit ref for case {self.case_id}', ex.exception.message)

    def test_create_eq_constructor_missing_ci_id(self):
        case_json = self.case_json.copy()
        del case_json['collectionInstrumentId']

        with self.assertRaises(InvalidEqPayLoad) as ex:
            EqPayloadConstructor(case_json, self.app, self.iac_code)
        self.assertIn(f'No collectionInstrumentId value for case id {self.case_id}', ex.exception.message)

    def test_create_eq_constructor_missing_ce_id(self):
        case_json = self.case_json.copy()
        del case_json["caseGroup"]["collectionExerciseId"]

        with self.assertRaises(InvalidEqPayLoad) as ex:
            EqPayloadConstructor(case_json, self.app, self.iac_code)
        self.assertIn(f'No collection id for case id {self.case_id}', ex.exception.message)

    def test_create_eq_constructor_missing_sample_unit_id(self):
        case_json = self.case_json.copy()
        del case_json["sampleUnitId"]

        with self.assertRaises(InvalidEqPayLoad) as ex:
            EqPayloadConstructor(case_json, self.app, self.iac_code)
        self.assertIn(f'No sample unit id for case {self.case_id}', ex.exception.message)

    @unittest_run_loop
    async def test_build(self):
        self.maxDiff = None  # for full payload comparison when running this test
        with mock.patch('app.eq.uuid4') as mocked_uuid4, mock.patch('app.eq.time.time') as mocked_time:
            # NB: has to be mocked after setup but before import
            mocked_time.return_value = self.eq_payload['iat']
            mocked_uuid4.return_value = self.jti

            with aioresponses() as mocked:
                mocked.get(self.collection_instrument_url, payload=self.collection_instrument_json)
                mocked.get(self.collection_exercise_url, payload=self.collection_exercise_json)
                mocked.get(self.collection_exercise_events_url, payload=self.collection_exercise_events_json)
                mocked.get(self.sample_attributes_url, payload=self.sample_attributes_json)
                mocked.get(self.survey_url, payload=self.survey_json)

                with self.assertLogs('app.eq', 'INFO') as cm:
                    payload = await EqPayloadConstructor(self.case_json, self.app, self.iac_code).build()
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

            with self.assertRaises(InvalidEqPayLoad) as ex:
                await eq.EqPayloadConstructor(self.case_json, self.app, self.iac_code).build()
            self.assertIn(f"Collection instrument {self.collection_instrument_id} type is not EQ", ex.exception.message)

    @unittest_run_loop
    async def test_build_raises_InvalidEqPayLoad_missing_ci_type(self):
        ci_json = self.collection_instrument_json.copy()
        del ci_json['type']

        with aioresponses() as mocked:
            mocked.get(self.collection_instrument_url, payload=ci_json)

            with self.assertRaises(InvalidEqPayLoad) as ex:
                await EqPayloadConstructor(self.case_json, self.app, self.iac_code).build()
            self.assertIn(f"No Collection Instrument type for {self.collection_instrument_id}", ex.exception.message)

    @unittest_run_loop
    async def test_build_raises_InvalidEqPayLoad_missing_classifiers(self):
        ci_json = self.collection_instrument_json.copy()
        del ci_json['classifiers']

        with aioresponses() as mocked:
            mocked.get(self.collection_instrument_url, payload=ci_json)

            with self.assertRaises(InvalidEqPayLoad) as ex:
                await EqPayloadConstructor(self.case_json, self.app, self.iac_code).build()
            self.assertIn(f"Could not retrieve classifiers for case {self.case_id}", ex.exception.message)

    @unittest_run_loop
    async def test_build_raises_InvalidEqPayLoad_missing_eq_id(self):
        ci_json = self.collection_instrument_json.copy()
        del ci_json['classifiers']['eq_id']

        with aioresponses() as mocked:
            mocked.get(self.collection_instrument_url, payload=ci_json)

            with self.assertRaises(InvalidEqPayLoad) as ex:
                await EqPayloadConstructor(self.case_json, self.app, self.iac_code).build()
            self.assertIn(f"Could not retrieve eq_id for case {self.case_id}", ex.exception.message)

    @unittest_run_loop
    async def test_build_raises_InvalidEqPayLoad_missing_form_type(self):
        ci_json = self.collection_instrument_json.copy()
        del ci_json['classifiers']['form_type']

        with aioresponses() as mocked:
            mocked.get(self.collection_instrument_url, payload=ci_json)

            with self.assertRaises(InvalidEqPayLoad) as ex:
                await EqPayloadConstructor(self.case_json, self.app, self.iac_code).build()
            self.assertIn(f"Could not retrieve form_type for eq_id {self.eq_id}", ex.exception.message)

    @unittest_run_loop
    async def test_build_raises_InvalidEqPayLoad_missing_exerciseRef(self):
        ce_json = self.collection_exercise_json.copy()
        del ce_json['exerciseRef']

        with aioresponses() as mocked:
            mocked.get(self.collection_instrument_url, payload=self.collection_instrument_json)
            mocked.get(self.collection_exercise_url, payload=ce_json)

            with self.assertRaises(InvalidEqPayLoad) as ex:
                await EqPayloadConstructor(self.case_json, self.app, self.iac_code).build()
            self.assertIn(f"Could not retrieve period id for case {self.case_id}", ex.exception.message)

    @unittest_run_loop
    async def test_build_raises_InvalidEqPayLoad_missing_exercise_id(self):
        ce_json = self.collection_exercise_json.copy()
        del ce_json['id']

        with aioresponses() as mocked:
            mocked.get(self.collection_instrument_url, payload=self.collection_instrument_json)
            mocked.get(self.collection_exercise_url, payload=ce_json)

            with self.assertRaises(InvalidEqPayLoad) as ex:
                await EqPayloadConstructor(self.case_json, self.app, self.iac_code).build()
            self.assertIn(f"Could not retrieve ce id for case {self.case_id}", ex.exception.message)

    @unittest_run_loop
    async def test_build_raises_InvalidEqPayLoad_missing_country_code(self):
        sample_json = self.sample_attributes_json.copy()
        del sample_json['attributes']['COUNTRY']

        with aioresponses() as mocked:
            mocked.get(self.collection_instrument_url, payload=self.collection_instrument_json)
            mocked.get(self.collection_exercise_url, payload=self.collection_exercise_json)
            mocked.get(self.collection_exercise_events_url, payload=self.collection_exercise_events_json)
            mocked.get(self.sample_attributes_url, payload=sample_json)

            with self.assertRaises(InvalidEqPayLoad) as ex:
                await EqPayloadConstructor(self.case_json, self.app, self.iac_code).build()
            self.assertIn(f"Could not retrieve country_code for case {self.case_id}", ex.exception.message)

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
                await eq.EqPayloadConstructor(self.case_json, self.app, self.iac_code).build()
            self.assertIn(f'Could not retrieve attributes for case {self.case_id}', ex.exception.message)

    def test_find_event_date_by_tag(self):
        find_mandatory_date = functools.partial(EqPayloadConstructor._find_event_date_by_tag, mandatory=True)

        for tag, expected in [
            ("ref_period_start", self.start_date),
            ("ref_period_end", self.end_date),
            ("return_by", self.return_by)
        ]:
            self.assertEqual(find_mandatory_date(self.dummy_eq, tag), expected)

    def test_find_event_date_by_tag_missing(self):
        self.dummy_eq._collex_events = []
        result = EqPayloadConstructor._find_event_date_by_tag(self.dummy_eq, "ref_period_start", False)
        self.assertIsNone(result)

    def test_find_event_date_by_tag_missing_mandatory(self):
        self.dummy_eq._collex_events = []
        with self.assertRaises(InvalidEqPayLoad) as e:
            EqPayloadConstructor._find_event_date_by_tag(self.dummy_eq, "ref_period_start", True)
        self.assertIn("ref_period_start", e.exception.message)

    def test_find_event_date_by_tag_unexpected_mandatory(self):
        with self.assertRaises(InvalidEqPayLoad) as e:
            EqPayloadConstructor._find_event_date_by_tag(self.dummy_eq, "unexpected", True)
        self.assertIn("unexpected", e.exception.message)

    def test_caps_to_snake(self):
        from app import eq

        result = eq.EqPayloadConstructor.caps_to_snake('TEST_CASE')
        self.assertEqual(result, 'test_case')

    def test_caps_to_snake_numbers(self):
        from app import eq

        result = eq.EqPayloadConstructor.caps_to_snake('ADDRESS_LINE1')
        self.assertEqual(result, 'address_line1')

    def test_caps_to_snake_empty(self):
        from app import eq

        result = eq.EqPayloadConstructor.caps_to_snake('')
        self.assertEqual(result, '')

    def test_build_display_address(self):
        from app import eq

        result = eq.EqPayloadConstructor.build_display_address(self.sample_attributes_json['attributes'])
        self.assertEqual(result, self.eq_payload['display_address'])

    def test_build_display_address_raises(self):
        from app import eq

        attributes = {}

        with self.assertRaises(InvalidEqPayLoad) as ex:
            eq.EqPayloadConstructor.build_display_address(attributes)
            self.assertIn("Displayable address not in sample attributes", ex.exception.message)

    def test_build_display_address_prems(self):
        from app import eq

        for attributes, expected in [
            ({
                 "ADDRESS_LINE1": "A House",
                 "ADDRESS_LINE2": "",
             }, "A House"),
            ({
                 "ADDRESS_LINE1": "",
                 "ADDRESS_LINE2": "A Second House",
             }, "A Second House"),
            ({
                 "ADDRESS_LINE1": "A House",
                 "ADDRESS_LINE2": "On The Second Hill",
             }, "A House, On The Second Hill"),
            ({
                 "ADDRESS_LINE1": "Another House",
                 "ADDRESS_LINE2": "",
                 "LOCALITY": "",
                 "TOWN_NAME": "",
                 "POSTCODE": "AA1 2BB"
             }, "Another House, AA1 2BB"),
            ({
                 "ADDRESS_LINE1": "Another House",
                 "ADDRESS_LINE2": "",
                 "LOCALITY": "",
                 "TOWN_NAME": "In Brizzle",
                 "POSTCODE": ""
             }, "Another House, In Brizzle"),
            ({
                 "ADDRESS_LINE1": "Another House",
                 "ADDRESS_LINE2": "",
                 "LOCALITY": "In The Shire",
                 "TOWN_NAME": "",
                 "POSTCODE": ""
             }, "Another House, In The Shire"),
        ]:
            self.assertEqual(eq.EqPayloadConstructor.build_display_address(attributes), expected)

    def test_correct_iso8601_date_format(self):
        # Given a valid date
        date = '2007-01-25T12:00:00Z'

        # When format_date is called
        result = format_date(parse_date(date))

        # Then the date is formatted correctly
        self.assertEqual(result, '2007-01-25')

    def test_iso8601_adjusts_to_local_time(self):
        # Given a valid date in tz -1hr before midnight
        date = '2007-01-25T23:59:59-0100'

        # When format_date is called
        result = format_date(parse_date(date))

        # Then the date is localised to the next day
        self.assertEqual(result, '2007-01-26')

    def test_invalid_iso8601_date_format(self):
        # Given a valid date
        date = 'invalid_date'

        # When parse_date is called
        with self.assertRaises(InvalidEqPayLoad) as e:
            parse_date(date)

        # Then the date is formatted correctly
        self.assertEqual(e.exception.message, 'Unable to parse invalid_date')

    def test_incorrect_date_format(self):
        # Given an invalid date
        date = 'invalid_date'

        # When format_date is called
        with self.assertRaises(InvalidEqPayLoad) as e:
            format_date(date)

        # Then an InvalidEqPayLoad is raised
        self.assertEqual(e.exception.message, 'Unable to format invalid_date')

    def test_check_ce_has_ended(self):
        # Given a valid date
        datetime_obj = parse_date('2007-01-25T12:00:00Z')

        # When check_ce_has_ended is called
        with self.assertRaises(ExerciseClosedError):
            EqPayloadConstructor._check_ce_has_ended(self.dummy_eq, datetime_obj)

        # Then an ExerciseEndError is raised

    def test_check_ce_has_not_ended(self):
        # Given a valid date
        datetime_obj = parse_date('2027-01-25T12:00:00Z')

        # When check_ce_has_ended is called
        self.assertIsNone(EqPayloadConstructor._check_ce_has_ended(self.dummy_eq, datetime_obj))

        # Then an ExerciseEndError is not raised

    def test_check_ce_has_ended_error(self):
        # Given an invalid date
        datetime_obj = 'invalid_date'

        # When check_ce_has_ended is called
        with self.assertRaises(InvalidEqPayLoad) as e:
            EqPayloadConstructor._check_ce_has_ended(self.dummy_eq, datetime_obj)

        # Then an InvalidEqPayload is raised
        self.assertEqual(e.exception.message, 'Unable to compare date objects')

    def test_build_response_id(self):
        response_id = build_response_id(self.case_id, self.collection_exercise_id, self.iac_code)

        self.assertEqual(response_id, self.eq_payload['response_id'])

    def test_build_response_id_is_unique_by_iac(self):
        different_iac = 'A' * 12

        response_id = build_response_id(self.case_id, self.collection_exercise_id, self.iac_code)
        different_response_id = build_response_id(self.case_id, self.collection_exercise_id, different_iac)

        self.assertNotEqual(different_response_id, response_id)

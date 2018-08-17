import json
import time
import uuid

from aiohttp import web
from aioresponses import aioresponses

from app.app import create_app


class DemoRunner:

    language_code = 'en'

    start_date = '2018-04-10'
    end_date = '2020-05-31'
    return_by = '2018-05-08'

    def __init__(self):
        with open('tests/test_data/case/case.json') as fp:
            self.case_json = json.load(fp)
        with open('tests/test_data/collection_exercise/collection_exercise.json') as fp:
            self.collection_exercise_json = json.load(fp)
        with open('tests/test_data/collection_exercise/collection_exercise_events.json') as fp:
            self.collection_exercise_events_json = json.load(fp)
        with open('tests/test_data/collection_instrument/collection_instrument_eq.json') as fp:
            self.collection_instrument_json = json.load(fp)
        with open('tests/test_data/sample/sample_attributes.json') as fp:
            self.sample_attributes_json = json.load(fp)
        with open('tests/test_data/survey/survey.json') as fp:
            self.survey_json = json.load(fp)

        self.app = create_app('TestingConfig')

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
        self.ru_name = self.sample_attributes_json['attributes']['ADDRESS_LINE1']
        self.sample_unit_id = self.sample_attributes_json['id']
        self.sample_unit_ref = self.case_json['caseGroup']['sampleUnitRef']
        self.sample_unit_type = self.case_json['sampleUnitType']
        self.survey_id = self.survey_json['id']
        self.survey_ref = self.survey_json['surveyRef']
        self.eq_payload = {
            "jti": self.jti,
            "tx_id": self.jti,
            "user_id": self.sample_unit_id,
            "iat": int(time.time()),
            "exp": int(time.time() + (5 * 60)),
            "eq_id": self.eq_id,
            "period_id": self.collection_exercise_ref,
            "form_type": self.form_type,
            "collection_exercise_sid": self.collection_exercise_id,
            "ru_ref": self.sample_unit_ref,
            "ru_name": self.ru_name,
            "case_id": self.case_id,
            "case_ref": self.case_ref,
            "account_service_url": self.app['ACCOUNT_SERVICE_URL'],
            "country_code": self.sample_attributes_json['attributes']['CountryCode'],
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
        self.sample_attributes_url = (
            f"{self.app['SAMPLE_URL']}/samples/{self.sample_unit_id}/attributes"
        )
        self.survey_url = (
            f"{self.app['SURVEY_URL']}/surveys/{self.survey_id}"
        )

    def run(self):
        with aioresponses(passthrough=[]) as mocked:
            for _ in range(3):
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

            web.run_app(self.app, port=self.app['PORT'])

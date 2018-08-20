import logging
import time
import re
from collections import namedtuple
from uuid import uuid4

import iso8601
from aiohttp.web import Application
from aiohttp import ClientError
from structlog import wrap_logger

from .exceptions import InvalidEqPayLoad


logger = wrap_logger(logging.getLogger(__name__))

Request = namedtuple("Request", ["method", "path", "auth", "func"])


def handle_response(response):
    try:
        response.raise_for_status()
    except ClientError as ex:
        logger.error("Error in response", url=str(response.url), status_code=response.status)
        raise ex
    else:
        logger.debug("Successfully connected to service", url=str(response.url))


def find_event_date_by_tag(search_param: str, collex_events: dict, collex_id: str, mandatory: bool):
    for event in collex_events:
        if event["tag"] == search_param and event.get("timestamp"):
            return format_date(event["timestamp"])

    if mandatory:
        raise InvalidEqPayLoad(
            f"Mandatory event not found for collection {collex_id} for search param {search_param}"
        )


def format_date(string_date):
    """
    Formats the date from a string to %Y-%m-%d eg 2018-01-20
    :param string_date: The date string
    :return formatted date
    """

    try:
        return iso8601.parse_date(string_date).strftime("%Y-%m-%d")
    except (ValueError, iso8601.iso8601.ParseError):
        raise InvalidEqPayLoad(f"Unable to format {string_date}")


class EqPayloadConstructor(object):

    def __init__(self, case: dict, app: Application):
        """
        Creates the payload needed to communicate with EQ, built from the Case, Collection Exercise, Sample,
        and Collection Instrument services
        """

        self._app = app
        self._ci_url = f"{app['COLLECTION_INSTRUMENT_URL']}/collection-instrument-api/1.0.2/collectioninstrument/id/"
        self._collex_url = f"{app['COLLECTION_EXERCISE_URL']}/collectionexercises/"
        self._sample_url = f"{app['SAMPLE_URL']}/samples/"

        self._tx_id = str(uuid4())
        self._account_service_url = app["ACCOUNT_SERVICE_URL"]

        try:
            self._case_id = case["id"]
        except KeyError:
            raise InvalidEqPayLoad("No case id in supplied case JSON")

        try:
            self._case_ref = case["caseRef"]
        except KeyError:
            raise InvalidEqPayLoad(f"No case ref in supplied case JSON")

        try:
            self._sample_unit_ref = case["caseGroup"]["sampleUnitRef"]
        except KeyError:
            raise InvalidEqPayLoad(f"Could not retrieve sample unit ref for case {self._case_id}")

        logger.info("Creating payload for JWT", case_id=self._case_id, tx_id=self._tx_id)

        try:
            self._ci_id = case["collectionInstrumentId"]
        except KeyError:
            raise InvalidEqPayLoad(f"No collectionInstrumentId value for case id {self._case_id}")

        try:
            self._collex_id = case["caseGroup"]["collectionExerciseId"]
        except KeyError:
            raise InvalidEqPayLoad(f"No collection id for case id {self._case_id}")

        try:
            self._sample_unit_id = case["sampleUnitId"]
        except KeyError:
            raise InvalidEqPayLoad(f"No sample unit id for case {self._case_id}")

    async def build(self):
        """__init__ is not a coroutine function, so I/O needs to go here"""
        self._ci = await self._get_collection_instrument()

        try:
            if self._ci["type"] != "EQ":
                raise InvalidEqPayLoad(f"Collection instrument {self._ci_id} type is not EQ")
        except KeyError:
            raise InvalidEqPayLoad(f"No Collection Instrument type for {self._ci_id}")

        try:
            self._ci["classifiers"]
        except KeyError:
            raise InvalidEqPayLoad(f"Could not retrieve classifiers for case {self._case_id}")

        try:
            self._eq_id = self._ci["classifiers"]["eq_id"]
        except KeyError:
            raise InvalidEqPayLoad(f"Could not retrieve eq_id for case {self._case_id}")

        try:
            self._form_type = self._ci["classifiers"]["form_type"]
        except KeyError:
            raise InvalidEqPayLoad(f"Could not retrieve form_type for eq_id {self._eq_id}")

        self._collex = await self._get_collection_exercise()

        try:
            self._collex_period_id = self._collex["exerciseRef"]
        except KeyError:
            raise InvalidEqPayLoad(f"Could not retrieve period id for case {self._case_id}")

        try:
            self._collex_id = self._collex["id"]
        except KeyError:
            raise InvalidEqPayLoad(f"Could not retrieve ce id for case {self._case_id}")

        self._collex_events = await self._get_collection_exercise_events()
        self._collex_event_dates = self._get_collex_event_dates()
        self._sample_attributes = await self._get_sample_attributes_by_id()

        try:
            self._sample_attributes = self._sample_attributes["attributes"]
        except KeyError:
            raise InvalidEqPayLoad(f"Could not retrieve attributes for case {self._case_id}")

        try:
            self._ru_name = self._sample_attributes["ADDRESS_LINE1"]
        except KeyError:
            raise InvalidEqPayLoad(f"Could not retrieve ru_name (address) for case {self._case_id}")

        try:
            self._country_code = self._sample_attributes["COUNTRY"]
        except KeyError:
            raise InvalidEqPayLoad(f"Could not retrieve country_code for case {self._case_id}")

        # TODO: Remove hardcoded language variables for payload when they become available in RAS/RM
        self._language_code = 'en'  # sample attributes do not currently have language details

        self._payload = {
            "jti": str(uuid4()),  # required by eQ for creating a new claim
            "tx_id": self._tx_id,  # not required by eQ (will generate if does not exist)
            "user_id": self._sample_unit_id,  # required by eQ
            "iat": int(time.time()),
            "exp": int(time.time() + (5 * 60)),  # required by eQ for creating a new claim
            "eq_id": self._eq_id,  # required but currently only one social survey ('lms')
            "period_id": self._collex_period_id,  # required by eQ
            "form_type": self._form_type,  # required but only one ('1') formtype for lms
            "collection_exercise_sid": self._collex_id,  # required by eQ
            "ru_ref": self._sample_unit_ref,  # required by eQ
            "ru_name": self._ru_name,  # required by eQ - household identifier (address)
            "case_id": self._case_id,  # not required by eQ but useful for downstream
            "case_ref": self._case_ref,  # not required by eQ but useful for downstream
            "account_service_url": self._account_service_url,  # required for save/continue
            "country_code": self._country_code,
            "language_code": self._language_code,  # currently only 'en' or 'cy'
            "display_address": self.build_display_address(self._sample_attributes),  # built from the Prem attributes
        }

        # Add all of the sample attributes to the payload as camel case fields
        self._payload.update(
            [(self.caps_to_snake(key), value) for key, value in self._sample_attributes.items()]
        )

        # Add any non null event dates that exist for this collection exercise
        # NB: for LMS the event dates are optional
        self._payload.update(
            [(key, value) for key, value in self._collex_event_dates.items() if value is not None]
        )

        logger.info(payload=self._payload)

        return self._payload

    @staticmethod
    def caps_to_snake(s):
        return s.lower().lstrip('_')

    @staticmethod
    def build_display_address(sample_attributes):
        """
        Build `display_address` value by appending not-None (in order) values of sample attributes

        :param sample_attributes: dictionary of address attributes
        :return: string of a single address attribute or a combination of two
        """
        display_address = ''
        for prem_key in ['ADDRESS_LINE1', 'ADDRESS_LINE2', 'LOCALITY', 'TOWN_NAME', 'POSTCODE']:  # retain order of address attributes
            val = sample_attributes.get(prem_key)
            if val:
                prev_display = display_address
                display_address = f'{prev_display}, {val}' if prev_display else val
                if prev_display:
                    break  # break once two address attributes have been added
        if not display_address:
            raise InvalidEqPayLoad("Displayable address not in sample attributes")
        return display_address

    async def _make_request(self, request: Request):
        method, url, auth, func = request
        logger.info(f"Making {method} request to {url} and handling with {func.__name__}")
        async with self._app.http_session_pool.request(method, url, auth=auth) as resp:
            func(resp)
            return await resp.json()

    async def _get_sample_attributes_by_id(self):
        url = self._sample_url + self._sample_unit_id + "/attributes"
        return await self._make_request(Request("GET", url, self._app['SAMPLE_AUTH'], handle_response))

    async def _get_collection_instrument(self):
        url = self._ci_url + self._ci_id
        return await self._make_request(Request("GET", url, self._app['COLLECTION_INSTRUMENT_AUTH'], handle_response))

    async def _get_collection_exercise(self):
        url = self._collex_url + self._collex_id
        return await self._make_request(Request("GET", url, self._app['COLLECTION_EXERCISE_AUTH'], handle_response))

    async def _get_collection_exercise_events(self):
        url = self._collex_url + self._collex_id + "/events"
        return await self._make_request(Request("GET", url, self._app['COLLECTION_EXERCISE_AUTH'], handle_response))

    def _get_collex_event_dates(self):
        return {
            "ref_p_start_date": find_event_date_by_tag(
                "ref_period_start", self._collex_events, self._collex_id, False
            ),
            "ref_p_end_date": find_event_date_by_tag(
                "ref_period_end", self._collex_events, self._collex_id, False
            ),
            "return_by": find_event_date_by_tag(
                "return_by", self._collex_events, self._collex_id, False
            ),
        }

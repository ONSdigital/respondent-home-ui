import time
import sys
import os

import requests
from sdc.crypto.encrypter import encrypt
from uuid import uuid4

sys.path.append(os.path.join(os.path.dirname(__file__), os.path.pardir))  # NB: script needs to know about app so append to PYTHONPATH

from app import config, jwt  # NOQA
from app.eq import build_response_id  # NOQA


try:
    config_info = getattr(config, os.environ['APP_SETTINGS'])
except (AttributeError, KeyError) as e:
    config_info = config.DevelopmentConfig

# Put config into a dict
config = dict((name, getattr(config_info, name)) for name in dir(config_info) if not name.startswith('__'))

# Setup URLs
case_url = f"{config['CASE_URL']}/cases/"
ci_url = f"{config['COLLECTION_INSTRUMENT_URL']}/collection-instrument-api/1.0.2/collectioninstrument/id/"
collex_url = f"{config['COLLECTION_EXERCISE_URL']}/collectionexercises/"
sample_url = f"{config['SAMPLE_URL']}/samples/"
eq_url = f"{config['EQ_URL']}"


def main(collection_ex_id):
    collection_ex_info = requests.get(collex_url + "link/" + collection_ex_id[0],
                                      auth=config["COLLECTION_EXERCISE_AUTH"])
    collection_ex_info.raise_for_status()

    sample_summary_id = collection_ex_info.json()

    sample_units = requests.get(sample_url + sample_summary_id[0] + "/sampleunits",
                                auth=config["SAMPLE_AUTH"])
    sample_units = sample_units.json()

    samples = [sample['id'] for sample in sample_units]

    case_inprogress = []
    for sample in samples:
        sample_return = requests.get(case_url + "?sampleUnitId=" + sample, auth=config["CASE_AUTH"])
        sample_return.raise_for_status()
        case_return = sample_return.json()
        case_return = case_return[0]
        if case_return["caseGroup"]["collectionExerciseId"] == str(collection_ex[0]) and case_return["caseGroup"][
            "caseGroupStatus"] == "INPROGRESS":
            case_inprogress.append(case_return)

    # Loop over cases to flush them away
    for case in case_inprogress:
        print("Flushing case: " + case["id"])
        flush_cases(case["id"])


def flush_cases(case_id):
    # Get iac for case
    iac_return = requests.get(case_url + case_id + "/iac", auth=config["CASE_AUTH"])
    iac_return.raise_for_status()
    iac_return = iac_return.json()

    # Get case details
    case_return = requests.get(case_url + case_id, auth=config["CASE_AUTH"])
    case_return.raise_for_status()
    case = case_return.json()

    # Collection instrument details
    ci_return = requests.get(ci_url + case["collectionInstrumentId"], auth=config["COLLECTION_INSTRUMENT_AUTH"])
    ci_return.raise_for_status()
    ci = ci_return.json()

    # Get collection exercise info
    collex_return = requests.get(collex_url + case["caseGroup"]["collectionExerciseId"],
                                 auth=config["COLLECTION_EXERCISE_AUTH"])
    collex_return.raise_for_status()
    collex = collex_return.json()

    # Get sample details
    sample_return = requests.get(sample_url + case["sampleUnitId"] + "/attributes",
                                 auth=config["SAMPLE_AUTH"])
    sample_return.raise_for_status()
    sample = sample_return.json()
    sample_attributes = sample["attributes"]

    # For each IAC that is returned for a case
    for iac in iac_return:
        # Put together the payload
        flush_payload = {
            "jti": str(uuid4()),  # required by eQ for creating a new claim
            "tx_id": str(uuid4()),  # not required by eQ (will generate if does not exist)
            "user_id": case["sampleUnitId"],  # required by eQ
            "iat": int(time.time()),
            "exp": int(time.time() + (5 * 60)),  # required by eQ for creating a new claim
            "eq_id": ci["classifiers"]["eq_id"],  # required but currently only one social survey ('lms')
            "period_id": collex["exerciseRef"],  # required by eQ
            "form_type": ci["classifiers"]["form_type"],  # required by eQ ('2' for lms_2 schema)
            "collection_exercise_sid": collex["id"],  # required by eQ
            "ru_ref": case["caseGroup"]["sampleUnitRef"],  # required by eQ
            "case_id": case["id"],  # not required by eQ but useful for downstream
            "case_ref": case["caseRef"],  # not required by eQ but useful for downstream
            "account_service_url": f'{config["ACCOUNT_SERVICE_URL"]}{config["URL_PATH_PREFIX"]}',
            # required for save/continue
            "country_code": sample_attributes["COUNTRY"],
            "language_code": "en",  # currently only 'en' or 'cy'
            "response_id": build_response_id(case["id"], collex["id"], iac["iac"]),
            "roles": "flusher"
        }

        # Get encryption key stuff
        config["key_store"] = jwt.key_store(config["JSON_SECRET_KEYS"])

        # Encrypt payload into token
        token = encrypt(flush_payload, key_store=config['key_store'], key_purpose="authentication")

        # Call flusher
        flush_url = eq_url + "/flush?token=" + token
        requests.post(flush_url)


if __name__ == '__main__':
    collection_ex = sys.argv[1:]
    print("Collection exercise: " + str(collection_ex))
    main(collection_ex)

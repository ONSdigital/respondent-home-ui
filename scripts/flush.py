import requests
import json
import time
import sys
import os
import pprint

sys.path.append(os.getcwd())

from app.config import DevelopmentConfig
from requests.auth import HTTPBasicAuth
from uuid import uuid4
from app.eq import build_response_id
from sdc.crypto.encrypter import encrypt
from app import jwt
from app.exceptions import InvalidEqPayLoad

collection_ex = sys.argv[1:]
print("Collection Exercise: " + collection_ex[0])

# Couldn't access this from eq.py, although maybe not necessary
def build_display_address(sample_attributes):
    """
    Build `display_address` value by appending not-None (in order) values of sample attributes

    :param sample_attributes: dictionary of address attributes
    :return: string of a single address attribute or a combination of two
    """
    display_address = ''
    for key in ['ADDRESS_LINE1', 'ADDRESS_LINE2', 'LOCALITY', 'TOWN_NAME',
                'POSTCODE']:  # retain order of address attributes
        val = sample_attributes.get(key)
        if val:
            prev_display = display_address
            display_address = f'{prev_display}, {val}' if prev_display else val
            if prev_display:
                break  # break once two address attributes have been added
    if not display_address:
        raise InvalidEqPayLoad("Displayable address not in sample attributes")
    return display_address


# Get dev config
dev = DevelopmentConfig()

# Put config into a dict
app_config = dict((name, getattr(dev, name)) for name in dir(dev) if not name.startswith('__'))

# Setup URLs
case_url = f"{app_config['CASE_URL']}/cases/"
ci_url = f"{app_config['COLLECTION_INSTRUMENT_URL']}/collection-instrument-api/1.0.2/collectioninstrument/id/"
collex_url = f"{app_config['COLLECTION_EXERCISE_URL']}/collectionexercises/"
sample_url = f"{app_config['SAMPLE_URL']}/samples/"
eq_url = f"{app_config['EQ_URL']}"

collection_ex_info = requests.get(collex_url + "link/" + collection_ex[0], auth=HTTPBasicAuth('admin', 'secret'))
sample_summary_id = json.loads(collection_ex_info.content)

sample_units = requests.get(sample_url + sample_summary_id[0] + "/sampleunits", auth=HTTPBasicAuth('admin', 'secret'))
sample_units = json.loads(sample_units.content)

samples = []
for sample in sample_units:
    samples.append(sample["id"])

case_inprogress = []
for sample in samples:
    sample_return = requests.get(case_url + "?sampleUnitId=" + sample, auth=HTTPBasicAuth('admin', 'secret'))
    case_return = json.loads(sample_return.content)
    case_return = case_return[0]
    if case_return["caseGroup"]["collectionExerciseId"] == str(collection_ex[0]) and case_return["caseGroup"][
        "caseGroupStatus"] == "INPROGRESS":
        case_inprogress.append(case_return)

pprint.pprint(case_inprogress)

def flush_cases(case_id):
    # Get iac for case
    iac_return = requests.get(case_url + case_id + "/iac", auth=HTTPBasicAuth('admin', 'secret'))
    iac_return = json.loads(iac_return.content)

    # Get case details
    case_return = requests.get(case_url + case_id, auth=HTTPBasicAuth('admin', 'secret'))
    case = json.loads(case_return.content)

    # Collection instrument details
    ci_return = requests.get(ci_url + case["collectionInstrumentId"], auth=HTTPBasicAuth('admin', 'secret'))
    ci = json.loads(ci_return.content)

    # Collection exercise stuff
    collex_return = requests.get(collex_url + case["caseGroup"]["collectionExerciseId"],
                                 auth=HTTPBasicAuth('admin', 'secret'))
    collex = json.loads(collex_return.content)

    # Sample stuff
    sample_return = requests.get(sample_url + case["sampleUnitId"] + "/attributes",
                                 auth=HTTPBasicAuth('admin', 'secret'))
    sample = json.loads(sample_return.content)
    sample_attributes = sample["attributes"]

    for iac in iac_return:
        # Put together payload
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
            "account_service_url": f'{app_config["ACCOUNT_SERVICE_URL"]}{app_config["URL_PATH_PREFIX"]}',
            # required for save/continue
            "country_code": sample_attributes["COUNTRY"],
            "language_code": "en",  # currently only 'en' or 'cy'
            # "display_address": build_display_address(sample_attributes),
            "response_id": build_response_id(case["id"], collex["id"], iac["iac"]),
            "roles": "flusher"
        }

        # Get encryption key stuff
        app_config["key_store"] = jwt.key_store(app_config["JSON_SECRET_KEYS"])

        # Encrypt payload into token
        token = encrypt(flush_payload, key_store=app_config['key_store'], key_purpose="authentication")

        # Call flusher
        flush_url = eq_url + "/flush?token=" + token
        flush_response = requests.post(flush_url)


# Loop over cases to flush them away
for case in case_inprogress:
    flush_cases(case["id"])
    print("Flushing case:" + case["id"])

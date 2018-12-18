import os
import sys

import requests

from app import config

try:
    config_info = getattr(config, os.environ['APP_SETTINGS'])
except (AttributeError, KeyError) as e:
    config_info = config.DevelopmentConfig

# Put config into a dict
config = dict((name, getattr(config_info, name)) for name in dir(config_info) if not name.startswith('__'))

# Setup URLs
case_url = f"{config['CASE_URL']}/cases/"
iac_url = f"{config['IAC_URL']}/iacs/"
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
    print(f'Sample units for collection exercise: {len(samples)}')

    sample_chunks = []
    for i in range(0, len(samples), 10):
        sample_chunks.append(samples[i:i + 10])

    sample_return = []
    for sample_chunk in sample_chunks:
        sample_chunk_return = requests.get(case_url + "sampleunitids?sampleUnitId=" + ','.join(sample_chunk),
                                           auth=config["CASE_AUTH"])
        sample_chunk_return.raise_for_status()
        for sample in sample_chunk_return.json():
            sample_return.append(sample)

    for sample in sample_return:
        case_id = sample["id"]
        iac_return = requests.get(case_url + case_id + "/iac", auth=config["CASE_AUTH"])
        iac_return.raise_for_status()
        iacs = iac_return.json()
        if sample["sampleUnitType"] == "H" and sample["state"] == "INACTIONABLE":
            for iac in iacs:
                iac = requests.get(iac_url + iac['iac'], auth=config["IAC_AUTH"])
                iac.raise_for_status()
                iac_data = iac.json()
                print(f'IAC: {iac_data["iac"]} Active: {iac_data["active"]}')
                if iac_data["active"]:
                    deactivate_iac(iac.json())


def deactivate_iac(iac):
    deactivate_data = {"active": "false", "updatedBy": "Tricky"}
    result = requests.put(iac_url + iac['iac'], json=deactivate_data, auth=config["IAC_AUTH"])
    result.raise_for_status()
    print(f'Deactivated {iac}')


if __name__ == '__main__':
    print(f'Using {config_info.__name__}')
    collection_ex = sys.argv[1:]
    print(f'Collection exercise: {str(collection_ex)}')
    main(collection_ex)

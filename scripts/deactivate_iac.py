#!/usr/bin/env python
import argparse
import logging
import os
import sys

import requests
from structlog import configure, wrap_logger
from structlog.processors import TimeStamper, JSONRenderer
from structlog.stdlib import add_log_level, filter_by_level, LoggerFactory

# Script needs to know about app so append to PYTHONPATH
sys.path.append(os.path.join(os.path.dirname(__file__), os.path.pardir))
from app import config  # NOQA


try:
    config_info = getattr(config, os.environ['APP_SETTINGS'])
except (AttributeError, KeyError) as e:
    config_info = config.DevelopmentConfig

# Put config into a dict
config = dict((name, getattr(config_info, name)) for name in dir(config_info) if not name.startswith('__'))

# Configure logger
logger = wrap_logger(logging.getLogger(__name__))

# Configure argument parser
parser = argparse.ArgumentParser(description='Deactivate IACs for a Collection Exercise.')
parser.add_argument('-c', dest='collectionExercise', type=str, help='Collection Exercise ID.')

# Setup URLs
case_url = f"{config['CASE_URL']}/cases/"
iac_url = f"{config['IAC_URL']}/iacs/"
collex_url = f"{config['COLLECTION_EXERCISE_URL']}/collectionexercises/"
sample_url = f"{config['SAMPLE_URL']}/samples/"


def main(collection_ex_id):

    logger.info("Finding Sample Summary IDs linked to Collection Exercise", collection_exercise=collection_ex_id)
    collection_ex_info = requests.get(collex_url + "link/" + collection_ex_id, auth=config["COLLECTION_EXERCISE_AUTH"])
    collection_ex_info.raise_for_status()
    sample_summary_id = collection_ex_info.json()

    logger.info("Finding Sample Units by Sample Summary ID", collection_exercise=collection_ex_id,
                sample_summary=sample_summary_id)
    sample_units = requests.get(sample_url + sample_summary_id[0] + "/sampleunits",
                                auth=config["SAMPLE_AUTH"])
    sample_units = sample_units.json()
    samples = [sample['id'] for sample in sample_units]
    logger.info(sample_size=len(samples))

    logger.info("Finding Cases for Sample Units", collection_exercise=collection_ex_id,
                sample_summary=sample_summary_id)
    sample_chunks = [samples[i:i + 10] for i in range(0, len(samples), 10)]
    sample_return = []
    for sample_chunk in sample_chunks:
        sample_chunk_return = requests.get(case_url + "sampleunitids?sampleUnitId=" + ','.join(sample_chunk),
                                           auth=config["CASE_AUTH"])
        sample_chunk_return.raise_for_status()
        for sample in sample_chunk_return.json():
            sample_return.append(sample)

    logger.info("De-activating IACs for Sample", collection_exercise=collection_ex_id, sample_summary=sample_summary_id)
    deactivated_total = 0
    for sample in sample_return:
        if sample["sampleUnitType"] == "H":
            case_id = sample["id"]
            iac_return = requests.get(case_url + case_id + "/iac", auth=config["CASE_AUTH"])
            iac_return.raise_for_status()
            iacs = iac_return.json()
            for iac in iacs:
                iac = requests.get(iac_url + iac['iac'], auth=config["IAC_AUTH"])
                iac.raise_for_status()
                iac_data = iac.json()
                logger.info('Found IAC', case_id=iac_data["caseId"],  iac_active=iac_data["active"])
                if iac_data.get("active", False):
                    deactivate_iac(iac.json())
                    deactivated_total += 1
    logger.info("Deactivated IACs total", deactivated_total=deactivated_total, collection_exercise=collection_ex_id)


def deactivate_iac(iac):
    deactivate_data = {"active": "false", "updatedBy": "DEACTIVATE_IAC_TASK"}
    result = requests.put(iac_url + iac['iac'], json=deactivate_data, auth=config["IAC_AUTH"])
    result.raise_for_status()


def add_service(_1, _2, event_dict):
    """
    Add the service name to the event dict.
    """
    event_dict['service'] = 'deactivate_iac'
    return event_dict


if __name__ == '__main__':
    logging.basicConfig(format="%(message)s", stream=sys.stdout, level=logging.INFO)
    configure(processors=[add_log_level, filter_by_level, add_service,
                          TimeStamper(fmt="%Y-%m-%dT%H:%M%s", utc=True, key="created_at"),
                          JSONRenderer(indent=1)],
              logger_factory=LoggerFactory)

    args = parser.parse_args()
    # Print help if no options supplied
    if len(sys.argv) == 1:
        parser.print_help(sys.stderr)
        sys.exit(1)
    collection_ex = args.collectionExercise
    if collection_ex:
        logger.info(configuration=config_info.__name__)
        logger.info(collection_exercise=str(collection_ex))
        main(collection_ex)

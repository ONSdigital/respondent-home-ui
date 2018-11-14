import csv
import logging
import string
from random import choice, randint

import requests
from sqlalchemy import create_engine
from structlog import wrap_logger

from tests.config import Config


logger = wrap_logger(logging.getLogger(__name__))


def execute_sql(sql_string=None, database_uri=Config.DATABASE_URI):
    try:
        logger.debug('Executing SQL script')
        engine = create_engine(database_uri)
        connection = engine.connect()
        trans = connection.begin()

        response = connection.execute(sql_string)

        trans.commit()
        logger.debug('Successfully executed SQL script')
        return response
    finally:
        connection.close()


def get_all_hacs_for_collection_exercise(collection_exercise_id):
    sample_unit_type = "H"

    sql_statement = "SELECT a.iac FROM casesvc.caseiacaudit a " \
                    "INNER JOIN casesvc.case c ON a.casefk = c.casepk " \
                    "INNER JOIN iac.iac i ON a.iac = i.code " \
                    "INNER JOIN casesvc.casegroup g ON c.casegroupfk = g.casegrouppk " \
                    f"WHERE c.statefk = 'ACTIONABLE' AND c.SampleUnitType = '{sample_unit_type}'" \
                    f"AND g.collectionexerciseid = '{collection_exercise_id}' " \
                    "AND i.active = TRUE " \
                    "ORDER BY c.createddatetime DESC;"
    return [row['iac'] for row in execute_sql(sql_string=sql_statement)]


def generate_social_sample(number_of_rows=1):
    addresses = [
        {
            'POSTCODE': generate_random_postcode(),
            'REFERENCE': str(randint(1000000, 9999999) + i),
            'ORGANISATION_NAME': 'Office for National Statistics',
            'ADDRESS_LINE1': 'Cardiff Road',
            'ADDRESS_LINE2': 'Garden Path',
            'LOCALITY': 'Gwent District',
            'TOWN_NAME': 'Newport',
            'UPRN': '123456',
            'TLA': 'OHS',
            'COUNTRY': 'W',
        }
        for i in range(number_of_rows)
    ]
    with open('tests/test_data/sample/tmp-sample.csv', 'w', newline='') as csvfile:
        fieldnames = ('TLA', 'REFERENCE', 'COUNTRY', 'ORGANISATION_NAME', 'ADDRESS_LINE1', 'ADDRESS_LINE2', 'LOCALITY', 'TOWN_NAME', 'POSTCODE', 'UPRN')
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(addresses)


def generate_random_postcode():
    return ''.join([choice(string.ascii_uppercase + string.digits) for _ in range(7)])


def get_collex_id():
    response = requests.get(f'{Config.COLLECTION_EXERCISE_SERVICE}'
                            f'/collectionexercises/1/survey/999',
                            auth=Config.BASIC_AUTH)
    response.raise_for_status()
    return response.json()["id"]

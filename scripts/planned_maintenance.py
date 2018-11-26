#!/usr/bin/python
import argparse
import json
import os
import sys

import redis

sys.path.append(os.path.join(os.path.dirname(__file__), os.path.pardir))

from app import MAINTENANCE_MSG  # NOQA
from app import config  # NOQA


try:
    config_info = getattr(config, os.environ['APP_SETTINGS'])
except (AttributeError, KeyError):
    config_info = config.DevelopmentConfig

redis_connection = redis.Redis(host=config_info.REDIS_HOST, port=config_info.REDIS_PORT)


def main(custom_message, ttl=None):
    message_dict = MAINTENANCE_MSG.copy()
    message_dict['text'] = message_dict['text'].format(custom_message=custom_message)
    redis_connection.set(config_info.REDIS_MAINTENANCE_KEY, json.dumps(message_dict))
    if ttl is not None:
        redis_connection.expire(config_info.REDIS_MAINTENANCE_KEY, ttl)
        print(f'Message set: """{message_dict["text"]}""" TTL: {ttl}s')
    else:
        print(f'Message set: """{message_dict["text"]}"""')
    print(f'Remove with: pipenv run python {__file__} --remove')


def remove_message():
    redis_connection.delete(config_info.REDIS_MAINTENANCE_KEY)
    print('Removed')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Set a planned maintenance message for Respondent Home UI')
    parser.add_argument('message', type=str, help='message to be displayed as part of the planned maintenance')
    parser.add_argument('--remove', action='store_true', help='remove the planned maintenance message')
    parser.add_argument('--ttl', type=int, help='add a time to live in seconds')
    args = parser.parse_args()
    if args.remove:
        remove_message()
    else:
        main(args.message, ttl=args.ttl)

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


def main(custom_message, ttl):
    message_dict = MAINTENANCE_MSG.copy()
    message_dict['text'] = message_dict['text'].format(custom_message=custom_message)
    redis_connection.set(config_info.REDIS_MAINTENANCE_KEY, json.dumps(message_dict))
    redis_connection.expire(config_info.REDIS_MAINTENANCE_KEY, ttl)
    print(message_dict['text'], f'{ttl}s')


if __name__ == '__main__':
    try:
        main(sys.argv[1:][0], sys.argv[1:][1])
    except IndexError:
        print('Usage: pipenv run python set_planned_maintenance "[custom message]" [TTL in seconds, 0 to clear]')

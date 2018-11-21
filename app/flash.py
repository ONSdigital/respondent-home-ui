import json
import logging
from copy import deepcopy
from functools import partial

import redis
from structlog import wrap_logger

from aiohttp import web
from aiohttp_session import get_session


SESSION_KEY = REQUEST_KEY = "flash"

logger = wrap_logger(logging.getLogger(__name__))


class MessageList(list):

    def __contains__(self, item):  # prevent duplicated messages
        return item['type'] in [message['type'] for message in self]


def flash(request, message, position=None):
    if message not in request[REQUEST_KEY]:
        if position is None:
            request[REQUEST_KEY].append(message)
        else:
            request[REQUEST_KEY].insert(position, message)


def pop_flash(request):
    flashed_message = request[REQUEST_KEY]
    request[REQUEST_KEY] = []
    return flashed_message


@web.middleware
async def flash_middleware(request, handler):
    session = await get_session(request)
    flash_incoming = MessageList(session.get(SESSION_KEY, []))
    request[REQUEST_KEY] = deepcopy(flash_incoming)  # copy flash for modification
    try:
        response = await handler(request)
    finally:
        flash_outgoing = request[REQUEST_KEY]
        if flash_outgoing != flash_incoming:
            if flash_outgoing:
                session[SESSION_KEY] = flash_outgoing
            else:
                del session[SESSION_KEY]
    return response


@web.middleware
async def maintenance_middleware(request, handler):
    try:
        maintenance_message = request.app.redis_connection.get(request.app['REDIS_MAINTENANCE_KEY'])
        if maintenance_message:
            maintenance_ttl = request.app.redis_connection.ttl(request.app['REDIS_MAINTENANCE_KEY'])
            maintenance_message = json.loads(maintenance_message)
            logger.info('Maintenance message received from redis',
                        message=maintenance_message['text'],
                        ttl=maintenance_ttl)
            flash(request, maintenance_message, position=0)
    except redis.exceptions.ConnectionError as e:
        logger.error('Failed to connect to redis', message=str(e))
    return await handler(request)


async def context_processor(request):
    return {'get_flashed_messages': partial(pop_flash, request)}

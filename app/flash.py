from copy import deepcopy
from functools import partial

from aiohttp import web
from aiohttp_session import get_session


SESSION_KEY = REQUEST_KEY = "flash"


def flash(request, message):
    request[REQUEST_KEY].append(message)


def pop_flash(request):
    flash = request[REQUEST_KEY]
    request[REQUEST_KEY] = []
    return flash


@web.middleware
async def flash_middleware(request, handler):
    session = await get_session(request)
    flash_incoming = session.get(SESSION_KEY, [])
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


async def context_processor(request):
    return {
        'get_flashed_messages': partial(pop_flash, request),
    }

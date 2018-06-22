from aiohttp import web
from aiohttp_session import get_session


@web.middleware
async def flash_middleware(request, handler):
    async def process(request):
        session = await get_session(request)
        flash_incoming = session.get(SESSION_KEY, [])
        
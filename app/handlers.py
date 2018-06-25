import time
from uuid import UUID

import aiohttp_jinja2
from aiohttp.web import Response
from aiohttp_session import get_session

from .flash import pop_flash, flash


async def get_index(request):
    response = aiohttp_jinja2.render_template("index.html", request, {})
    return response


async def post_index(request):
    data = await request.post()
    iac = ''.join([v.lower() for v in data.values()][:3])

    async with request.app.http_session_pool.get(f'{request.app["IAC_URL"]}/iacs/{iac}') as resp:
        assert resp.status == 200

    return Response(text=iac)


@aiohttp_jinja2.template("base.html")
async def get_questionnaire(request):
    context = {"a_variable": 12}
    response = aiohttp_jinja2.render_template("base.html", request, context)
    return response


async def post_questionnaire(request):
    return Response(text="Questionnaire post!")

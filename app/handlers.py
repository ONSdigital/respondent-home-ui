import time

import aiohttp_jinja2
from aiohttp.web import Response
from aiohttp_session import get_session

from .flash import pop_flash


async def get_index(request):
    response = aiohttp_jinja2.render_template("index.html", request, {})
    return response


async def post_index(request):
    return Response(text="A post!")


@aiohttp_jinja2.template("base.html")
async def get_questionnaire(request):
    context = {"a_variable": 12}
    response = aiohttp_jinja2.render_template("base.html", request, context)
    return response


async def post_questionnaire(request):
    return Response(text="Questionnaire post!")

import aiohttp_jinja2
from aiohttp.web import Response


@aiohttp_jinja2.template('index.html')
async def get_index(request):
    context = {'a_variable': 12}
    response = aiohttp_jinja2.render_template("base.html", request, context)
    return response


async def post_index(request):
    return Response(text="A post!")

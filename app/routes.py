from collections import namedtuple

from . import handlers


Route = namedtuple("Route", ["method", "path", "handler", "name"])


ROUTES = [
    Route("GET",  "/", handler=handlers.get_index,  name="get_index"),
    Route("POST", "/", handler=handlers.post_index, name="post_index"),
    Route("GET", "/info", handler=handlers.get_info, name="get_info"),
]


def setup(app, url_path_prefix):
    """Set up routes. Preserve /info for app health check"""
    for route in ROUTES:
        method, url, handler, name = route
        url = url.lstrip('/')
        full_url = f"{url_path_prefix}/{url}" if name != "get_info" else f"/{url}"
        app.router.add_route(method, full_url, handler, name=name)

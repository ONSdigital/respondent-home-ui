from aiohttp_utils.routing import add_resource_context

from .handlers import routes


def setup(app, url_path_prefix):
    """Set up routes as resources so we can use the `Index:get` notation for URL lookup."""
    for route in routes:
        prefix = url_path_prefix if route.kwargs.get('use_prefix', True) else ''
        with add_resource_context(app, module='app.handlers', url_prefix=prefix) as new_route:
            new_route(route.path, route.handler())

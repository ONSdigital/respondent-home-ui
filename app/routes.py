from .handlers import routes


def setup(app, url_path_prefix):
    """Set up routes."""
    prefix = url_path_prefix.lstrip("/")
    for route in routes:
        url = route.path.lstrip('/')
        route_path = f"/{prefix}{url}" if route.kwargs.get('use_prefix', True) else f"/{url}"
        app.router.add_route(route.method, route_path, route.handler, name=route.kwargs.get('name'))

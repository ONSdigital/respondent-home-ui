from .handlers import routes


def setup(app, url_path_prefix):
    """Set up routes."""
    for route in routes:
        path = route.path.lstrip('/')
        path = f'/{path}' if path else ''
        route_path = f'{url_path_prefix}{path}' if route.kwargs.get('use_prefix', True) else path
        app.router.add_route(route.method, route_path, route.handler, name=route.kwargs.get('name'))

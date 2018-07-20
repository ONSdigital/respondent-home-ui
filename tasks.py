import os
import sys

import requests
from envparse import ConfigurationError, Env
from invoke import task, run as run_command
from requests import RequestException
from retrying import retry

from tests.config import Config


env = Env()


class HealthCheckException(Exception):
    def __init__(self, service):
        self.service = service

    def __str__(self) -> str:
        return f'Healthcheck fails for {self.service.lower()}'


def retry_if_http_error(exception):
    print(f'error has occurred: {str(exception)}')
    return isinstance(exception, RequestException) or isinstance(exception, HealthCheckException)


@retry(retry_on_exception=retry_if_http_error, wait_fixed=10000, stop_max_delay=600000, wrap_exception=True)
def check_status(service, url):
    try:
        resp = requests.get(f'{url}/info')
        resp.raise_for_status()
    except Exception:
        raise HealthCheckException(service)


@task
def run(ctx, port=None):
    port = port or env("PORT", default=9092)
    if not os.getenv('APP_SETTINGS'):
        os.environ['APP_SETTINGS'] = 'DevelopmentConfig'
    run_command(f"adev runserver app --port {port}", echo=True)


@task
def server(ctx, port=None, reload=True):
    """Run the development server"""
    try:
        port = port or env("PORT")
    except ConfigurationError:
        print('Port not set. Use `inv server --port=[INT]` or set the PORT environment variable.')
        sys.exit(1)

    command = (
        'gunicorn "app.app:create_app()" -w 4 '
        f"--bind 0.0.0.0:{port} --worker-class aiohttp.worker.GunicornWebWorker --access-logfile - --log-level DEBUG"
    )

    if reload:
        command += " --reload"
    run_command(command, echo=True)


@task
def flake8(ctx):
    """Run flake8 on the codebase"""
    run_command("flake8 app", echo=True)


@task
def unittests(ctx):
    import pytest

    return pytest.main(["tests/unit"])


@task(pre=[flake8])
def test(ctx, clean=False):
    """Run all the tests."""

    if clean:
        cleanpy(ctx)

    return_code = unittests(ctx) or smoke(ctx) or integration(ctx)

    sys.exit(return_code)


@task
def smoke(ctx, clean=False):
    """Run the smoke tests."""
    import pytest

    if clean:
        cleanpy(ctx)
    retcode = pytest.main(["tests/smoke"])
    sys.exit(retcode)


@task
def integration(ctx, clean=False):
    """Run the integration tests."""
    import pytest

    if clean:
        cleanpy(ctx)
    retcode = pytest.main(["tests/integration"])
    sys.exit(retcode)


@task
def cleanpy(ctx):
    """Clear out __pycache__ directories."""
    run_command("find . -path '*/__pycache__/*' -delete", echo=True)
    print("Cleaned up.")


@task
def demo(ctx):
    run_command("python -m tests.demo")


@task
def wait(ctx):
    [check_status(k, v) for k, v in dict(vars(Config)).items() if k.endswith('_SERVICE') or k.endswith('_UI')]
    print('all services are up')


@task
def coverage(ctx):
    run_command("pytest tests/unit --cov app --cov-report html --ignore=node_modules")

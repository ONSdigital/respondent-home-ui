import os
import sys

from envparse import ConfigurationError, Env
from invoke import task, run as run_command


env = Env()


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

    return pytest.main(["tests"])


@task(pre=[flake8])
def test(ctx, clean=False):
    """Run the tests."""

    if clean:
        clean_pycache(ctx)

    retcode = unittests(ctx)

    sys.exit(retcode)


@task
def smoke(ctx, clean=False):
    """Run the tests."""
    import pytest

    if clean:
        clean_pycache(ctx)
    retcode = pytest.main(["tests/smoke"])
    sys.exit(retcode)


@task
def clean_pycache(ctx):
    """Clear out __pycache__ directories."""
    run_command("find . -path '*/__pycache__/*' -delete", echo=True)
    print("Cleaned up.")

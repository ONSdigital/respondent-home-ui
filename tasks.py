import os
import sys

from envparse import ConfigurationError, Env
from invoke import task, run


env = Env()


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
    run(command, echo=True)


@task
def flake8(ctx):
    """Run flake8 on the codebase"""
    run("flake8 app", echo=True)


@task(pre=[flake8])
def test(ctx, clean=False):
    """Run the tests."""
    import pytest

    if clean:
        clean_pycache(ctx)
    retcode = pytest.main(["app"])
    sys.exit(retcode)


@task
def clean_pycache(ctx):
    """Clear out __pycache__ directories."""
    run("find . -path '*/__pycache__/*' -delete", echo=True)
    print("Cleaned up.")

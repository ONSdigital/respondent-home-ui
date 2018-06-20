import os
import sys

from invoke import task, run


@task
def server(ctx, port=None, reload=True):
    """Run the development server"""

    command = (
        "pipenv run python -m app.app"
    )

    if reload:
        command += " --reload"
    run(command, echo=True)


@task
def test(ctx, clean=False):
    """Run the tests."""
    import pytest

    if clean:
        clean()
    flake()
    retcode = pytest.main(["api"])
    sys.exit(retcode)


@task
def flake8(ctx):
    """Run flake8 on the codebase"""
    run("flake8 api", echo=True)


@task
def clean(ctx):
    """Clear out __pycache__ directories."""
    run("find . -path '*/__pycache__/*' -delete", echo=True)
    print("Cleaned up.")

import json
import logging
import os

from sdc.crypto.key_store import validate_required_keys
from sdc.crypto.key_store import KeyStore
from structlog import wrap_logger

logger = wrap_logger(logging.getLogger('respondent-home'))


def key_store(path: str) -> bool:
    dirname = os.path.dirname(__file__)
    filepath = os.path.join(dirname, path)

    with open(filepath) as fp:
        secrets = json.load(fp)

    logger.info("Validating key file")
    validate_required_keys(secrets, "authentication")

    return KeyStore(secrets)

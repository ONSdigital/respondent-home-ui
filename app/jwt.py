import json
import logging

from sdc.crypto.key_store import validate_required_keys
from sdc.crypto.key_store import KeyStore
from structlog import wrap_logger

logger = wrap_logger(logging.getLogger('respondent-home'))


def key_store(keys: str) -> KeyStore:
    secrets = json.loads(keys)

    logger.info("Validating key file")
    validate_required_keys(secrets, "authentication")

    return KeyStore(secrets)

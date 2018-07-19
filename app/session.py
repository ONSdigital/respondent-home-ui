import base64

from aiohttp_session import session_middleware
from aiohttp_session.cookie_storage import EncryptedCookieStorage
from cryptography import fernet


def generate_new_key():
    # NB: should only be used to generate a new environment variable
    fernet_key = fernet.Fernet.generate_key()
    return base64.urlsafe_b64decode(fernet_key)


def setup(secret_key):
    return session_middleware(EncryptedCookieStorage(secret_key))

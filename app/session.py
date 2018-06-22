import base64

from aiohttp_session import setup as session_setup
from aiohttp_session import session_middleware
from aiohttp_session.cookie_storage import EncryptedCookieStorage
from cryptography import fernet


def setup():
    fernet_key = fernet.Fernet.generate_key()
    secret_key = base64.urlsafe_b64decode(fernet_key)
    return session_middleware(EncryptedCookieStorage(secret_key))

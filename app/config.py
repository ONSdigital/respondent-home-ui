from functools import partial

from envparse import Env


class Config(dict):

    def from_object(self, obj):
        for key in dir(obj):
            if key.isupper():
                self[key] = getattr(obj, key)

    def __getattr__(self, name):
        try:
            return self[name]
        except KeyError:
            raise AttributeError('"{}" not found'.format(name))

    def __setattr__(self, name, value):
        self[name] = value


class BaseConfig:
    env = Env()
    env = partial(env, default=None)

    HOST = env("HOST")
    PORT = env("PORT")
    LOG_LEVEL = env("LOG_LEVEL")
    STATIC_ROOT = "app/static"

    ACCOUNT_SERVICE_URL = env("ACCOUNT_SERVICE_URL")
    EQ_URL = env("EQ_URL")
    JSON_SECRET_KEYS = env("JSON_SECRET_KEYS")

    CASE_URL = env("CASE_URL")
    CASE_AUTH = (env("CASE_USERNAME"), env("CASE_PASSWORD"))

    COLLECTION_EXERCISE_URL = env("COLLECTION_EXERCISE_URL")
    COLLECTION_EXERCISE_AUTH = env("COLLECTION_EXERCISE_AUTH")

    COLLECTION_INSTRUMENT_URL = env("COLLECTION_INSTRUMENT_URL")
    COLLECTION_INSTRUMENT_AUTH = env("COLLECTION_INSTRUMENT_AUTH")

    IAC_URL = env("IAC_URL")
    IAC_AUTH = (env("IAC_USERNAME"), env("IAC_PASSWORD"))


class DevelopmentConfig:
    env = Env()
    HOST = env.str("HOST", default="0.0.0.0")
    PORT = env.int("PORT", default="9092")
    LOG_LEVEL = env("LOG_LEVEL", default="INFO")
    STATIC_ROOT = "app/static"

    ACCOUNT_SERVICE_URL = env.str("ACCOUNT_SERVICE_URL", default="http://0.0.0.0:9092")
    EQ_URL = env.str("EQ_URL", default="http://0.0.0.0:5000/session?token=")
    JSON_SECRET_KEYS = env.str("JSON_SECRET_KEYS", default=None) or open("./tests/test_data/test_keys.json").read()

    COLLECTION_EXERCISE_URL = env.str("COLLECTION_EXERCISE_URL", default="http://0.0.0.0:8145")
    COLLECTION_EXERCISE_AUTH = (
        env.str("COLLECTION_EXERCISE_USERNAME", default="admin"),
        env.str("COLLECTION_EXERCISE_PASSWORD", default="secret")
    )

    COLLECTION_INSTRUMENT_URL = env.str("COLLECTION_INSTRUMENT_URL", default="http://0.0.0.0:8002")
    COLLECTION_INSTRUMENT_AUTH = (
        env.str("COLLECTION_INSTRUMENT_USERNAME", default="admin"),
        env.str("COLLECTION_INSTRUMENT_PASSWORD", default="secret")
    )

    CASE_URL = env.str("CASE_URL", default="http://0.0.0.0:8171")
    CASE_AUTH = (env.str("CASE_USERNAME", default="admin"), env.str("CASE_PASSWORD", default="secret"))

    IAC_URL = env.str("IAC_URL", default="http://0.0.0.0:8121")
    IAC_AUTH = (env.str("IAC_USERNAME", default="admin"), env.str("IAC_PASSWORD", default="secret"))


class TestingConfig:
    HOST = "0.0.0.0"
    PORT = "9092"
    LOG_LEVEL = "INFO"
    STATIC_ROOT = "app/static"

    ACCOUNT_SERVICE_URL = "http://0.0.0.0:9092"
    EQ_URL = "http://0.0.0.0:5000/session?token="
    JSON_SECRET_KEYS = open("./tests/test_data/test_keys.json").read()

    COLLECTION_EXERCISE_URL = "http://0.0.0.0:8145"
    COLLECTION_EXERCISE_AUTH = ("admin", "secret")

    COLLECTION_INSTRUMENT_URL = "http://0.0.0.0:8002"
    COLLECTION_INSTRUMENT_AUTH = ("admin", "secret")

    CASE_URL = "http://0.0.0.0:8171"
    CASE_AUTH = ("admin", "secret")

    IAC_URL = "http://0.0.0.0:8121"
    IAC_AUTH = ("admin", "secret")

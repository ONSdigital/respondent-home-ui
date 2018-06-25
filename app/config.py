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

    EQ_URL = env("EQ_URL")
    JSON_SECRET_KEYS = env("JSON_SECRET_KEYS")

    IAC_URL = env("IAC_URL")
    IAC_AUTH = (env("IAC_USERNAME"), env("IAC_PASSWORD"))


class DevelopmentConfig:
    env = Env()
    HOST = env.str("HOST", default="0.0.0.0")
    PORT = env.int("PORT", default="9092")
    LOG_LEVEL = env("LOG_LEVEL", default="INFO")

    EQ_URL = env.str("EQ_URL", default="https://localhost:5000/session")
    JSON_SECRET_KEYS = env.json("JSON_SECRET_KEYS", default="tests/test_keys.json")

    IAC_URL = env.str("IAC_URL", default="http://0.0.0.0:8121")
    IAC_AUTH = (env.str("IAC_USERNAME", default="admin"), env.str("IAC_PASSWORD", default="secret"))

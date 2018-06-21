from envparse import env


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
    HOST = env.str("HOST", default=None)
    PORT = env.int("PORT", default=None)
    EQ_URL = env.str("EQ_URL", default=None)
    IAC_URL = env.str("IAC_URL", default=None)
    IAC_AUTH = (
        env.str("IAC_USERNAME", default=None),
        env.str("IAC_PASSWORD", default=None),
    )


class DevelopmentConfig:
    HOST = env.str("HOST", default="0.0.0.0")
    PORT = env.int("PORT", default="9092")
    EQ_URL = env.str("EQ_URL", default='https://localhost:5000/session?token=')
    IAC_URL = env.str("IAC_URL", default='http://localhost:8121')
    IAC_AUTH = (
        env.str("IAC_USERNAME", default="admin"),
        env.str("IAC_PASSWORD", default="secret"),
    )
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


class DevelopmentConfig:
    HOST = env.str("HOST", default="0.0.0.0")
    PORT = env.int("PORT", default="9092")

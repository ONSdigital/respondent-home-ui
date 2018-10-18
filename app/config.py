from functools import partial

from envparse import Env, ConfigurationError

from app.session import generate_new_key


class Config(dict):

    def from_object(self, obj):
        for key in dir(obj):
            if key.isupper():
                config = getattr(obj, key)
                if config is None:
                    raise ConfigurationError(f'{key} not set')
                self[key] = config

    def get_service_urls_mapped_with_path(self, path='/', suffix='URL', excludes=None) -> dict:
        return {service_name: f"{self[service_name]}{path}"
                for service_name in self
                if service_name.endswith(suffix)
                and service_name not in (excludes if excludes else [])}

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

    ACCOUNT_SERVICE_URL = env("ACCOUNT_SERVICE_URL")
    EQ_URL = env("EQ_URL")
    JSON_SECRET_KEYS = env("JSON_SECRET_KEYS")

    CASE_URL = env("CASE_URL")
    CASE_AUTH = (env("CASE_USERNAME"), env("CASE_PASSWORD"))

    COLLECTION_EXERCISE_URL = env("COLLECTION_EXERCISE_URL")
    COLLECTION_EXERCISE_AUTH = (env("COLLECTION_EXERCISE_USERNAME"), env("COLLECTION_EXERCISE_PASSWORD"))

    COLLECTION_INSTRUMENT_URL = env("COLLECTION_INSTRUMENT_URL")
    COLLECTION_INSTRUMENT_AUTH = (env("COLLECTION_INSTRUMENT_USERNAME"), env("COLLECTION_INSTRUMENT_PASSWORD"))

    IAC_URL = env("IAC_URL")
    IAC_AUTH = (env("IAC_USERNAME"), env("IAC_PASSWORD"))

    SAMPLE_URL = env("SAMPLE_URL")
    SAMPLE_AUTH = (env("SAMPLE_USERNAME"), env("SAMPLE_PASSWORD"))

    SURVEY_URL = env("SURVEY_URL")
    SURVEY_AUTH = (env("SURVEY_USERNAME"), env("SURVEY_PASSWORD"))

    SECRET_KEY = env("SECRET_KEY")

    URL_PATH_PREFIX = env("URL_PATH_PREFIX", default="")

    ANALYTICS_UA_ID = env("ANALYTICS_UA_ID", default="")


class ProductionConfig(BaseConfig):
    pass


class DevelopmentConfig:
    env = Env()
    HOST = env.str("HOST", default="0.0.0.0")
    PORT = env.int("PORT", default="9092")
    LOG_LEVEL = env("LOG_LEVEL", default="INFO")

    ACCOUNT_SERVICE_URL = env.str("ACCOUNT_SERVICE_URL", default="http://localhost:9092")
    EQ_URL = env.str("EQ_URL", default="http://localhost:5000")
    JSON_SECRET_KEYS = env.str("JSON_SECRET_KEYS", default=None) or open("./tests/test_data/test_keys.json").read()

    COLLECTION_EXERCISE_URL = env.str("COLLECTION_EXERCISE_URL", default="http://localhost:8145")
    COLLECTION_EXERCISE_AUTH = (
        env.str("COLLECTION_EXERCISE_USERNAME", default="admin"),
        env.str("COLLECTION_EXERCISE_PASSWORD", default="secret")
    )

    COLLECTION_INSTRUMENT_URL = env.str("COLLECTION_INSTRUMENT_URL", default="http://localhost:8002")
    COLLECTION_INSTRUMENT_AUTH = (
        env.str("COLLECTION_INSTRUMENT_USERNAME", default="admin"),
        env.str("COLLECTION_INSTRUMENT_PASSWORD", default="secret")
    )

    CASE_URL = env.str("CASE_URL", default="http://localhost:8171")
    CASE_AUTH = (env.str("CASE_USERNAME", default="admin"), env.str("CASE_PASSWORD", default="secret"))

    IAC_URL = env.str("IAC_URL", default="http://localhost:8121")
    IAC_AUTH = (env.str("IAC_USERNAME", default="admin"), env.str("IAC_PASSWORD", default="secret"))

    SAMPLE_URL = env("SAMPLE_URL", default="http://localhost:8125")
    SAMPLE_AUTH = (env("SAMPLE_USERNAME", default="admin"), env("SAMPLE_PASSWORD", default="secret"))

    SURVEY_URL = env("SURVEY_URL", default="http://localhost:8080")
    SURVEY_AUTH = (env("SURVEY_USERNAME", default="admin"), env("SURVEY_PASSWORD", default="secret"))

    SECRET_KEY = env.str("SECRET_KEY", default=None) or generate_new_key()

    URL_PATH_PREFIX = env("URL_PATH_PREFIX", default="")

    ANALYTICS_UA_ID = env("ANALYTICS_UA_ID", default="")


class TestingConfig:
    HOST = "0.0.0.0"
    PORT = "9092"
    LOG_LEVEL = "INFO"

    ACCOUNT_SERVICE_URL = "http://localhost:9092"
    EQ_URL = "http://localhost:5000"
    JSON_SECRET_KEYS = open("./tests/test_data/test_keys.json").read()

    COLLECTION_EXERCISE_URL = "http://localhost:8145"
    COLLECTION_EXERCISE_AUTH = ("admin", "secret")

    COLLECTION_INSTRUMENT_URL = "http://localhost:8002"
    COLLECTION_INSTRUMENT_AUTH = ("admin", "secret")

    CASE_URL = "http://localhost:8171"
    CASE_AUTH = ("admin", "secret")

    IAC_URL = "http://localhost:8121"
    IAC_AUTH = ("admin", "secret")

    SAMPLE_URL = "http://localhost:8125"
    SAMPLE_AUTH = ("admin", "secret")

    SURVEY_URL = "http://localhost:8080"
    SURVEY_AUTH = ("admin", "secret")

    SECRET_KEY = generate_new_key()

    URL_PATH_PREFIX = ""

    ANALYTICS_UA_ID = ""

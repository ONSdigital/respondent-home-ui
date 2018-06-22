from envparse import env

env.read_envfile()

ENV = env.str("APP_SETTINGS", default="BaseConfig")
DEBUG = ENV != "Production"

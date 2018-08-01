from envparse import Env


ENV = Env().str("APP_SETTINGS", default="BaseConfig")
DEBUG = ENV != "ProductionConfig"

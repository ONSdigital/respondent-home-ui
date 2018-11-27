import cfenv


class ONSCloudFoundry(object):
    def __init__(self, app):
        self._cf_env = cfenv.AppEnv()
        self._app = app

    @property
    def detected(self):
        return self._cf_env.app

    @property
    def redis(self):
        return self._cf_env.get_service(name=self._app['REDIS_SERVICE'])

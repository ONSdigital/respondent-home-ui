import logging
import os

from structlog import wrap_logger
import cfenv


logger = wrap_logger(logging.getLogger(__name__))


class ONSCloudFoundry(object):
    def __init__(self, redis_name):
        self.cf_env = cfenv.AppEnv()
        self.redis_name = redis_name
        self._redis = None

    @property
    def detected(self):
        return self.cf_env.app

    @property
    def redis(self):
        if not self.redis_name:
            logger.warning('Cloud Foundry redis service name not set')
            return
        self._redis = self._redis or self.cf_env.get_service(name=self.redis_name)
        if self._redis is None:
            logger.warning('Cloud Foundry redis service not found',
                           redis_name=self.redis_name,
                           services=os.getenv('VCAP_SERVICES', '{}'))
        return self._redis

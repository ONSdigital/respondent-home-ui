import json
from unittest.mock import MagicMock

import redis
from aiohttp.test_utils import make_mocked_request, unittest_run_loop

from app import MAINTENANCE_MSG
from app.flash import REQUEST_KEY, maintenance_middleware
from . import RHTestCase


async def dummy_handler(_):
    pass


class TestMaintenanceMiddleware(RHTestCase):

    def setUp(self):
        super().setUp()
        self.message_dict = MAINTENANCE_MSG.copy()
        self.message_dict['text'] = self.message_dict['text'].format(message='Test')

    @unittest_run_loop
    async def test_get_maintenance_message(self):
        request = make_mocked_request('GET', '/', app=self.app)
        request[REQUEST_KEY] = []
        request.app.redis_connection.get = MagicMock(return_value=json.dumps(self.message_dict))
        request.app.redis_connection.ttl = MagicMock(return_value=1)
        with self.assertLogs('app.flash', 'INFO') as cm:
            await maintenance_middleware(request, dummy_handler)
        self.assertLogLine(cm, 'Maintenance message received from redis', message=self.message_dict['text'], ttl=1)
        self.assertIn(self.message_dict, request[REQUEST_KEY])

    @unittest_run_loop
    async def test_get_maintenance_message_first(self):
        request = make_mocked_request('GET', '/', app=self.app)
        request[REQUEST_KEY] = [123]
        request.app.redis_connection.get = MagicMock(return_value=json.dumps(self.message_dict))
        request.app.redis_connection.ttl = MagicMock(return_value=1)
        with self.assertLogs('app.flash', 'INFO') as cm:
            await maintenance_middleware(request, dummy_handler)
        self.assertLogLine(cm, 'Maintenance message received from redis', message=self.message_dict['text'], ttl=1)
        self.assertEqual(self.message_dict, request[REQUEST_KEY][0])

    @unittest_run_loop
    async def test_get_no_maintenance_message(self):
        request = make_mocked_request('GET', '/', app=self.app)
        request[REQUEST_KEY] = []
        request.app.redis_connection.get = MagicMock(return_value=None)
        await maintenance_middleware(request, dummy_handler)
        self.assertNotIn(self.message_dict, request[REQUEST_KEY])

    @unittest_run_loop
    async def test_get_maintenance_message_failed(self):
        request = make_mocked_request('GET', '/', app=self.app)
        request[REQUEST_KEY] = []
        request.app.redis_connection.get = MagicMock(side_effect=redis.exceptions.ConnectionError)
        with self.assertLogs('app.flash', 'ERROR') as cm:
            await maintenance_middleware(request, dummy_handler)
        self.assertLogLine(cm, 'Failed to connect to redis')
        self.assertNotIn(self.message_dict, request[REQUEST_KEY])

    @unittest_run_loop
    async def test_get_unexpected_maintenance_message(self):
        request = make_mocked_request('GET', '/', app=self.app)
        request[REQUEST_KEY] = []
        request.app.redis_connection.get = MagicMock(return_value=[1, 2, 3])
        request.app.redis_connection.ttl = MagicMock(return_value=1)
        with self.assertLogs('app.flash', 'ERROR') as cm:
            await maintenance_middleware(request, dummy_handler)
        self.assertLogLine(cm, 'Unexpected message type received from redis')
        self.assertNotIn(self.message_dict, request[REQUEST_KEY])

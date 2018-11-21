import json
from unittest.mock import MagicMock

import redis
from aiohttp.test_utils import make_mocked_request, unittest_run_loop

from app.flash import REQUEST_KEY, maintenance_middleware
from . import RHTestCase


async def dummy_handler(request):
    pass


class TestMaintenanceMiddleware(RHTestCase):

    @unittest_run_loop
    async def test_get_maintenance_message(self):
        message_dict = {
            'text': ('This site will be temporarily unavailable for maintenance <b>Test</b>.'
                     '\n'
                     'We apologise for any inconvenience this may cause.'),
            'level': 'INFO',
            'type': 'PLANNED_MAINTENANCE',
        }
        request = make_mocked_request('GET', '/', app=self.app)
        request[REQUEST_KEY] = []
        request.app.redis_connection.get = MagicMock(return_value=json.dumps(message_dict))
        request.app.redis_connection.ttl = MagicMock(return_value=1)
        with self.assertLogs('app.flash', 'INFO') as cm:
            await maintenance_middleware(request, dummy_handler)
        self.assertLogLine(cm, 'Maintenance message received from redis', message=message_dict['text'], ttl=1)
        self.assertIn(message_dict, request[REQUEST_KEY])

    @unittest_run_loop
    async def test_get_maintenance_message_first(self):
        message_dict = {
            'text': ('This site will be temporarily unavailable for maintenance <b>Test</b>.'
                     '\n'
                     'We apologise for any inconvenience this may cause.'),
            'level': 'INFO',
            'type': 'PLANNED_MAINTENANCE',
        }
        request = make_mocked_request('GET', '/', app=self.app)
        request[REQUEST_KEY] = [123]
        request.app.redis_connection.get = MagicMock(return_value=json.dumps(message_dict))
        request.app.redis_connection.ttl = MagicMock(return_value=1)
        with self.assertLogs('app.flash', 'INFO') as cm:
            await maintenance_middleware(request, dummy_handler)
        self.assertLogLine(cm, 'Maintenance message received from redis', message=message_dict['text'], ttl=1)
        self.assertEqual(message_dict, request[REQUEST_KEY][0])

    @unittest_run_loop
    async def test_get_no_maintenance_message(self):
        message_dict = {
            'text': ('This site will be temporarily unavailable for maintenance <b>Test</b>.'
                     '\n'
                     'We apologise for any inconvenience this may cause.'),
            'level': 'INFO',
            'type': 'PLANNED_MAINTENANCE',
        }
        request = make_mocked_request('GET', '/', app=self.app)
        request[REQUEST_KEY] = []
        request.app.redis_connection.get = MagicMock(return_value=None)
        await maintenance_middleware(request, dummy_handler)
        self.assertNotIn(message_dict, request[REQUEST_KEY])

    @unittest_run_loop
    async def test_get_maintenance_message_failed(self):
        message_dict = {
            'text': ('This site will be temporarily unavailable for maintenance <b>Test</b>.'
                     '\n'
                     'We apologise for any inconvenience this may cause.'),
            'level': 'INFO',
            'type': 'PLANNED_MAINTENANCE',
        }
        request = make_mocked_request('GET', '/', app=self.app)
        request[REQUEST_KEY] = []
        request.app.redis_connection.get = MagicMock(side_effect=redis.exceptions.ConnectionError)
        with self.assertLogs('app.flash', 'ERROR') as cm:
            await maintenance_middleware(request, dummy_handler)
        self.assertLogLine(cm, 'Failed to connect to redis')
        self.assertNotIn(message_dict, request[REQUEST_KEY])

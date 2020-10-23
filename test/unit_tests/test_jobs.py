import unittest
from unittest.mock import Mock
from jobs import check_block_height_increase, check_health, check_syncing
from models.nodes import Node, UnauthorizedException


class ContextMock:
    bot_data = {}


class JobTests(unittest.TestCase):
    context = ContextMock()
    node_mock = Mock(spec=Node)

    def __init__(self, *args, **kwargs):
        super(JobTests, self).__init__(*args, **kwargs)
        self.node_mock.get_block_height.return_value = 42
        self.node_mock.node_id = ":)"
        self.node_mock.node_ip = "123"
        self.node_mock.network_name = "MoshbitChain"

    def test_block_height_increase_check(self):
        message = check_block_height_increase(self.context, self.node_mock)
        self.assertIs(message, None)

        message = check_block_height_increase(self.context, self.node_mock)
        self.assertIn("Block height is not increasing anymore".lower(), message.lower())

        message = check_block_height_increase(self.context, self.node_mock)
        self.assertIs(message, None)

        self.node_mock.get_block_height.return_value = 43

        message = check_block_height_increase(self.context, self.node_mock)
        self.assertIn("Block height is increasing again".lower(), message.lower())

        self.node_mock.get_block_height.return_value = 44

        message = check_block_height_increase(self.context, self.node_mock)
        self.assertIs(message, None)

        self.node_mock.get_block_height.side_effect = UnauthorizedException()
        message = check_block_height_increase(self.context, self.node_mock)
        self.assertIn(f"returns 401 - Unauthorized".lower(), message.lower())

    def test_health_check(self):
        self.node_mock.is_healthy.return_value = True
        message = check_health(self.node_mock, self.context)
        self.assertIs(message, None)

        self.node_mock.is_healthy.return_value = False
        message = check_health(self.node_mock, self.context)
        self.assertIn(f"is not healthy anymore".lower(), message.lower())

        message = check_health(self.node_mock, self.context)
        self.assertIs(message, None)

        self.node_mock.is_healthy.return_value = True
        message = check_health(self.node_mock, self.context)
        self.assertIn(f"is healthy again!".lower(), message.lower())

        message = check_health(self.node_mock, self.context)
        self.assertIs(message, None)

    def test_syncing_check(self):
        self.node_mock.is_fully_synced.return_value = True
        message = check_syncing(self.node_mock, self.context)
        self.assertIs(message, None)

        self.node_mock.is_fully_synced.return_value = False
        message = check_syncing(self.node_mock, self.context)
        self.assertIn(f"is syncing with the network".lower(), message.lower())

        message = check_syncing(self.node_mock, self.context)
        self.assertIs(message, None)

        self.node_mock.is_fully_synced.return_value = True
        message = check_syncing(self.node_mock, self.context)
        self.assertIn(f"is fully synced again".lower(), message.lower())

        message = check_syncing(self.node_mock, self.context)
        self.assertIs(message, None)

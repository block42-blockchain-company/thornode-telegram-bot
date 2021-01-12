import unittest
from unittest.mock import Mock, patch

from constants.messages import NETWORK_HEALTH_WARNING, NETWORK_HEALTHY_AGAIN, NetworkHealthStatus

from jobs.other_nodes_jobs import *
from jobs.other_nodes_jobs import check_health
from jobs.thornodes_jobs import check_solvency, check_network_security
from models.nodes import Node, UnauthorizedException


class ContextMock:
    bot_data = {}


class JobTests(unittest.TestCase):
    context = ContextMock()
    node_mock = Mock(spec=Node)

    def __init__(self, *args, **kwargs):
        super(JobTests, self).__init__(*args, **kwargs)
        self.node_mock.get_block_height.return_value = 42
        self.node_mock.node_id = "node_1234"
        self.node_mock.node_ip = "11.42.25.201"
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
        message = check_other_nodes_syncing(self.node_mock, self.context)
        self.assertIs(message, None)

        self.node_mock.is_fully_synced.return_value = False
        message = check_other_nodes_syncing(self.node_mock, self.context)
        self.assertIn(f"is syncing with the network".lower(), message.lower())

        message = check_other_nodes_syncing(self.node_mock, self.context)
        self.assertIs(message, None)

        self.node_mock.is_fully_synced.return_value = True
        message = check_other_nodes_syncing(self.node_mock, self.context)
        self.assertIn(f"is fully synced again".lower(), message.lower())

        message = check_other_nodes_syncing(self.node_mock, self.context)
        self.assertIs(message, None)

    @patch('jobs.thornodes_jobs.yggdrasil_solvency_check')
    @patch('jobs.thornodes_jobs.asgard_solvency_check')
    def test_solvency_check_success(self, mock_asgard_solvency_check, mock_yggdrasil_solvency_check):
        mock_asgard_solvency_check.return_value = {"is_solvent": True,
                                                   "solvent_coins": {'BNB.RUNE-67C': '461534.11554061',
                                                                     'BNB.MATIC-416': '3042.60609950'}}
        mock_yggdrasil_solvency_check.return_value = {"is_solvent": True,
                                                      "solvent_coins": {'BNB.RUNE-67C': '129646.02621566999',
                                                                        'BNB.MATIC-416': '6580.429120989999'}}

        message = check_solvency(self.context)
        self.assertIs(message, None, "Solvency message should be None but is not!")

        mock_yggdrasil_solvency_check.return_value = {"is_solvent": False,
                                                      "solvent_coins": {'BNB.RUNE-67C': '129646.02621566999',
                                                                        'BNB.MATIC-416': '6580.429120989999'},
                                                      'insolvent_coins': {
                                                          'tthorpub1addwnpepqwl6dhku5q2r98mwlx4ey4epzz5hamzc5c0s3z7qm8gudekdzgr4wjdafnc':
                                                              {'BNB.BNB':
                                                                   {'expected': '1175126895',
                                                                    'actual': '11.75096895'}}}}
        for i in range(0, MISSING_FUNDS_THRESHOLD - 1):
            message = check_solvency(self.context)
            self.assertIs(message, None, "Solvency message should be None but is not!")

        message = check_solvency(self.context)
        self.assertIn("THORChain is *missing funds*! 💀", message,
                      "Solvency message should alert about missing funds but does not!")

        mock_yggdrasil_solvency_check.return_value = {"is_solvent": True,
                                                      "solvent_coins": {'BNB.RUNE-67C': '129646.02621566999',
                                                                        'BNB.MATIC-416': '6580.429120989999'}}

        message = check_solvency(self.context)
        self.assertIn("THORChain is *100% solvent* again! 👌\n", message,
                      "Solvency message should alert about correct funds but does not!")

    @patch('jobs.thornodes_jobs.get_network_security_ratio')
    def test_check_network_security(self, mock_get_network_security_ratio):
        mock_get_network_security_ratio.return_value = 0.66
        network_security_message = check_network_security(self.context)
        self.assertIs(network_security_message, None, "Can not trigger comparison difference. No previous value")

        mock_get_network_security_ratio.return_value = 0.66
        network_security_message = check_network_security(self.context)
        self.assertIs(network_security_message, None, "Network is optimal, but an warning is raised")

        mock_get_network_security_ratio.return_value = 0.80
        network_security_message = check_network_security(self.context)
        self.assertIn(network_security_message, NETWORK_HEALTH_WARNING(NetworkHealthStatus.OVERBONDED),
                      "Network state should have changed to OVERBONDED")

        mock_get_network_security_ratio.return_value = 0.7
        network_security_message = check_network_security(self.context)
        self.assertIn(network_security_message, NETWORK_HEALTHY_AGAIN,
                      "Network state should have changed back to OPTIMAL again")

        mock_get_network_security_ratio.return_value = 0.91
        network_security_message = check_network_security(self.context)
        self.assertIn(network_security_message, NETWORK_HEALTH_WARNING(NetworkHealthStatus.INEFFICIENT),
                      "Network state should have changed to INEFFICIENT")

        mock_get_network_security_ratio.return_value = 0.3
        network_security_message = check_network_security(self.context)
        self.assertIn(network_security_message, NETWORK_HEALTH_WARNING(NetworkHealthStatus.INSECURE),
                      "Network state should have changed to INSECURE")

        mock_get_network_security_ratio.return_value = 0.5
        network_security_message = check_network_security(self.context)
        self.assertIn(network_security_message, NETWORK_HEALTH_WARNING(NetworkHealthStatus.UNDBERBONDED),
                      "Network state should have changed to UNDBERBONDED")

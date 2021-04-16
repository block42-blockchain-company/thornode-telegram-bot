import copy
import unittest
from unittest.mock import Mock, patch

from constants.messages import get_network_health_warning, NETWORK_HEALTHY_AGAIN, NetworkHealthStatus
from jobs.other_nodes_jobs import *
from jobs.thorchain_network_jobs import check_network_security, check_thorchain_constants
from jobs.other_nodes_jobs import check_health
from jobs.thorchain_node_jobs import check_solvency, check_churning
from models.nodes import Node, UnauthorizedException
from helpers import network_data


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

    @patch('jobs.thorchain_node_jobs.yggdrasil_solvency_check')
    @patch('jobs.thorchain_node_jobs.asgard_solvency_check')
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

    @patch('jobs.thorchain_network_jobs.get_network_data')
    @patch('jobs.thorchain_network_jobs.get_network_security_ratio')
    def test_check_network_security(self, mock_get_network_security_ratio, mock_get_network_data):
        mock_get_network_security_ratio.return_value = 0.66
        mock_get_network_data.return_value = "network_data"

        network_security_message = check_network_security(self.context)
        self.assertIs(network_security_message, None,
                      "Can not trigger comparison difference. No previous value")

        mock_get_network_security_ratio.return_value = 0.66
        network_security_message = check_network_security(self.context)
        self.assertIs(network_security_message, None,
                      "Network is optimal, but an warning is raised")

        mock_get_network_security_ratio.return_value = 0.8
        network_security_message = check_network_security(self.context)
        self.assertIn(get_network_health_warning(NetworkHealthStatus.OVERBONDED), network_security_message,
                      "Network state should have changed to OVERBONDED")

        mock_get_network_security_ratio.return_value = 0.8
        network_security_message = check_network_security(self.context)
        self.assertIs(network_security_message, None,
                      "Network health state did not change but user was notified")

        mock_get_network_security_ratio.return_value = 0.7
        network_security_message = check_network_security(self.context)
        self.assertIn(network_security_message, NETWORK_HEALTHY_AGAIN,
                      "Network state should have changed back to OPTIMAL again")

        mock_get_network_security_ratio.return_value = 0.66
        network_security_message = check_network_security(self.context)
        self.assertIs(network_security_message, None,
                      "Network health state did not change but user was notified")

        mock_get_network_security_ratio.return_value = 0.91
        network_security_message = check_network_security(self.context)
        self.assertIn(network_security_message, get_network_health_warning(NetworkHealthStatus.INEFFICIENT),
                      "Network state should have changed to INEFFICIENT")

        mock_get_network_security_ratio.return_value = 0.3
        network_security_message = check_network_security(self.context)
        self.assertIn(network_security_message, get_network_health_warning(NetworkHealthStatus.INSECURE),
                      "Network state should have changed to INSECURE")

        mock_get_network_security_ratio.return_value = 0.5
        network_security_message = check_network_security(self.context)
        self.assertIn(network_security_message, get_network_health_warning(NetworkHealthStatus.UNDBERBONDED),
                      "Network state should have changed to UNDBERBONDED")

    @patch('jobs.thorchain_network_jobs.get_thorchain_network_constants')
    def test_network_constants_job(self, mock_get_thorchain_network_constants):

        constants_payload = {
                "int_64_values": {
                    "BadValidatorRate": 17280,
                    "BlocksPerYear": 6311390,
                    "ObserveFlex": 5,
                    "ObserveSlashPoints": 3,
                    "ValidatorRotateOutNumBeforeFull": 2,
                    "WhiteListGasAsset": 1000,
                    "YggFundLimit": 50
                },
                "bool_values": {
                    "StrictBondStakeRatio": False
                },
                "string_values": {
                    "DefaultPoolStatus": "Bootstrap"
                }
        }

        mock_get_thorchain_network_constants.return_value = constants_payload

        changed_values = check_thorchain_constants(self.context)
        self.assertIs(changed_values, None,
                      "First value entered. Can not have conflict with previous.")

        changed_values = check_thorchain_constants(self.context)
        self.assertIs(changed_values, None,
                      "Same constanstants returned as previous. There should not be a difference")

        new_constants_payload = copy.deepcopy(constants_payload)

        new_constants_payload["int_64_values"]["ValidatorRotateOutNumBeforeFull"] = 1
        new_constants_payload["bool_values"]["StrictBondStakeRatio"] = True
        mock_get_thorchain_network_constants.return_value = new_constants_payload

        changed_values = check_thorchain_constants(self.context)
        self.assertIn("Global Network Constants Change 📢:", changed_values,
                      "Title missing")

        self.assertIn("ValidatorRotateOutNumBeforeFull has changed from 2 to 1", changed_values,
                      "ValidatorRotateOutNumBeforeFull changes not detected")

        self.assertIn("StrictBondStakeRatio has changed from False to True", changed_values,
                      "StrictBondStakeRatio changes not detected")

        changed_values = check_thorchain_constants(self.context)
        self.assertIs(changed_values, None, "Nothing has changed, no changes should appear")

        another_new_constants_payload = copy.deepcopy(new_constants_payload)
        another_new_constants_payload["int_64_values"].pop("YggFundLimit")
        another_new_constants_payload["bool_values"]["NewRandomGlobalConstant"] = True
        mock_get_thorchain_network_constants.return_value = another_new_constants_payload

        changed_values = check_thorchain_constants(self.context)
        self.assertIn("YggFundLimit has been removed", changed_values, "YggFundLimit removal was not detected")
        self.assertIn("NewRandomGlobalConstant with value True has been added", changed_values,
                      "NewRandomGlobalConstant was not detected")

    @patch('jobs.thorchain_node_jobs.try_message_to_all_users')
    @patch('jobs.thorchain_node_jobs.get_node_accounts')
    @patch('jobs.thorchain_node_jobs.get_network_data')
    @patch('jobs.thorchain_node_jobs.get_pool_addresses_from_any_node')
    def test_check_churning(self, mock_get_pool_addresses_from_any_node, mock_get_network_data,
                            mock_get_node_accounts, mock_try_message_to_all_users):
        mock_get_node_accounts.return_value = [{
            'node_address': "127.0.0.1",
            'status': 'standby',
            'status_since': '123',
            'bond': '100'
        }]
        mock_get_network_data.return_value = {
            'bondMetrics': {
                'totalActiveBond': '10'
            },
            'totalStaked': '100',
            'bondingAPY': '100.01',
            'liquidityAPY': '99.01'
        }
        mock_get_pool_addresses_from_any_node.return_value = {
            "current": [
                {
                    "chain": "BNB",
                    "pub_key": "tthor16lvssqsnzt6gd38v6t8sjym3xmln3563tk36at",
                    "address": "bnb1mghkd903p06fdxvm7l3pj5284sneck03gqh78r"
                }
            ]
        }

        # first call: no churning, just initializing
        check_churning(self.context)

        # second call: churning first time
        mock_get_node_accounts.return_value[0]['status'] = 'active'
        check_churning(self.context)
        # assert that address did not change -> no output for new address / old address
        mock_try_message_to_all_users.assert_called_with(self.context,
                                                         text="🔄 CHURN SUMMARY\nTHORChain has successfully churned:\n\nNodes Added:\n*127.0.0.1*\nBond: *0.0000 RUNE*\n\nSystem:\n📡 Network Security: *NetworkHealthStatus.INSECURE*\n\n💚 Total Active Bond: *0.0000 RUNE* (total)\n\n⚖️ Bonded/Staked Ratio: *9.00 %*\n\n↩️ Bonding ROI: *10001.00 %* APY\n\n↩️ Liquidity ROI: *9901.00 %* APY")

        # third call: churning out
        mock_get_node_accounts.return_value[0]['status'] = 'standby'
        check_churning(self.context)
        # assert churning out text (check for: Nodes Removed:)
        mock_try_message_to_all_users.assert_called_with(self.context,
                                                         text="🔄 CHURN SUMMARY\nTHORChain has successfully churned:\n\n\nNodes Removed:\n*127.0.0.1*\nBond: *0.0000 RUNE*\n\nSystem:\n📡 Network Security: *NetworkHealthStatus.INSECURE*\n\n💚 Total Active Bond: *0.0000 RUNE* (total)\n\n⚖️ Bonded/Staked Ratio: *9.00 %*\n\n↩️ Bonding ROI: *10001.00 %* APY\n\n↩️ Liquidity ROI: *9901.00 %* APY\n\n⚠️ 🚨 CHURNING BUT THE VAULT ADDRESSES DID NOT CHANGE 🚨\n")

        # fourth call: churning in / address changed
        mock_get_node_accounts.return_value[0]['status'] = 'active'
        mock_get_pool_addresses_from_any_node.return_value['current'][0]['address'] = 'CHANGED-Address'
        check_churning(self.context)
        # assert churning in text (check for: Nodes Added, New Vault Address / Old Vault Address)
        mock_try_message_to_all_users.assert_called_with(self.context,
                                                         text="🔄 CHURN SUMMARY\nTHORChain has successfully churned:\n\nNodes Added:\n*127.0.0.1*\nBond: *0.0000 RUNE*\n\nSystem:\n📡 Network Security: *NetworkHealthStatus.INSECURE*\n\n💚 Total Active Bond: *0.0000 RUNE* (total)\n\n⚖️ Bonded/Staked Ratio: *9.00 %*\n\n↩️ Bonding ROI: *10001.00 %* APY\n\n↩️ Liquidity ROI: *9901.00 %* APY\n\n🔐 Vault Addresses:\n*BNB*: \nOld Vault address: bnb1mghkd903p06fdxvm7l3pj5284sneck03gqh78r\n⬇️\nNew Vault address: CHANGED-Address\n")

        #churning out
        mock_get_node_accounts.return_value[0]['status'] = 'standby'
        check_churning(self.context)
        # assert churning out text (check for: Nodes Removed:)
        mock_try_message_to_all_users.assert_called_with(self.context,
                                                         text="🔄 CHURN SUMMARY\nTHORChain has successfully churned:\n\n\nNodes Removed:\n*127.0.0.1*\nBond: *0.0000 RUNE*\n\nSystem:\n📡 Network Security: *NetworkHealthStatus.INSECURE*\n\n💚 Total Active Bond: *0.0000 RUNE* (total)\n\n⚖️ Bonded/Staked Ratio: *9.00 %*\n\n↩️ Bonding ROI: *10001.00 %* APY\n\n↩️ Liquidity ROI: *9901.00 %* APY\n\n⚠️ 🚨 CHURNING BUT THE VAULT ADDRESSES DID NOT CHANGE 🚨\n")

        # churning in with same address - assert warning
        mock_get_node_accounts.return_value[0]['status'] = 'active'
        check_churning(self.context)
        # assert churning in text with warning (check for: Nodes Added, warning because address did not change)
        mock_try_message_to_all_users.assert_called_with(self.context,
                                                         text="🔄 CHURN SUMMARY\nTHORChain has successfully churned:\n\nNodes Added:\n*127.0.0.1*\nBond: *0.0000 RUNE*\n\nSystem:\n📡 Network Security: *NetworkHealthStatus.INSECURE*\n\n💚 Total Active Bond: *0.0000 RUNE* (total)\n\n⚖️ Bonded/Staked Ratio: *9.00 %*\n\n↩️ Bonding ROI: *10001.00 %* APY\n\n↩️ Liquidity ROI: *9901.00 %* APY\n\n⚠️ 🚨 CHURNING BUT THE VAULT ADDRESSES DID NOT CHANGE 🚨\n")

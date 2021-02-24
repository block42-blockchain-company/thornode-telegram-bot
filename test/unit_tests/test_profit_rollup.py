import unittest
from unittest.mock import patch

from service.thorchain_network_service import get_profit_roll_up_stats
from helpers import churn_cycles_mock_day, churn_cycles_mock_day


class ProfitRollupTests(unittest.TestCase):

    @patch('service.thorchain_network_service.get_churn_cycles_with_node')
    @patch('service.utils.get_latest_block_height')
    def test_calculate_profit_rollup(self, mock_get_latest_block_height, mock_get_churn_cycles_with_node,
                                     churn_cycles_mock_day=None):
        mock_get_latest_block_height.return_value = 500000

        mock_get_churn_cycles_with_node.side_effect = \
            [churn_cycles_mock_day, churn_cycles_mock_week, churn_cycles_mock_month, churn_cycles_mock_overall]
        print(churn_cycles_mock)

        profit_rollup = get_profit_roll_up_stats("thor18md2p592zdkn440rfd3y5c26jencsryql75kep")
        print(profit_rollup)

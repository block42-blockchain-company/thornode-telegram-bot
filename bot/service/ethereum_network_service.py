from constants.globals import DEBUG
from constants.mock_values import eth_is_syncing_mock, eth_last_block_mock, eth_node_healthy_mock
from service.general_network_service import eth_rpc_request


def is_ethereum_node_fully_synced(self) -> bool:
    if DEBUG:
        return not eth_is_syncing_mock

    is_syncing = eth_rpc_request(self.node_ip, method="eth_syncing").json()['result']

    return not is_syncing


def get_ethereum_node_block_height(self):
    if DEBUG:
        global eth_last_block_mock
        eth_last_block_mock += 1
        return eth_last_block_mock

    return int(eth_rpc_request(self.node_ip, method="eth_blockNumber").json()['result'], 16)


def is_healthy(self) -> bool:
    if DEBUG:
        return eth_node_healthy_mock

    return eth_rpc_request(ip=self.node_ip, method="eth_protocolVersion").ok


def get_ethereum_network_block_count(self):
    if DEBUG:
        return eth_last_block_mock

    syncing = eth_rpc_request(ip=self.node_ip, method="eth_syncing").json()['result']

    if not syncing:
        return self.get_block_height()
    else:
        return int(syncing['highestBlock'], 16)

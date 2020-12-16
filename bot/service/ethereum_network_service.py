from constants.globals import DEBUG
from constants.mock_values import *
from service.general_network_service import eth_rpc_request


def is_eth_node_fully_synced(node_ip) -> bool:
    if DEBUG:
        return not eth_is_syncing_mock

    is_syncing = eth_rpc_request(node_ip, method="eth_syncing").json()['result']

    return not is_syncing


def get_eth_node_block_height(node_ip):
    if DEBUG:
        global eth_last_block_mock
        eth_last_block_mock += 1
        return eth_last_block_mock

    return int(eth_rpc_request(node_ip, method="eth_blockNumber").json()['result'], 16)


def is_eth_node_healthy(node_ip) -> bool:
    if DEBUG:
        return eth_node_healthy_mock

    return eth_rpc_request(ip=node_ip, method="eth_protocolVersion").ok


def get_eth_network_block_count(node_ip):
    if DEBUG:
        return eth_last_block_mock

    syncing = eth_rpc_request(ip=node_ip, method="eth_syncing").json()['result']

    if not syncing:
        return get_eth_node_block_height(node_ip)
    else:
        return int(syncing['highestBlock'], 16)

from constants.globals import logger, DEBUG
from constants.mock_values import *
from constants.node_ips import BINANCE_DEX_ENDPOINT
from service.general_network_service import get_request_json, get_request_json_with_retries


def get_binance_balance(address: str) -> dict:
    return get_request_json_with_retries(url=f"{BINANCE_DEX_ENDPOINT}/api/v1/account/{address}")['balances']


def get_binance_network_block_count() -> dict:
    res = get_request_json_with_retries(url=f"{BINANCE_DEX_ENDPOINT}/api/v1/node-info")

    return res['sync_info']['latest_block_height']


def is_binance_node_syncing(binance_node_ip) -> bool:
    if DEBUG:
        return binance_is_syncing_mock

    status = get_request_json(url=f"http://{binance_node_ip}/status")
    is_catching_up = status['sync_info']['catching_up']

    if is_catching_up:
        return True
    else:
        return False


def get_binance_node_block_height(binance_node_ip):
    if DEBUG:
        global binance_last_block_mock
        binance_last_block_mock += 1
        return binance_last_block_mock

    status = get_request_json(url=f"http://{binance_node_ip}/status")

    return status['result']['sync_info']['latest_block_height']


def is_binance_node_healthy(binance_node_ip) -> bool:
    if DEBUG:
        return binance_node_healthy_mock

    try:
        get_request_json(url=f"http://{binance_node_ip}/health")
    except Exception as e:
        logger.exception(e)
        return False

    return True

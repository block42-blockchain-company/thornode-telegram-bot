import random

import aiohttp
import requests

from constants import *


def get_node_accounts():
    url = ":8080/nodeaccounts.json" if DEBUG else ":1317/thorchain/nodeaccounts"
    return get_request_json_thorchain(url_path=url)


def get_node_status(node_ip=None):
    status_path = {
        "TESTNET": ":26657/status",
        "CHAOSNET": ":27147/status"
    }[NETWORK_TYPE]

    return get_request_json_thorchain(url_path=status_path, node_ip=node_ip)


def get_latest_block_height(node_ip=None) -> str:
    return str(get_node_status(node_ip)['result']['sync_info']['latest_block_height'])


def is_thorchain_catching_up(node_ip=None) -> bool:
    return get_node_status(node_ip)['result']['sync_info']['catching_up']


def is_midgard_api_healthy(node_ip) -> bool:
    try:
        get_request_json(url=f"http://{node_ip}:8080/v1/health")
    except Exception as e:
        logger.exception(e)
        return False

    return True


def get_number_of_unconfirmed_transactions(node_ip) -> int:
    unconfirmed_txs_path = {
        "TESTNET": ":26657/num_unconfirmed_txs",
        "CHAOSNET": ":27147/num_unconfirmed_txs"
    }[NETWORK_TYPE]
    url = f"http://{node_ip}{unconfirmed_txs_path}"

    return int(get_request_json(url=url)['result']['total'])


def get_network_data(node_ip=None):
    return get_request_json_thorchain(url_path=f":8080/v1/network", node_ip=node_ip)


def is_binance_node_healthy(binance_node_ip) -> bool:
    health_path = {
        "TESTNET": ":26657/health",
        "CHAOSNET": ":27147/health"
    }[NETWORK_TYPE]

    try:
        get_request_json(url=f"http://{binance_node_ip}{health_path}")
    except Exception as e:
        logger.exception(e)
        return False

    return True


def get_thorchain_blocks_per_year(node_ip=None):
    constants = get_request_json_thorchain(url_path=f":8080/v1/thorchain/constants", node_ip=node_ip)
    return constants['int_64_values']['BlocksPerYear']


def get_asgard_json() -> dict:
    url = ':8080/asgard.json' if DEBUG else f":1317/thorchain/vaults/asgard"
    return get_request_json_thorchain(url_path=url)


def get_yggdrasil_json() -> dict:
    url = ":8080/yggdrasil.json" if DEBUG else ":1317/thorchain/vaults/yggdrasil"
    return get_request_json_thorchain(url_path=url)


def get_binance_balance(address: str) -> dict:
    return get_request_json(url=f"{BINANCE_DEX_ENDPOINT}/api/v1/account/{address}")['balances']


async def get_pool_addresses(node_ip: str):
    async with aiohttp.ClientSession() as session:
        async with session.get(
                f'http://{node_ip}:8080/v1/thorchain/pool_addresses',
                timeout=CONNECTION_TIMEOUT) as response:
            if response.status != 200:
                raise Exception(
                    f"Error while getting pool address. " +
                    "Endpoint responded with: {await resp.text()} \n"
                    "Code: ${str(resp.status)}")

            return await response.json()


def get_request_json(url: str) -> dict:
    response = requests.get(url=url, timeout=CONNECTION_TIMEOUT)

    if response.status_code != 200:
        raise BadStatusException(response)

    return response.json()


def get_request_json_thorchain(url_path: str, node_ip: str=None) -> dict:
    if DEBUG:
        node_ip = 'localhost'

    if node_ip:
        return get_request_json(url=f"http://{node_ip}{url_path}")

    seeding_node_url = \
        {"TESTNET": "https://testnet-seed.thorchain.info", "CHAOSNET": "https://chaosnet-seed.thorchain.info"}[
            NETWORK_TYPE]

    available_node_ips = requests.get(url=seeding_node_url, timeout=CONNECTION_TIMEOUT).json()

    random.shuffle(available_node_ips)
    for random_node_ip in available_node_ips:
        try:
            return get_request_json(url=f"http://{random_node_ip}{url_path}")
        except Exception:
            continue
    raise Exception("No seed node returned a valid response!")


class BadStatusException(Exception):

    def __init__(self, response: requests.Response):
        self.message = f"Error while network request.\n" \
                       f"Received status code: {str(response.status_code)}\n" \
                       f"Received response: {response.text}"

    def __str__(self):
        return self.message

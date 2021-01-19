import random
from time import sleep

import aiohttp
import requests
from requests.exceptions import Timeout, ConnectionError

from constants.mock_values import thorchain_last_block_mock
from service.general_network_service import get_request_json
from constants.globals import *
from constants.node_ips import *


def get_node_accounts():
    path = ":8080/nodeaccounts.json" if DEBUG else ":1317/thorchain/nodeaccounts"
    return get_request_json_thorchain(url_path=path)


def get_node_status(node_ip=None):
    status_path = {
        "TESTNET": ":26657/status",
        "CHAOSNET": ":27147/status"
    }[NETWORK_TYPE]

    return get_request_json_thorchain(url_path=status_path, node_ip=node_ip)


def get_latest_block_height(node_ip=None) -> int:
    return int(get_node_status(node_ip)['result']['sync_info']['latest_block_height'])


def is_thorchain_catching_up(node_ip=None) -> bool:
    return get_node_status(node_ip)['result']['sync_info']['catching_up']


def is_midgard_api_healthy(node_ip) -> bool:
    try:
        get_request_json_thorchain(url_path=":8080/v1/health", node_ip=node_ip)
    except (Timeout, ConnectionError):
        logger.warning(f"Timeout or Connection error with {node_ip}")
        return False
    except Exception as e:
        if len(e.args) > 0 and "status_code" in e.args[0] and e.args[0].status_code == 502:
            logger.info(f"Bad Status Request (status code 502) in 'is_midgard_api_healthy(node_ip)' with {node_ip}")
        else:
            logger.exception(e)
        return False

    return True


def get_number_of_unconfirmed_transactions(node_ip) -> int:
    unconfirmed_txs_path = {
        "TESTNET": ":26657/num_unconfirmed_txs",
        "CHAOSNET": ":27147/num_unconfirmed_txs"
    }[NETWORK_TYPE]
    return int(get_request_json_thorchain(url_path=unconfirmed_txs_path, node_ip=node_ip)['result']['total'])


def get_network_data(node_ip=None):
    return get_request_json_thorchain(url_path=f":8080/v1/network", node_ip=node_ip)


def get_thorchain_network_constants(node_ip=None):
    return get_request_json_thorchain(url_path=f":8080/v1/thorchain/constants")


def get_thorchain_blocks_per_year(node_ip=None):
    constants = get_thorchain_network_constants()
    return constants['int_64_values']['BlocksPerYear']


def get_thorchain_blocks_per_second():
    return get_thorchain_blocks_per_year() / (365 * 24 * 60 * 60)


def get_thorchain_last_block(node_ip=None):
    if DEBUG:
        sleep(0.5)
        last_block = thorchain_last_block_mock
    else:
        last_block = get_request_json_thorchain(url_path=f":8080/v1/thorchain/lastblock", node_ip=node_ip)

    return last_block['thorchain']


def get_asgard_json() -> dict:
    path = ':8080/asgard.json' if DEBUG else f":1317/thorchain/vaults/asgard"
    return get_request_json_thorchain(url_path=path)


def get_yggdrasil_json() -> dict:
    path = ":8080/yggdrasil.json" if DEBUG else ":1317/thorchain/vaults/yggdrasil"
    return get_request_json_thorchain(url_path=path)


def get_pool_addresses_from_single_node() -> dict:
    path = ":8080/pool_addresses_1.json" if DEBUG else ":8080/v1/thorchain/pool_addresses"
    return get_request_json_thorchain(path)


async def get_pool_addresses_from_all_node(node_ip: str):
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


def get_request_json_thorchain(url_path: str, node_ip: str = None) -> dict:
    if DEBUG:
        node_ip = 'localhost'

    if node_ip:
        return get_request_json(url=f"http://{node_ip}{url_path}{REQUEST_POSTFIX}")

    seeding_node_url = \
        {"TESTNET": "https://testnet-seed.thorchain.info", "CHAOSNET": "https://chaosnet-seed.thorchain.info"}[
            NETWORK_TYPE]

    available_node_ips = requests.get(url=seeding_node_url, timeout=CONNECTION_TIMEOUT).json()

    random.shuffle(available_node_ips)
    for random_node_ip in available_node_ips:
        try:
            return get_request_json(url=f"http://{random_node_ip}{url_path}{REQUEST_POSTFIX}")
        except Exception:
            continue
    raise Exception("No seed node returned a valid response!")


def get_thornode_object_or_none(address):
    nodes = get_node_accounts()

    node = next(filter(lambda n: n['node_address'] == address, nodes), None)

    return node

import random

import aiohttp
import requests

from constants import *


def get_node_accounts():
    if DEBUG:
        url = 'http://localhost:8080/nodeaccounts.json'
    else:
        url = 'http://' + get_random_seed_node_endpoint(
        ) + ':1317/thorchain/nodeaccounts'

    validators_response = requests.get(url=url, timeout=CONNECTION_TIMEOUT)

    if validators_response.status_code != 200:
        raise BadStatusException(validators_response)

    return validators_response.json()


def get_node_status(node_ip=None):
    if node_ip is None:
        node_ip = get_random_seed_node_endpoint()

    status_path = {
        "TESTNET": ":26657/status",
        "CHAOSNET": ":27147/status"
    }[NETWORK_TYPE]

    status_response = requests.get(url='http://' + node_ip + status_path,
                                   timeout=CONNECTION_TIMEOUT)

    if status_response.status_code != 200:
        raise BadStatusException(status_response)

    return status_response.json()


def get_latest_block_height(node_ip=None) -> str:
    return str(
        get_node_status(node_ip)['result']['sync_info']['latest_block_height'])


def is_thorchain_catching_up(node_ip=None) -> bool:
    return get_node_status(node_ip)['result']['sync_info']['catching_up']


def is_midgard_api_healthy(node_ip) -> bool:
    try:
        midgard_health_response = requests.get(url='http://' + node_ip +
                                               ':8080/v1/health',
                                               timeout=CONNECTION_TIMEOUT)
    except Exception as e:
        logger.exception(e)
        return False

    return midgard_health_response.status_code == 200


def get_number_of_unconfirmed_transactions(node_ip) -> int:
    unconfirmed_txs_path = {
        "TESTNET": ":26657/num_unconfirmed_txs",
        "CHAOSNET": ":27147/num_unconfirmed_txs"
    }[NETWORK_TYPE]
    url = 'http://' + node_ip + unconfirmed_txs_path

    transactions_data_response = requests.get(url=url,
                                              timeout=CONNECTION_TIMEOUT)

    if transactions_data_response.status_code != 200:
        raise BadStatusException(transactions_data_response)

    return int(transactions_data_response.json()['result']['total'])


def get_random_seed_node_endpoint() -> str:
    if DEBUG:
        return 'localhost'

    seeding_node_url = \
        {"TESTNET": "https://testnet-seed.thorchain.info", "CHAOSNET": "https://chaosnet-seed.thorchain.info"}[
            NETWORK_TYPE]

    available_node_ips = requests.get(url=seeding_node_url,
                                      timeout=CONNECTION_TIMEOUT).json()

    random.shuffle(available_node_ips)
    response = None
    for node_ip in available_node_ips:
        try:
            response = requests.get(url='http://' + node_ip + ':8080/v1/health',
                                    timeout=10)
        except Exception as e:
            logger.exception(e)
            continue
        if response.status_code == 200:
            return node_ip
    raise BadStatusException(response)


def get_network_data(node_ip=None):
    if node_ip is None:
        node_ip = get_random_seed_node_endpoint()

    network_data_response = requests.get(url='http://' + node_ip +
                                         ':8080/v1/network',
                                         timeout=CONNECTION_TIMEOUT)

    if network_data_response.status_code != 200:
        raise BadStatusException(network_data_response)

    return network_data_response.json()


def is_binance_node_healthy(binance_node_ip) -> bool:
    health_path = {
        "TESTNET": ":26657/health",
        "CHAOSNET": ":27147/health"
    }[NETWORK_TYPE]

    try:
        health_response = requests.get(url='http://' + binance_node_ip +
                                       health_path,
                                       timeout=CONNECTION_TIMEOUT)
    except Exception as e:
        logger.exception(e)
        return False

    return health_response.status_code == 200


def get_thorchain_blocks_per_year(node_ip=None):
    if node_ip is None:
        node_ip = get_random_seed_node_endpoint()

    constants_response = requests.get(url='http://' + node_ip +
                                      ':8080/v1/thorchain/constants',
                                      timeout=CONNECTION_TIMEOUT)

    if constants_response.status_code != 200:
        raise BadStatusException(constants_response)

    return constants_response.json()['int_64_values']['BlocksPerYear']


async def get_pool_addresses(node_ip: str):
    async with aiohttp.ClientSession() as session:
        async with session.get(
                f'http://{node_ip}:8080/v1/thorchain/pool_addresses',
                timeout=CONNECTION_TIMEOUT) as resp:
            if resp.status != 200:
                raise Exception(
                    f"Error while getting pool address. " +
                    "Endpoint responded with: {await resp.text()} \n"
                    "Code: ${str(resp.status)}")

            return await resp.json()


class BadStatusException(Exception):

    def __init__(self, response: requests.Response):
        self.message = "Error while network request.\nReceived status code: " + \
                       str(response.status_code) + '\nReceived response: ' + response.text

    def __str__(self):
        return self.message

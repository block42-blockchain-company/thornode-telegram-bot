import random

import requests

from bot.constants import DEBUG, logger, BINANCE_NODE_IP


def get_node_accounts():
    if DEBUG:
        url = 'http://localhost:8080/nodeaccounts.json'
    else:
        url = 'http://' + get_random_seed_node_endpoint() + ':1317/thorchain/nodeaccounts'

    validators_response = requests.get(url=url)

    if validators_response.status_code != 200:
        raise BadStatusException(validators_response)

    return validators_response.json()


def get_node_status(node_ip=None):
    if node_ip is None:
        node_ip = get_random_seed_node_endpoint()

    status_response = requests.get(url='http://' + node_ip + ':26657/status')

    if status_response.status_code != 200:
        raise BadStatusException(status_response)

    return status_response.json()


def get_latest_block_height(node_ip=None) -> str:
    return str(get_node_status(node_ip)['result']['sync_info']['latest_block_height'])


def is_thorchain_catching_up(node_ip=None) -> bool:
    return get_node_status(node_ip)['result']['sync_info']['catching_up']


def is_midgard_api_healthy(node_ip) -> bool:
    try:
        midgard_health_response = requests.get(url='http://' + node_ip + ':8080/v1/health')
    except Exception as e:
        logger.exception(e)
        return False

    return midgard_health_response.status_code == 200


def get_number_of_unconfirmed_transactions(node_ip) -> int:
    url = 'http://' + node_ip + ':26657/num_unconfirmed_txs'

    transactions_data_response = requests.get(url=url)

    if transactions_data_response.status_code != 200:
        raise BadStatusException(transactions_data_response)

    return int(transactions_data_response.json()['result']['total'])


def get_random_seed_node_endpoint() -> str:
    seeding_node_url = 'https://testnet-seed.thorchain.info'  # todo: from .env

    available_node_ips = requests.get(seeding_node_url).json()

    return random.choice(available_node_ips)


def get_network_data(node_ip=None):
    if node_ip is None:
        node_ip = get_random_seed_node_endpoint()

    network_data_response = requests.get(url='http://' + node_ip + ':8080/v1/network')

    if network_data_response.status_code != 200:
        raise BadStatusException(network_data_response)

    return network_data_response.json()


def is_binance_node_healthy() -> bool:
    try:
        health_response = requests.get(url='http://' + BINANCE_NODE_IP + ':26657/health')
    except Exception as e:
        logger.exception(e)
        return False

    return health_response.status_code == 200


def get_thorchain_blocks_per_year(node_ip=None):
    if node_ip is None:
        node_ip = get_random_seed_node_endpoint()

    constants_response = requests.get(url='http://' + node_ip + ':8080/v1/thorchain/constants')

    if constants_response.status_code != 200:
        raise BadStatusException(constants_response)

    return constants_response.json()['int_64_values']['BlocksPerYear']


class BadStatusException(Exception):
    def __init__(self, response: requests.Response):
        self.message = "Error while network request.\nReceived status code: " + \
                       str(response.status_code) + '\nReceived response: ' + response.text

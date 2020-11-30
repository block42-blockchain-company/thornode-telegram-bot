import asyncio
from collections import defaultdict
from datetime import datetime, timedelta
from typing import Callable, Awaitable

from service.thorchain_network_service import *


async def for_each_async(elements: [], function: Callable[...,
                                                          Awaitable[None]]):
    tasks = []
    for element in elements:
        tasks.append(function(element))

    await asyncio.gather(*tasks)


def btc_rpc_request(address: str, method: str, params=None):
    return rpc_request(url=f'http://{address}', jsonrpc_version="1.0", method=method,
                       params=params)


def eth_rpc_request(ip: str, method: str, params=None):
    return rpc_request(url=f'http://{ip}:8545/', jsonrpc_version="2.0", method=method,
                       params=params)


def rpc_request(url: str, method: str, jsonrpc_version: str, params=None):
    if params is None:
        params = []
    json = {"jsonrpc": jsonrpc_version, "id": None, "method": method, "params": params}

    return requests.post(url, json=json)


def format_to_days_and_hours(duration: timedelta) -> str:
    result = ""
    hours = duration.seconds // 3600

    if duration.days > 0:
        result += str(duration.days)
        if duration.days == 1:
            result += ' day'
        else:
            result += " days"

        if hours > 0:
            result += " "

    if hours <= 0:
        if duration.days <= 0:
            result += "< 1 hour"
    else:
        result += str(hours)
        if hours == 1:
            result += ' hour'
        else:
            result += ' hours'

    return result


def asgard_solvency_check() -> dict:
    solvency_report = {'is_solvent': True}
    asgard_actual = defaultdict(lambda: {"json": {}})
    asgard_expected = get_asgard_json()
    pool_addresses = get_request_json_thorchain(url_path=':8080/v1/thorchain/pool_addresses')

    for chain_data in pool_addresses['current']:
        chain = chain_data['chain']
        if chain == 'BNB':
            asgard_actual[chain]['json'] = get_binance_balance(chain_data['address'])

    for chain_key, chain_value in asgard_actual.items():
        if chain_key == 'BNB':
            for balance in chain_value['json']:
                chain_value[balance['symbol']] = balance['free']

    for chain in asgard_expected:
        if chain['status'] == 'active':
            for coin in chain['coins']:
                asset = coin['asset'].split('.')
                actual_amount_formatted = (asgard_actual.get(asset[0]).
                                           setdefault(asset[1], "0").replace(".", ""))
                expected_amount_formatted = (coin['amount'].replace(".", ""))
                if int(actual_amount_formatted) < int(expected_amount_formatted):
                    solvency_report['is_solvent'] = False
                    if 'insolvent_coins' not in solvency_report:
                        solvency_report['insolvent_coins'] = {}
                    solvency_report['insolvent_coins'][coin['asset']] = {
                        "expected": coin['amount'],
                        "actual": asgard_actual[asset[0]][asset[1]]
                    }
                else:
                    if 'solvent_coins' not in solvency_report:
                        solvency_report['solvent_coins'] = {}
                    solvency_report['solvent_coins'][coin['asset']] = asgard_actual[asset[0]][asset[1]]

    return solvency_report


def yggdrasil_check() -> dict:
    solvency_report = {'is_solvent': True}
    yggdrasil_actual = {}

    yggdrasil_expected = get_yggdrasil_json()
    for vault in yggdrasil_expected:
        if vault['status'] == 'active' and vault['vault']['status'] == 'active':
            for chain in vault['addresses']:
                if chain['chain'] == 'BNB':
                    public_key = vault['vault']['pub_key']
                    if public_key not in yggdrasil_actual:
                        yggdrasil_actual[public_key] = {}
                    if chain['chain'] not in yggdrasil_actual[public_key]:
                        yggdrasil_actual[public_key][chain['chain']] = {}
                    yggdrasil_actual[public_key][chain['chain']] = {"json": {}}
                    yggdrasil_actual[public_key][chain['chain']]['json'] = get_binance_balance(chain['address'])

    for vault in yggdrasil_actual:
        for chain_key, chain_value in yggdrasil_actual[vault].items():
            if chain_key == 'BNB':
                for balance in chain_value['json']:
                    chain_value[balance['symbol']] = balance['free']

    for vault in yggdrasil_expected:
        if vault['status'] == 'active' and vault['vault']['status'] == 'active':
            for coin in vault['vault']['coins']:
                asset = coin['asset'].split('.')
                actual_amount = (yggdrasil_actual[vault['vault']['pub_key']].get(asset[0]).setdefault(asset[1], "0")
                                 .replace(".", ""))
                expected_amount = (coin['amount'].replace(".", ""))
                if int(actual_amount) < int(expected_amount):
                    solvency_report['is_solvent'] = False
                    if 'insolvent_coins' not in solvency_report:
                        solvency_report['insolvent_coins'] = {}
                    if vault['vault']['pub_key'] not in solvency_report['insolvent_coins']:
                        solvency_report['insolvent_coins'][vault['vault']['pub_key']] = {}
                    solvency_report['insolvent_coins'][vault['vault']['pub_key']][coin['asset']] = \
                        {
                            "expected": coin['amount'],
                            "actual": yggdrasil_actual[vault['vault']['pub_key']][asset[0]][asset[1]]
                        }
                else:
                    if 'solvent_coins' not in solvency_report:
                        solvency_report['solvent_coins'] = {}
                    if coin['asset'] in solvency_report['solvent_coins']:
                        solvency_report['solvent_coins'][coin['asset']] += \
                            float(yggdrasil_actual[vault['vault']['pub_key']][asset[0]][asset[1]])
                    else:
                        solvency_report['solvent_coins'][coin['asset']] = \
                            float(yggdrasil_actual[vault['vault']['pub_key']][asset[0]][asset[1]])

    return solvency_report


def get_solvency_message(asgard_solvency, yggdrasil_solvency) -> str:
    message = "Tracked Balances of *Asgard*:\n"
    if 'insolvent_coins' in asgard_solvency:
        for coin_key, coin_value in asgard_solvency['insolvent_coins'].items():
            message += f"*{coin_key}*:\n" \
                       f"  Expected: {coin_value['expected']}\n" \
                       f"  Actual:   {coin_value['actual']}\n"

    if 'solvent_coins' in asgard_solvency:
        for coin_key, coin_value in asgard_solvency['solvent_coins'].items():
            message += f"*{coin_key}*: {coin_value}\n"

    message += "\nTracked Balances of *Yggdrasil*:\n"
    if 'insolvent_coins' in yggdrasil_solvency:
        for pub_key, coins in yggdrasil_solvency['insolvent_coins'].items():
            for coin_key, coin_value in coins.items():
                message += f"*{pub_key}*:\n" \
                           f"*{coin_key}*:\n" \
                           f"  Expected: {coin_value['expected']}\n" \
                           f"  Actual:   {coin_value['actual']}\n"

    if 'solvent_coins' in yggdrasil_solvency:
        for coin_key, coin_value in yggdrasil_solvency['solvent_coins'].items():
            message += f"*{coin_key}*: {coin_value}\n"

    return message


def network_security_ratio_to_string(network_security_ratio):
    """
    Converts the network security ratio to an understandable english string
    """

    if network_security_ratio > 0.9:
        network_security_string = "Inefficent"
    elif 0.9 >= network_security_ratio > 0.75:
        network_security_string = "Overbonded"
    elif 0.75 >= network_security_ratio >= 0.6:
        network_security_string = "Optimal"
    elif 0.6 > network_security_ratio >= 0.5:
        network_security_string = "Underbonded"
    else:
        network_security_string = "Insecure"

    return network_security_string


def get_network_security_ratio(network_json):
    """
    Returns network security as a ratio number
    """

    total_active_bond = int(network_json['bondMetrics']['totalActiveBond'])
    total_staked = int(network_json['totalStaked'])
    return total_active_bond / (total_active_bond + total_staked)


def tor_to_rune(tor):
    """
    1e8 Tor are 1 Rune
    Format depending if RUNE > or < Zero
    """

    # Cast to float first if string is float
    tor = int(float(tor))
    if tor == 0:
        return "0 RUNE"
    elif tor >= 100000000:
        return "{:,} RUNE".format(int(tor / 100000000))
    else:
        return '{:.4f} RUNE'.format(tor / 100000000)


def add_thornode_to_user_data(user_data, address, node):
    """
    Add a node in the user specific dictionary
    """

    # Find an alias that does not exist yet
    i = 0
    while True:
        i += 1
        alias = "Thor-" + str(i)
        if not next(
                filter(
                    lambda current_address: user_data['nodes'][current_address][
                                                'alias'] == alias, user_data['nodes']), None):
            break

    user_data['nodes'][address] = node
    user_data['nodes'][address]['alias'] = alias
    user_data['nodes'][address][
        'last_notification_timestamp'] = datetime.timestamp(datetime.now())
    user_data['nodes'][address][
        'notification_timeout_in_seconds'] = INITIAL_NOTIFICATION_TIMEOUT

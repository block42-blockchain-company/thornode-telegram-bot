import asyncio
import subprocess
import json
from collections import defaultdict
from typing import Callable, Awaitable

from telegram import InlineKeyboardButton, KeyboardButton, ReplyKeyboardMarkup, InlineKeyboardMarkup, TelegramError
from datetime import datetime, timedelta

from constants import *
from messages import NETWORK_ERROR_MSG
from service.thorchain_network_service import *


def try_message_with_home_menu(context, chat_id, text):
    keyboard = get_home_menu_buttons()
    try_message(context=context,
                chat_id=chat_id,
                text=text,
                reply_markup=ReplyKeyboardMarkup(keyboard,
                                                 resize_keyboard=True))


def try_message_to_all_users(context, text):
    for chat_id in context.dispatcher.user_data.keys():
        try_message_with_home_menu(context, chat_id=chat_id, text=text)


def get_home_menu_buttons():
    """
    Return keyboard buttons for the home menu
    """

    keyboard = [[
        KeyboardButton('📡 MY NODES', callback_data='thornode_menu'),
        KeyboardButton('🌎 NETWORK', callback_data='thornode_menu')
    ],
                [
                    KeyboardButton('👀 SHOW ALL',
                                   callback_data='show_all_thorchain_nodes'),
                    KeyboardButton('🔑 ADMIN AREA', callback_data='admin_menu')
                ]]

    return keyboard


def show_thornode_menu_new_msg(update, context):
    user_data = context.user_data if context.user_data else context.job.context[
        'user_data']

    keyboard = get_thornode_menu_buttons(user_data=user_data)
    text = 'Click an address from the list below or add a node:' if len(keyboard) > 2 else 'You do not monitor any ' \
                                                                                           'THORNodes yet.\nAdd a Node!'
    try_message(context=context,
                chat_id=update.effective_message.chat_id,
                text=text,
                reply_markup=InlineKeyboardMarkup(keyboard))


def get_thornode_menu_buttons(user_data):
    """
    Return keyboard buttons for the thornode menu
    """

    keyboard = [[]]

    for address in user_data['nodes'].keys():
        emoji = STATUS_EMOJIS[user_data['nodes'][address]['status']] \
            if user_data['nodes'][address]['status'] in STATUS_EMOJIS else STATUS_EMOJIS["unknown"]

        truncated_address = address[:9] + "..." + address[-4:]
        button_text = emoji + " " + user_data['nodes'][address][
            'alias'] + " (" + truncated_address + ")"
        keyboard.append([
            InlineKeyboardButton(button_text,
                                 callback_data='thornode_details-' + address)
        ])

    keyboard.append(
        [InlineKeyboardButton('1️⃣ ADD NODE', callback_data='add_thornode')])
    keyboard.append([
        InlineKeyboardButton('➕ ADD ALL',
                             callback_data='confirm_add_all_thornodes'),
        InlineKeyboardButton('➖ REMOVE ALL',
                             callback_data='confirm_delete_all_thornodes')
    ])

    return keyboard


def show_detail_menu(update, context):
    """
    Show detail buttons for selected address
    """

    query = update.callback_query
    address = context.user_data['selected_node_address']

    try:
        node = get_thornode_object_or_none(address=address)
    except Exception as e:
        logger.exception(e)
        query.edit_message_text(NETWORK_ERROR_MSG)
        show_thornode_menu_new_msg(update, context)
        return

    if node is None:
        text = 'THORNode ' + address + ' is not active anymore and will be removed shortly! 💀'
        query.edit_message_text(text)
        show_thornode_menu_new_msg(update, context)
        return

    text = 'THORNode: *' + context.user_data['nodes'][address]['alias'] + '*\n' + \
           'Address: *' + address + '*\n' + \
           'Version: *' + node['version'] + '*\n\n' + \
           'Status: *' + node['status'].capitalize() + '*\n' + \
           'Bond: *' + tor_to_rune(node['bond']) + '*\n' + \
           'Slash Points: ' + '*{:,}*'.format(int(node['slash_points'])) + '\n' + \
           'Accrued Rewards: *' + tor_to_rune(node['current_award']) + '*\n' + \
           'Status Since Block: ' + '*{:,}*'.format(int(node['status_since'])) + '\n'

    try:
        latest_block_height = get_latest_block_height()
        blocks_per_second = get_thorchain_blocks_per_second()
        status_since_in_seconds = (int(latest_block_height) - int(
            node['status_since'])) / blocks_per_second

        text += node['status'].capitalize() + ' for *' + \
                format_to_days_and_hours(timedelta(seconds=status_since_in_seconds)) + '*\n\n'
    except Exception as e:
        logger.exception(e)
        text += 'Currently I Can\'t get duration of this status. Try again later!\n\n'

    try:
        text += 'Number of Unconfirmed Transactions: '
        unconfirmed_txs = get_number_of_unconfirmed_transactions(
            node['ip_address'])
        text += '*{:,}*'.format(int(unconfirmed_txs)) + '\n\n'
    except Exception as e:
        logger.exception(e)
        text += 'Currently unavailable!\n\n'

    text += "What do you want to do with that Node?"

    keyboard = [[
        InlineKeyboardButton('➖ REMOVE',
                             callback_data='confirm_thornode_deletion'),
        InlineKeyboardButton('✏️ CHANGE ALIAS', callback_data='change_alias')
    ], [InlineKeyboardButton('⬅️ BACK', callback_data='thornode_menu')]]

    # Modify message
    query.edit_message_text(text,
                            parse_mode='markdown',
                            reply_markup=InlineKeyboardMarkup(keyboard))


def show_admin_menu_new_msg(context, chat_id):
    """
    Send a new message with the admin area
    """

    try:
        keyboard = get_admin_menu_buttons()
    except ProcessLookupError:
        text = "❌ Error while getting running docker container! ❌"
        try_message_with_home_menu(context=context, chat_id=chat_id, text=text)
        return

    # Send message
    text = "⚠️ You're in the Admin Area - proceed with care ⚠️\n" \
           "Below is a list of docker containers running on your system.\n" \
           "Click on any container to restart it!"

    try_message(context=context,
                chat_id=chat_id,
                text=text,
                reply_markup=InlineKeyboardMarkup(keyboard))


def get_admin_menu_buttons():
    """
    Return keyboard buttons for the admin menu
    """

    try:
        containers = get_running_docker_container()
    except ProcessLookupError:
        raise

    # build keyboard with one button for every container
    keyboard = [[]]
    for container in containers:
        for name in container['Names']:
            container_name = name.replace('/', '')
            status = container['Status']
            text = "🐳 " + container_name + " - " + status
            keyboard.append([
                InlineKeyboardButton(text,
                                     callback_data='container-#' +
                                     container_name)
            ])

    return keyboard


def show_text_input_message(update, text):
    """
    Initiate a conversation and prompt for user input.
    """

    # Enable message editing
    query = update.callback_query

    # Send message
    query.edit_message_text(text)


def try_message(context, chat_id, text, reply_markup=None):
    """
    Send a message to a user.
    """

    if context.job and not context.job.enabled:
        return

    try:
        context.bot.send_message(chat_id,
                                 text,
                                 parse_mode='markdown',
                                 reply_markup=reply_markup)
    except TelegramError as e:
        if 'bot was blocked by the user' in e.message:
            print("Telegram user " + str(chat_id) +
                  " blocked me; removing him from the user list")
            del context.dispatcher.user_data[chat_id]
            del context.dispatcher.chat_data[chat_id]
            del context.dispatcher.persistence.user_data[chat_id]
            del context.dispatcher.persistence.chat_data[chat_id]

            # Somehow session.data does not get updated if all users block the bot.
            # That makes problems on bot restart. That's why we delete the file ourselves.
            if len(context.dispatcher.persistence.user_data) == 0:
                if os.path.exists(session_data_path):
                    os.remove(session_data_path)
            context.job.enabled = False
            context.job.schedule_removal()
        else:
            print("Got Error\n" + str(e) + "\nwith telegram user " +
                  str(chat_id))


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


def show_confirmation_menu(update, text, keyboard):
    """
    "Are you sure?" - "YES" | "NO"
    """

    query = update.callback_query

    query.edit_message_text(text,
                            parse_mode='markdown',
                            reply_markup=InlineKeyboardMarkup(keyboard))


def get_running_docker_container():
    """
    Return Json of all running container on the host machine
    """

    bash_command = DOCKER_CURL_CMD + " http://localhost/containers/json"
    process = subprocess.Popen(bash_command.split(),
                               stdout=subprocess.PIPE,
                               stderr=subprocess.PIPE)
    output, error = process.communicate()
    rc = process.returncode

    if error or rc:
        print(error)
        raise ProcessLookupError

    container_string = output.decode('utf8')
    return json.loads(container_string)


def get_thornode_object_or_none(address):
    """
    Query nodeaccounts endpoints and return the Thornode object
    """

    nodes = get_node_accounts()

    node = next(filter(lambda n: n['node_address'] == address, nodes), None)

    return node


def get_network_security(network_json):
    """
    Returns network security as a ratio number
    """

    total_active_bond = int(network_json['bondMetrics']['totalActiveBond'])
    total_staked = int(network_json['totalStaked'])
    return total_active_bond / (total_active_bond + total_staked)


def network_security_ratio_to_string(network_security_ratio):
    """
    Converts the network security ratio to an understandable english string
    """

    if network_security_ratio > 0.9:
        network_security_string = "Inefficent"
    elif network_security_ratio <= 0.9 and network_security_ratio > 0.75:
        network_security_string = "Overbonded"
    elif network_security_ratio <= 0.75 and network_security_ratio >= 0.6:
        network_security_string = "Optimal"
    elif network_security_ratio < 0.6 and network_security_ratio >= 0.5:
        network_security_string = "Underbonded"
    elif network_security_ratio < 0.5 and network_security_ratio:
        network_security_string = "Insecure"

    return network_security_string


def get_thorchain_blocks_per_second():
    return get_thorchain_blocks_per_year() / (365 * 24 * 60 * 60)


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


def did_churn_happen(validator, local_node_statuses, highest_churn_status_since) -> bool:
    remote_status = validator['status']
    local_status = local_node_statuses[validator['node_address']] if validator[
                                                                         'node_address'] in local_node_statuses else "unknown"
    if int(validator['status_since']) > highest_churn_status_since and \
            ((local_status == 'ready' and remote_status == 'active') or (local_status == 'active' and remote_status == 'standby')):
        return True
    return False


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
                actual_amount_formatted = (asgard_actual[asset[0]][asset[1]].replace(".", "")).strip("0")
                expected_amount_formatted = (coin['amount'].replace(".", "")).strip("0")
                if actual_amount_formatted != expected_amount_formatted:
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
                actual_amount_formatted = (yggdrasil_actual[vault['vault']['pub_key']][asset[0]][asset[1]]
                                           .replace(".", "")).strip("0")
                expected_amount_formatted = (coin['amount'].replace(".", "")).strip("0")
                if actual_amount_formatted != expected_amount_formatted:
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


def error(update, context):
    """
    Log error.
    """

    logger.warning('Update "%s" caused error: %s', update, context.error)


async def for_each_async(elements: [], function: Callable[...,
                                                          Awaitable[None]]):
    tasks = []
    for element in elements:
        tasks.append(function(element))

    await asyncio.gather(*tasks)

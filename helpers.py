import random
import subprocess
import requests
import json
from telegram import InlineKeyboardButton, KeyboardButton, ReplyKeyboardMarkup, InlineKeyboardMarkup, TelegramError
from datetime import datetime

from constants import *

"""
######################################################################################################################################################
Helpers
######################################################################################################################################################
"""


def try_message_with_home_menu(context, chat_id, text):
    """
    Send a new message with the home menu
    """

    keyboard = get_home_menu_buttons()
    try_message(context=context, chat_id=chat_id, text=text, reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True))


def get_home_menu_buttons():
    """
    Return keyboard buttons for the home menu
    """

    keyboard = [[KeyboardButton('📡 MY NODES', callback_data='thornode_menu')],
                [KeyboardButton('👀 SHOW ALL', callback_data='show_all_thorchain_nodes'),
                 KeyboardButton('🗝 ADMIN AREA', callback_data='admin_menu')]]

    return keyboard


def show_thornode_menu_new_msg(update, context):
    """
    Send a new message with the Thornode Menu
    """

    user_data = context.user_data if context.user_data else context.job.context['user_data']

    keyboard = get_thornode_menu_buttons(user_data=user_data)
    text = 'Click an address from the list below or add a node:' if len(keyboard) > 2 else 'You do not monitor any ' \
                                                                                           'THORNodes yet.\nAdd a Node!'
    try_message(context=context, chat_id=update.effective_message.chat_id, text=text, reply_markup=InlineKeyboardMarkup(keyboard))


def get_thornode_menu_buttons(user_data):
    """
    Return keyboard buttons for the thornode menu
    """

    keyboard = [[]]

    for address in user_data['nodes'].keys():
        try:
            emoji = STATUS_EMOJIS[user_data['nodes'][address]['status']]
        except:
            emoji = STATUS_EMOJIS["deactive"]

        truncated_address = address[:9] + "..." + address[-4:]
        button_text = emoji + " " + user_data['nodes'][address]['alias'] + " (" + truncated_address + ")"
        keyboard.append([InlineKeyboardButton(button_text, callback_data='thornode_details-' + address)])

    keyboard.append([InlineKeyboardButton('1️⃣ ADD NODE', callback_data='add_thornode')])
    keyboard.append([InlineKeyboardButton('➕ ADD ALL', callback_data='confirm_add_all_thornodes'),
                     InlineKeyboardButton('➖ REMOVE ALL', callback_data='confirm_delete_all_thornodes')])

    return keyboard


def show_detail_menu(update, context):
    """
    Show detail buttons for selected address
    """

    query = update.callback_query
    address = context.user_data['selected_node_address']

    node = get_thornode_object(address=address)

    if node is None:
        text = 'THORNode ' + address + ' is not active anymore and will be removed shortly! 💀'
        query.edit_message_text(text)
        show_thornode_menu_new_msg(update, context)

    text = 'THORNode: *' + context.user_data['nodes'][address]['alias'] + '*\n' + \
           'Address: *' + address + '*\n' + \
           'Version: *' + node['version'] + '*\n\n' + \
           'Status: *' + node['status'].capitalize() + '*\n' + \
           'Bond: *' + tor_to_rune(int(node['bond'])) + '*\n' + \
           'Slash Points: ' + '*{:,}*'.format(int(node['slash_points'])) + '\n' \
           'Status Since: ' + '*{:,}*'.format(int(node['status_since'])) + '\n\n'

    if THORCHAIN_NODE_IP:
        text += 'Number of Unconfirmed Txs: ' + '*{:,}*'.format(int(get_number_unconfirmed_txs())) + '\n\n'

    text += "What do you want to do with that Node?"

    keyboard = [[InlineKeyboardButton('➖ REMOVE', callback_data='confirm_thornode_deletion'),
                 InlineKeyboardButton('✏️ CHANGE ALIAS', callback_data='change_alias')],
                [InlineKeyboardButton('⬅️ BACK', callback_data='thornode_menu')]]

    # Modify message
    query.edit_message_text(text, parse_mode='markdown', reply_markup=InlineKeyboardMarkup(keyboard))


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

    try_message(context=context, chat_id=chat_id, text=text, reply_markup=InlineKeyboardMarkup(keyboard))


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
            keyboard.append([InlineKeyboardButton(text, callback_data='container-#' + container_name)])

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
        context.bot.send_message(chat_id, text, parse_mode='markdown', reply_markup=reply_markup)
    except TelegramError as e:
        if 'bot was blocked by the user' in e.message:
            print("Telegram user " + str(chat_id) + " blocked me; removing him from the user list")
            del context.dispatcher.user_data[chat_id]
            del context.dispatcher.chat_data[chat_id]
            del context.dispatcher.persistence.user_data[chat_id]
            del context.dispatcher.persistence.chat_data[chat_id]

            # Somehow session.data does not get updated if all users block the bot.
            # That makes problems on bot restart. That's why we delete the file ourselves.
            if len(context.dispatcher.persistence.user_data) == 0:
                if os.path.exists("storage/session.data"):
                    os.remove("storage/session.data")
            context.job.enabled = False
            context.job.schedule_removal()
        else:
            print("Got Error\n" + str(e) + "\nwith telegram user " + str(chat_id))


def add_thornode_to_user_data(user_data, address, node):
    """
    Add a node in the user specific dictionary
    """

    # Find an alias that does not exist yet
    i = 0
    while True:
        i += 1
        alias = "Thor-" + str(i)
        if not next(filter(
                lambda current_address: user_data['nodes'][current_address]['alias'] == alias, user_data['nodes']), None):
            break

    user_data['nodes'][address] = {}
    user_data['nodes'][address]['alias'] = alias
    user_data['nodes'][address]['status'] = node['status']
    user_data['nodes'][address]['bond'] = node['bond']
    user_data['nodes'][address]['slash_points'] = node['slash_points']
    user_data['nodes'][address]['last_notification_timestamp'] = datetime.timestamp(datetime.now())
    user_data['nodes'][address]['notification_timeout_in_seconds'] = INITIAL_NOTIFICATION_TIMEOUT


def show_confirmation_menu(update, text, keyboard):
    """
    "Are you sure?" - "YES" | "NO"
    """

    query = update.callback_query

    query.edit_message_text(text, parse_mode='markdown', reply_markup=InlineKeyboardMarkup(keyboard))


def get_running_docker_container():
    """
    Return Json of all running container on the host machine
    """

    bash_command = DOCKER_CURL_CMD + " http://localhost/containers/json"
    process = subprocess.Popen(bash_command.split(), stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    output, error = process.communicate()
    rc = process.returncode

    if error or rc:
        print(error)
        raise ProcessLookupError

    container_string = output.decode('utf8')
    return json.loads(container_string)


def get_thornode_object(address):
    """
    Query nodeaccounts endpoints and return the Thornode object
    """

    nodes = get_thorchain_validators()
    # Get the right node
    node = next(filter(lambda node: node['node_address'] == address, nodes), None)
    return node


def get_thorchain_validators():
    while True:
        response = requests.get(url=get_thorchain_validators_endpoint())
        if response.status_code == 200:
            break

    return response.json()


def get_thorchain_block_height():
    """
    Return block height of your Thornode
    """

    while True:
        response = requests.get(url=get_thorchain_status_endpoint())
        if response.status_code == 200:
            break

    status = response.json()
    return status['result']['sync_info']['latest_block_height']


def is_thorchain_catching_up():
    response = requests.get(url=get_thorchain_status_endpoint())
    if response.status_code != 200:
        return True

    status = response.json()
    return status['result']['sync_info']['catching_up']


def is_thorchain_midgard_healthy():
    """
    Return status of Midgard API
    """

    response = requests.get(url=get_thorchain_midgard_endpoint())
    if response.status_code == 200:
        return True
    else:
        return False


def get_number_unconfirmed_txs():
    """
    Return number of unconfirmed transactions
    """

    while True:
        response = requests.get(url=get_thorchain_number_unconfirmed_txs_endpoint())
        if response.status_code == 200:
            break

    unconfirmed_txs_status = response.json()
    return unconfirmed_txs_status['result']['total']


def is_binance_node_healthy():
    """
    Return if Binance Node is healthy
    """

    response = requests.get(url=get_binance_health_endpoint())
    if response.status_code == 200:
        return True
    else:
        return False


def get_thorchain_validators_endpoint():
    """
    Return the nodeaccounts endpoint to query data from.
    """

    if DEBUG:
        return 'http://localhost:8000/nodeaccounts.json'
    elif THORCHAIN_NODE_IP:
        return 'http://' + THORCHAIN_NODE_IP + ':1317/thorchain/nodeaccounts'
    else:
        endpoints = requests.get('https://testnet-seed.thorchain.info').json()
        random_endpoint = endpoints[random.randrange(0, len(endpoints))]
        return 'http://' + random_endpoint + ':1317/thorchain/nodeaccounts'


def get_thorchain_status_endpoint():
    """
    Return the endpoint for block height checks
    """

    return 'http://localhost:8000/status.json' if DEBUG else 'http://' + THORCHAIN_NODE_IP + ':26657/status'


def get_thorchain_midgard_endpoint():
    """
    Return the endpoint for Midgard API check
    """

    return 'http://localhost:8000/midgard.json' if DEBUG else 'http://' + THORCHAIN_NODE_IP + ':8080/v1/health'


def get_thorchain_number_unconfirmed_txs_endpoint():
    """
    Return the endpoint for number of unconfirmed transactions
    """

    return 'http://localhost:8000/unconfirmed_txs.json' if DEBUG else 'http://' + THORCHAIN_NODE_IP + ':26657/num_unconfirmed_txs'


def get_binance_health_endpoint():
    """
    Return the health endpoint of a binance node
    """

    return 'http://localhost:8000/binance_health.json' if DEBUG else 'http://' + BINANCE_NODE_IP + ':26657/health'


def tor_to_rune(tor):
    """
    1e8 Tor are 1 Rune
    Format depending if RUNE > or < Zero
    """

    # Cast to int if tor is string
    tor = int(tor)
    if tor >= 100000000:
        return "{:,} RUNE".format(int(tor / 100000000))
    else:
        return '{:.8f} RUNE'.format(tor / 100000000)


def error(update, context):
    """
    Log error.
    """

    logger.warning('Update "%s" caused error: %s', update, context.error)

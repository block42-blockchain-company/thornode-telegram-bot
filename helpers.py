import random
import subprocess
import requests
import json
from telegram import InlineKeyboardButton, InlineKeyboardMarkup

from constants import *


"""
######################################################################################################################################################
Helpers
######################################################################################################################################################
"""


def show_home_menu(context, chat_id, query=None):
    """
    Show buttons of home menu
    """

    keyboard = [[InlineKeyboardButton('My THORNodes', callback_data='thornode_menu'),
                 InlineKeyboardButton('Admin Area', callback_data='admin_menu')]]

    text = 'I am your THORNode Bot. 🤖\nChoose an action:'
    # Edit message or write a new one depending on function call
    if query:
        query.edit_message_text(text,
                                reply_markup=InlineKeyboardMarkup(keyboard))
    else:
        context.bot.send_message(chat_id, text,
                                 reply_markup=InlineKeyboardMarkup(keyboard))


def show_thornode_menu(context, chat_id, user_data, query=None):
    """
    Show buttons for supported actions.
    """

    keyboard = [[]]

    for address in user_data['nodes'].keys():
        keyboard.append([InlineKeyboardButton(address, callback_data='thornode_details-' + address)])

    keyboard.append([InlineKeyboardButton('Add THORNode', callback_data='add_thornode'),
                     InlineKeyboardButton('<< Back', callback_data='back_button')])

    # Edit query message. Write a new message instead after address input
    if query:
        query.edit_message_text('Choose an address from the list below or add one:',
                                reply_markup=InlineKeyboardMarkup(keyboard))
    else:
        context.bot.send_message(chat_id, 'Choose an address from the list below or add one:',
                                 reply_markup=InlineKeyboardMarkup(keyboard))


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
        show_thornode_menu(context=context, chat_id=update.effective_chat.id, user_data=context.user_data)
        return END

    text = 'THORNode: *' + address + '*\n' + \
           'Version: *' + node['version'] + '*\n\n' + \
           'Status: *' + node['status'].capitalize() + '*\n' + \
           'Bond: *' + tor_to_rune(int(node['bond'])) + '*\n' + \
           'Slash Points: ' + '*{:,}*'.format(int(node['slash_points'])) + '\n' \
           'Status Since: ' + '*{:,}*'.format(int(node['status_since'])) + '\n\n'

    if THORCHAIN_NODE_IP:
        text += 'Number of Unconfirmed Txs: ' + '*{:,}*'.format(int(get_number_unconfirmed_txs())) + '\n\n'

    text += "What do you want to do with that Node?"

    keyboard = [[
        InlineKeyboardButton('Delete THORNode', callback_data='confirm_thornode_deletion'),
        InlineKeyboardButton('<< Back', callback_data='back_button')
        ]]

    # Modify message
    query.edit_message_text(text, parse_mode='markdown', reply_markup=InlineKeyboardMarkup(keyboard))
    return WAIT_FOR_DETAIL


def show_admin_menu(context, chat_id, query=None):
    """
    Show buttons of admin area
    """

    containers = get_running_docker_container()
    if containers == "ERROR":
        if query:
            query.answer("Error while getting running docker container", show_alert=True)
        print("Error while getting running docker container")
        return END

    # build keyboard with one button for every container
    keyboard = [[]]
    for container in containers:
        for name in container['Names']:
            container_name = name.replace('/', '')
            status = container['Status']
            text = container_name + " - " + status
            keyboard.append([InlineKeyboardButton(text, callback_data='container-#' + container_name)])

    keyboard.append([InlineKeyboardButton('<< Back', callback_data='back_button')])

    # Send message
    text = "⚠️ You're in the Admin Area - proceed with care ⚠️\n" \
           "Below is a list of docker containers running on your system.\n" \
           "Click on any container to restart it!"
    if query:
        query.answer()
        query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard))
    else:
        context.bot.send_message(chat_id, text, reply_markup=InlineKeyboardMarkup(keyboard))


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
        return "ERROR"

    container_string = output.decode('utf8')
    return json.loads(container_string)


def get_thornode_object(address):
    """
    Query nodeaccounts endpoints and return the Thornode object
    """

    while True:
        response = requests.get(url=get_thorchain_validators())
        if response.status_code == 200:
            break

    nodes = response.json()

    # Get the right node
    node = next(filter(lambda node: node['node_address'] == address, nodes), None)
    return node


def get_thorchain_block_height():
    """
    Return block height of your Thornode
    """

    while True:
        response = requests.get(url=get_thorchain_status())
        if response.status_code == 200:
            break

    status = response.json()
    return status['result']['sync_info']['latest_block_height']


def is_thorchain_catching_up():
    response = requests.get(url=get_thorchain_status())
    if response.status_code != 200:
        return True

    status = response.json()
    return status['result']['sync_info']['catching_up']


def is_thorchain_midgard_healthy():
    """
    Return status of Midgard API
    """

    response = requests.get(url=get_thorchain_midgard_endpoint())
    if response.status_code != 200:
        return False

    if response.text.find('"OK"') != -1:
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

def get_thorchain_validators():
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


def get_thorchain_status():
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


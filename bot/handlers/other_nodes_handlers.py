import itertools

from telegram import InlineKeyboardButton

from constants.node_ips import *
from handlers.chat_helpers import *
from models.nodes import *


def show_other_nodes_menu(update, context):
    # fixme - refactor me - regarding Chris issue of BTC env variable form
    all_nodes = itertools.chain(EthereumNode.from_ips(ETHEREUM_NODE_IPS),
                                BitcoinNode.from_ips_with_credentials(BITCOIN_NODE_IPS, BITCOIN_NODE_USERNAMES,
                                                                      BITCOIN_NODE_PASSWORDS),
                                BinanceNode.from_ips(BINANCE_NODE_IPS))
    # todo: implement and fix binance nodes.
    all_nodes = list(all_nodes)
    leng = len(all_nodes)
    print(leng)

    buttons = []
    for node in all_nodes:
        is_healthy = context.bot_data.get(node.node_id, {}).get('health', None)
        text = f'({is_healthy}) {node.network_short_name} {node.node_ip}'

        buttons.append(InlineKeyboardButton(text, callback_data='other_node_details-' + node.node_id))

    keyboard = build_2_columns_keyboard(buttons)

    try_message(context=context,
                chat_id=update.effective_message.chat_id,
                text='Choose the node you want to see details.',
                reply_markup=InlineKeyboardMarkup(keyboard))


def show_other_nodes_details(update, context):
    query = update.callback_query

    id = query.data.split('other_node_details-')[-1]

    # ip = other_node_details
    text = f"Work in progress but it's node {id}\n "

    is_synced = context.bot_data.get(id, {}).get('syncing', None)

    if is_synced is None:
        text += "I don't know if it's syncing or not :(. I need to fetch the data."
    else:
        text += f"Is fully synced: {is_synced}"

    try_message(context=context,
                chat_id=update.effective_message.chat_id,
                text=text,
                reply_markup=InlineKeyboardMarkup(
                    [[InlineKeyboardButton('⬅️ BACK', callback_data='show_nodes_other')]]))

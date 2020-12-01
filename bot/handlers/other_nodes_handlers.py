import itertools

from telegram import InlineKeyboardButton

from constants.messages import HEALTH_LEGEND
from constants.node_ips import *
from handlers.chat_helpers import *
from models.nodes import *


def show_other_nodes_menu(update, context):
    all_nodes = itertools.chain(EthereumNode.from_ips(ETHEREUM_NODE_IPS),
                                BitcoinNode.from_ips(BITCOIN_NODE_IPS),
                                BinanceNode.from_ips(BINANCE_NODE_IPS))
    # todo: implement and fix binance nodes.
    all_nodes = list(all_nodes)
    leng = len(all_nodes)
    print(leng)

    text = HEALTH_LEGEND
    text += '\nClick an address from the list below or add a node:'

    buttons = []
    for node in all_nodes:
        is_healthy = context.bot_data.get(node.node_id, {}).get('health', None)
        emoji = HEALTH_EMOJIS[is_healthy]

        buttons.append(InlineKeyboardButton(f'{emoji} {node.network_short_name} {node.node_ip}',
                                            callback_data='other_node_details-' + node.node_id))

    keyboard = build_2_columns_keyboard(buttons)

    try_message(context=context,
                chat_id=update.effective_message.chat_id,
                text=text,
                reply_markup=InlineKeyboardMarkup(keyboard))


def show_other_nodes_details(update, context):
    query = update.callback_query
    node_id = query.data.split('other_node_details-')[-1]
    node = Node.from_id(node_id)

    text = f"Details of node: *{node.network_name}* (*{node.node_ip}*)\n\n "

    is_synced = context.bot_data.get(node.node_id, {}).get('syncing', None)

    if is_synced is None:
        try:
            is_synced = node.is_fully_synced()
        except Exception as e:
            logger.debug(e, exc_info=True)
            is_synced = 'currently unavailable'

    text += f"Is fully synced: *{is_synced}*\n"

    node_height = None
    network_block_height = None

    try:
        node_height = node.get_block_height()
    except Exception as e:
        logger.debug(e, exc_info=True)

    try:
        network_block_height = node.get_real_block_count()
    except Exception as e:
        logger.debug(e, exc_info=True)

    text += f"Node block height:"

    if node_height:
        if network_block_height:
            text += f"*{node_height}/{network_block_height}*"
        else:
            text += f"*{node_height}"

    else:
        text += f"*currently unavailable*"

    try_message(context=context,
                chat_id=update.effective_message.chat_id,
                text=text,
                reply_markup=InlineKeyboardMarkup(
                    [[InlineKeyboardButton('⬅️ BACK', callback_data='show_nodes_other')]]))

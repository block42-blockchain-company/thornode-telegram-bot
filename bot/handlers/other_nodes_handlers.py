from telegram import InlineKeyboardButton

from constants.messages import HEALTH_LEGEND
from data.other_nodes_dao import OtherNodesDao
from handlers.chat_helpers import *


def show_other_nodes_menu(update, context):
    dao = OtherNodesDao()
    text = HEALTH_LEGEND
    text += '\nClick an address from the list below or add a node:'

    buttons = []
    for node in dao.get_all_nodes():
        is_healthy = context.bot_data.get(node.node_id, {}).get('health', None)
        emoji = HEALTH_EMOJIS[is_healthy]

        buttons.append(InlineKeyboardButton(f'{emoji} {node.network_short_name} {node.node_ip}',
                                            callback_data=f'other_node-{hash(node)}'))

    keyboard = build_2_columns_keyboard(buttons)
    keyboard.append([InlineKeyboardButton('⬅ BACK', callback_data='my_nodes_menu')])

    try_message(context=context,
                chat_id=update.effective_message.chat_id,
                text=text,
                reply_markup=InlineKeyboardMarkup(keyboard))


def show_other_nodes_details(update, context):
    query = update.callback_query
    node_hash = query.data.split('other_node-')[-1]
    node = OtherNodesDao().get_node_by_hash(node_hash)

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

import math

from telegram import InlineKeyboardButton
from telegram.ext import run_async

from constants.messages import NETWORK_ERROR, HEALTH_LEGEND
from handlers.chat_helpers import *
from service.utils import *
from datetime import timedelta


@run_async
def confirm_add_all_thornodes(update, _):
    """
    Ask user if he really wants to add all available Thornodes
    """

    keyboard = [[
        InlineKeyboardButton('YES ✅', callback_data='add_all_thornodes'),
        InlineKeyboardButton('NO ❌', callback_data='show_nodes_thor')
    ]]
    text = '⚠️ Do you really want to *add all* available THORNodes to your monitoring list? ⚠️'

    return show_confirmation_menu(update=update, text=text, keyboard=keyboard)


@run_async
def confirm_delete_all_thornodes(update, context):
    """
    Ask user if he really wants to delete all available Thornodes
    """

    keyboard = [[
        InlineKeyboardButton('YES ✅', callback_data='delete_all_thornodes'),
        InlineKeyboardButton('NO ❌', callback_data='show_nodes_thor')
    ]]
    text = '⚠️ Do you really want to *remove all* THORNodes from your monitoring list? ⚠️'

    return show_confirmation_menu(update=update, text=text, keyboard=keyboard)


@run_async
def add_thornode(update, context):
    """
    Initiate a conversation and prompt for user input (thornode address).
    """

    context.chat_data['expected'] = 'add_node'

    text = 'What\'s the address of your THORNode?'
    return show_text_input_message(update, text)


@run_async
def change_alias(update, context):
    """
    Initiate a conversation and prompt for user input (new alias).
    """

    context.chat_data['expected'] = 'change_alias'

    text = 'How would you like to name your THORNode?'
    return show_text_input_message(update, text)


def handle_add_node(update, context):
    """
    Handle text input after an user has asked to add a new thornode.
    """

    # Assume text input is an address
    address = update.message.text

    node = get_thornode_object_or_none(address=address)

    if node is None:
        update.message.reply_text(
            '⛔️ I have not found a THORNode with this address! Please try another one.'
        )
        context.chat_data['expected'] = 'add_node'
        return

    add_thornode_to_chat_data(context.chat_data, address, node)

    # Send message
    update.message.reply_text('Got it! 👌')
    show_my_thorchain_nodes_menu(update, context)


def handle_change_alias(update, context):
    """
    Handle text input after the user clicked "change alias"
    """

    # Text input is the new alias
    alias = update.message.text

    if len(alias) > 16:
        update.message.reply_text(
            '⛔️ Alias cannot have more than 16 characters! Please try another one.'
        )
        context.chat_data['expected'] = 'change_alias'
        return

    context.chat_data.setdefault('nodes', {})[
        context.chat_data['selected_node_address']]['alias'] = alias

    # Send message
    update.message.reply_text('Got it! 👌')
    show_my_thorchain_nodes_menu(update, context)


def confirm_thornode_deletion(update, context):
    """
    Initiate process of thornode address removal
    """

    address = context.chat_data['selected_node_address']

    keyboard = [[
        InlineKeyboardButton('YES ✅', callback_data='delete_thornode'),
        InlineKeyboardButton('NO ❌',
                             callback_data='thornode_details-' + address)
    ]]
    text = '⚠️ Do you really want to remove this node from your monitoring list? ⚠\n️' + \
           "*" + context.chat_data['nodes'][address]['alias'] + "*\n" + \
           "*" + address + "*"

    return show_confirmation_menu(update=update, text=text, keyboard=keyboard)


def delete_thornode(update, context):
    """
    Remove selected address from the monitored thornodes
    """

    query = update.callback_query
    address = context.chat_data['selected_node_address']

    text = "❌ Thornode got deleted! ❌\n" + \
           "*" + context.chat_data['nodes'][address]['alias'] + "*\n" + \
           "*" + address + "*"

    del context.chat_data['nodes'][address]

    query.edit_message_text(text, parse_mode='markdown')
    show_my_thorchain_nodes_menu(update, context)


def thornode_details(update, context):
    """
    Shows thornode detail buttons
    """

    query = update.callback_query

    address = query.data.split("-")[1]
    context.chat_data['selected_node_address'] = address

    return show_detail_menu(update=update, context=context)


def add_all_thornodes(update, context):
    """
    Add all available Thornode addresses to users monitoring list
    """

    query = update.callback_query

    nodes = get_node_accounts()

    for node in nodes:
        address = node['node_address']
        if address not in context.chat_data.get('nodes', {}):
            add_thornode_to_chat_data(context.chat_data, address, node)

    # Send message
    query.edit_message_text('Added all THORNodes! 👌')
    show_my_thorchain_nodes_menu(update, context)


def delete_all_thornodes(update, context):
    """
    Delete all Thornode addresses from users monitoring list
    """

    query = update.callback_query

    context.chat_data.clear()

    text = '❌ Deleted all THORNodes! ❌'
    # Send message
    query.edit_message_text(text)

    show_my_thorchain_nodes_menu(update, context)


def show_all_thorchain_nodes(update, context):
    """
    Show the status of all Thornodes in the whole Thorchain network
    """

    try:
        nodes = get_node_accounts()
        latest_block_height = get_latest_block_height()
        blocks_per_second = get_thorchain_blocks_per_second()
    except Exception as e:
        logger.exception(e)
        try_message_with_home_menu(context=context,
                                   chat_id=update.effective_chat.id,
                                   text=NETWORK_ERROR)
        return

    text = "Status of all THORNodes in the THORChain network:\n\n"

    for node in nodes:
        try:
            monitored_address = next(
                filter(
                    lambda a: a == node[
                        'node_address'], context.chat_data.get('nodes', {})), None)
            text += 'THORNode: *'

            if monitored_address:
                text += context.chat_data['nodes'][monitored_address]['alias']
            else:
                text += "not monitored"
            text += "*\n"

            status_since_in_seconds = (int(latest_block_height) - int(
                node['status_since'])) / blocks_per_second

            text += 'Address: *' + node['node_address'] + '*\n' + \
                    'Version: *' + node['version'] + '*\n' + \
                    'Status: *' + node['status'].capitalize() + '*\n' + \
                    'Bond: *' + tor_to_rune(node['bond']) + '*\n' + \
                    'Slash Points: ' + '*{:,}*'.format(int(node['slash_points'])) + '\n' + \
                    'Accrued Rewards: *' + tor_to_rune(node['current_award']) + '*\n' + \
                    node['status'].capitalize() + ' for *' + \
                    format_to_days_and_hours(timedelta(seconds=status_since_in_seconds)) + '*\n\n' + \
                    'Status Since Block: ' + '*{:,}*'.format(int(node['status_since'])) + '\n\n'

            try_message(context=context,
                        chat_id=update.effective_chat.id,
                        text=text)
            text = ''
        except Exception as e:
            logger.exception(e)
            text += '\nError while getting more data about this node.\n'
            try_message(context=context,
                        chat_id=update.effective_chat.id,
                        text=text)
            text = ''


def show_my_thorchain_nodes_menu(update, context):
    PAGE_SIZE = 30
    chat_data = context.chat_data if context.chat_data else context.job.context[
        'chat_data']

    keyboard = get_thornode_menu_buttons(chat_data=chat_data)

    if len(keyboard) > 2:
        text = '*Node statuses*:\n'
        for status, emoji in STATUS_EMOJIS.items():
            text += f"{emoji} - *{status}*\n"

        text += HEALTH_LEGEND
        text += '\nClick an address from the list below or add a node:'
    else:
        text = 'You do not monitor any THORNodes yet.\nAdd a Node!'

    if len(keyboard) < PAGE_SIZE:
        update.callback_query.edit_message_text(context=context,
                                                text=text,
                                                parse_mode='markdown',
                                                reply_markup=InlineKeyboardMarkup(keyboard))
    else:
        pages = math.ceil(len(keyboard) / PAGE_SIZE)
        for i in range(pages):
            try_message(context=context,
                        chat_id=update.effective_message.chat_id,
                        text=f"{text}\nPage {i+1} of {pages}",
                        reply_markup=InlineKeyboardMarkup(keyboard[(i * PAGE_SIZE): ((i+1) * PAGE_SIZE)]))
            text = ""



def get_thornode_menu_buttons(chat_data):
    buttons = []
    for address in chat_data.get('nodes', {}).keys():
        node = chat_data['nodes'][address]
        status_emoji = STATUS_EMOJIS.get(node['status'], STATUS_EMOJIS["unknown"])
        truncated_address = f"...{address[-3:]}"
        is_catching_up = node.get('is_catching_up', None)
        is_healthy = None if is_catching_up is None else not is_catching_up
        is_healthy_emoji = HEALTH_EMOJIS[is_healthy]

        button_text = f"{status_emoji} {node['alias']} ({truncated_address}) [{is_healthy_emoji}]"

        buttons.append(InlineKeyboardButton(button_text, callback_data='thornode_details-' + address))

    keyboard = build_2_columns_keyboard(buttons)
    buttons = [[
        InlineKeyboardButton('1️⃣ ADD NODE', callback_data='add_thornode')], [
        InlineKeyboardButton('➕ ADD ALL',
                             callback_data='confirm_add_all_thornodes'),
        InlineKeyboardButton('➖ REMOVE ALL',
                             callback_data='confirm_delete_all_thornodes')
    ], [
        InlineKeyboardButton('⬅ BACK', callback_data='my_nodes_menu-edit'),
    ]]
    keyboard.extend(buttons)

    return keyboard


def show_detail_menu(update, context):
    """
    Show detail buttons for selected address
    """

    query = update.callback_query
    address = context.chat_data['selected_node_address']

    try:
        node = get_thornode_object_or_none(address=address)
    except Exception as e:
        logger.exception(e)
        query.edit_message_text(NETWORK_ERROR)
        show_my_thorchain_nodes_menu(update, context)
        return

    if node is None:
        text = 'THORNode ' + address + ' is not active anymore and will be removed shortly! 💀'
        query.edit_message_text(text)
        show_my_thorchain_nodes_menu(update, context)
        return

    text = 'THORNode: *' + context.chat_data['nodes'][address]['alias'] + '*\n' + \
           'Address: *' + address + '*\n' + \
           'Version: *' + node['version'] + '*\n\n' + \
           'Status: *' + node['status'].capitalize() + '*\n' + \
           'Bond: *' + tor_to_rune(node['bond']) + '*\n' + \
           'Slash Points: ' + '*{:,}*'.format(int(node['slash_points'])) + '\n' + \
           'Accrued Rewards: *' + tor_to_rune(node['current_award']) + '*\n'

    status = None
    try:
        status = get_node_status(node['ip_address'])['result']

        is_catching_up = status['sync_info']['catching_up']
        current_height = status['sync_info']['latest_block_height']
        last_block = get_thorchain_last_block()

        text += f'Node synchronized: *{not is_catching_up}*\n' \
                f'Current block: *{current_height}/{last_block}*\n'
    except Exception as e:
        logger.exception(e)
        text += "*I can't check synchronization status and current block of this node*\n"

    try:
        text += 'Status Since Block: ' + '*{:,}*'.format(int(node['status_since'])) + '\n'
        latest_block_height = status['sync_info']['latest_block_height']
        blocks_per_second = get_thorchain_blocks_per_second()
        status_since_in_seconds = (int(latest_block_height) - int(
            node['status_since'])) / blocks_per_second

        text += f"{node['status'].capitalize()} for " \
                f"*{format_to_days_and_hours(timedelta(seconds=status_since_in_seconds))}*\n"
    except Exception as e:
        logger.exception(e)
        text += 'Currently I Can\'t get duration of this status. Try again later!\n'

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
    ], [InlineKeyboardButton('⬅️ BACK', callback_data='show_nodes_thor')]]

    # Modify message
    query.edit_message_text(text,
                            parse_mode='markdown',
                            reply_markup=InlineKeyboardMarkup(keyboard))

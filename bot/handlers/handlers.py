import re

from telegram.error import BadRequest
from telegram.ext import run_async

from handlers.network_info_handlers import show_network_menu, show_vault_key_addresses, solvency_stats, \
    show_network_stats
from jobs import *
from service.thorchain_network_service import *


@run_async
def start(update, context):
    """
    Send start message and display action buttons.
    """

    if not is_admin(update, context):
        return

    # Start job for user
    if 'job_started' not in context.user_data:
        context.job_queue.run_repeating(user_specific_checks,
                                        interval=JOB_INTERVAL_IN_SECONDS,
                                        context={
                                            'chat_id': update.message.chat.id,
                                            'user_data': context.user_data
                                        })
        context.user_data['job_started'] = True
        context.user_data['nodes'] = {}

    text = 'Heil ok sæll! I am your THORNode Bot running on ' + NETWORK_TYPE + '. 🤖\n\n' \
                                                                               'I will notify you about changes of your THORNode\'s\n' \
                                                                               '- *Status*\n' \
                                                                               '- *Bond*\n' \
                                                                               '- *Slash Points*\n' \
                                                                               '- if your *Block Height* gets stuck\n' \
                                                                               '- if your *Midgard API* gets unhealthy\n\n' \
                                                                               'You will get a notification\n' \
                                                                               '- once any node *upgrades its version*\n' \
                                                                               '- after *successful churning*\n' \
                                                                               '- if thorchain becomes *insolvent*\n\n'

    text += 'If you specified Node IPs, I notify you about changes of your *Binance, ' \
            'Ethereum and Bitcoin Node\'s health*.\n\n'
    text += 'Moreover, in the Network section you can display\n' \
            '- the *status of the whole network*\n' \
            '- the correct *vault addresses*.\n' \
            '- the current *solvency* status.\n'

    # Send message
    try_message_with_home_menu(context=context,
                               chat_id=update.message.chat.id,
                               text=text)


@run_async
def my_nodes_menu_handler(update, context):
    """
    Thornode Menu Command handler
    """

    show_nodes_type_choice_menu(update, context)


@run_async
def dispatch_query(update, context):
    """
    Call right function depending on the button clicked
    """

    query = update.callback_query
    query.answer()
    data = query.data

    if not is_admin(update, context):
        return

    context.user_data['expected'] = None
    edit = True
    call = None

    if data == 'show_all_thorchain_nodes':
        call = show_all_thorchain_nodes
    elif data == 'show_network_stats':
        call = show_network_stats
    elif data == 'solvency':
        call = solvency_stats
    elif data == 'vault_key_addresses':
        call = show_vault_key_addresses
    elif data == 'add_thornode':
        call = add_thornode
    elif data == 'confirm_add_all_thornodes':
        call = confirm_add_all_thornodes
    elif data == 'add_all_thornodes':
        call = add_all_thornodes
    elif data == 'confirm_delete_all_thornodes':
        call = confirm_delete_all_thornodes
    elif data == 'delete_all_thornodes':
        call = delete_all_thornodes
    elif re.match('thornode_details', data):
        call = thornode_details
    elif data == 'confirm_thornode_deletion':
        call = confirm_thornode_deletion
    elif data == 'delete_thornode':
        call = delete_thornode
    elif data == 'change_alias':
        call = change_alias
    elif data == 'show_nodes_thor':
        call = show_my_thorchain_nodes_menu
    else:
        edit = False

    # Catch any 'Message is not modified' error by removing the keyboard
    if edit:
        try:
            context.bot.edit_message_reply_markup(
                reply_markup=None,
                chat_id=update.callback_query.message.chat_id,
                message_id=update.callback_query.message.message_id)
        except BadRequest as e:
            if 'Message is not modified' in e.message:
                pass
            else:
                raise

    if call:
        call = asyncio.coroutine(call)
        return asyncio.run(call(update, context))


@run_async
def confirm_add_all_thornodes(update, context):
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

    context.user_data['expected'] = 'add_node'

    text = 'What\'s the address of your THORNode?'
    return show_text_input_message(update, text)


@run_async
def change_alias(update, context):
    """
    Initiate a conversation and prompt for user input (new alias).
    """

    context.user_data['expected'] = 'change_alias'

    text = 'How would you like to name your THORNode?'
    return show_text_input_message(update, text)


@run_async
def plain_input(update, context):
    """
    Handle if the users sends a message
    """

    if not is_admin(update, context):
        return

    message = update.message.text
    expected = context.user_data[
        'expected'] if 'expected' in context.user_data else None
    if message == '📡 MY NODES':
        return my_nodes_menu_handler(update, context)
    elif message == '🌎 NETWORK':
        return show_network_menu(update, context)
    elif message == '👀 SHOW ALL':
        return show_all_thorchain_nodes(update, context)
    elif expected == 'add_node':
        context.user_data['expected'] = None
        return handle_add_node(update, context)
    elif expected == 'change_alias':
        context.user_data['expected'] = None
        return handle_change_alias(update, context)


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
        context.user_data['expected'] = 'add_node'
        return

    add_thornode_to_user_data(context.user_data, address, node)

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
        context.user_data['expected'] = 'change_alias'
        return

    context.user_data['nodes'][
        context.user_data['selected_node_address']]['alias'] = alias

    # Send message
    update.message.reply_text('Got it! 👌')
    show_my_thorchain_nodes_menu(update, context)


def confirm_thornode_deletion(update, context):
    """
    Initiate process of thornode address removal
    """

    address = context.user_data['selected_node_address']

    keyboard = [[
        InlineKeyboardButton('YES ✅', callback_data='delete_thornode'),
        InlineKeyboardButton('NO ❌',
                             callback_data='thornode_details-' + address)
    ]]
    text = '⚠️ Do you really want to remove this node from your monitoring list? ⚠\n️' + \
           "*" + context.user_data['nodes'][address]['alias'] + "*\n" + \
           "*" + address + "*"

    return show_confirmation_menu(update=update, text=text, keyboard=keyboard)


def delete_thornode(update, context):
    """
    Remove selected address from the monitored thornodes
    """

    query = update.callback_query
    address = context.user_data['selected_node_address']

    text = "❌ Thornode got deleted! ❌\n" + \
           "*" + context.user_data['nodes'][address]['alias'] + "*\n" + \
           "*" + address + "*"

    del context.user_data['nodes'][address]

    query.edit_message_text(text, parse_mode='markdown')
    show_my_thorchain_nodes_menu(update, context)


def thornode_details(update, context):
    """
    Shows thornode detail buttons
    """

    query = update.callback_query

    address = query.data.split("-")[1]
    context.user_data['selected_node_address'] = address

    return show_detail_menu(update=update, context=context)


def add_all_thornodes(update, context):
    """
    Add all available Thornode addresses to users monitoring list
    """

    query = update.callback_query

    nodes = get_node_accounts()

    for node in nodes:
        address = node['node_address']
        if address not in context.user_data['nodes']:
            add_thornode_to_user_data(context.user_data, address, node)

    # Send message
    query.edit_message_text('Added all THORNodes! 👌')
    show_my_thorchain_nodes_menu(update, context)


def delete_all_thornodes(update, context):
    """
    Delete all Thornode addresses from users monitoring list
    """

    query = update.callback_query

    addresses = []
    for address in context.user_data['nodes']:
        addresses.append(address)

    for address in addresses:
        del context.user_data['nodes'][address]

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
                                   text=NETWORK_ERROR_MSG)
        return

    text = "Status of all THORNodes in the THORChain network:\n\n"

    for node in nodes:
        try:
            monitored_address = next(
                filter(
                    lambda monitored_address: monitored_address == node[
                        'node_address'], context.user_data['nodes']), None)
            text += 'THORNode: *'

            if monitored_address:
                text += context.user_data['nodes'][monitored_address]['alias']
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

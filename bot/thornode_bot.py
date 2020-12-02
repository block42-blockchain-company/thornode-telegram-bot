import atexit
import re
import time

from telegram.error import BadRequest, Unauthorized, InvalidToken
from telegram.ext import (Updater, CommandHandler, PicklePersistence,
                          CallbackQueryHandler, MessageHandler, Filters, messagequeue)
from telegram.ext.dispatcher import run_async
from telegram.utils.request import Request

from handlers.network_info import *
from jobs import *
from messages import NETWORK_ERROR_MSG
from service.thorchain_network_service import *
from message_queue import MQBot

"""
######################################################################################################################################################
BOT RESTART SETUP
######################################################################################################################################################
"""


def setup_existing_users(dispatcher):
    """
    Tasks to ensure smooth user experience for existing users upon Bot restart
    """
    logger.info("Setting up the user's data.")

    blocked_ids = []

    for chat_id in dispatcher.chat_data.keys():
        # about `not is_group_chat(chat_id)`: Filter out group chats, as they can't get whitelisted.
        if ALLOWED_USER_IDS != 'ALL' and not is_group_chat(chat_id) and chat_id not in ALLOWED_USER_IDS:
            blocked_ids.append(chat_id)
            continue

        restart_message = 'Heil ok sæll!\n' \
                          'Me, your THORNode Bot, just got restarted on the server! 🤖\n' \
                          'To make sure you have the latest features, please start ' \
                          'a fresh chat with me by typing /start.'

        message_result = dispatcher.bot.send_message(chat_id, restart_message)
        if isinstance(message_result.exception, Unauthorized):
            blocked_ids.append(chat_id)
            continue
        elif isinstance(message_result.exception, TelegramError):
            logger.exception(f'USER {str(chat_id)}\n Error: {str(message_result.exception)}',
                             exc_info=True)

        # Start monitoring jobs for all existing users
        if 'job_started' not in dispatcher.chat_data[chat_id]:
            dispatcher.chat_data[chat_id]['job_started'] = True
        dispatcher.job_queue.run_repeating(
            user_specific_checks,
            interval=JOB_INTERVAL_IN_SECONDS,
            context={
                'chat_id': chat_id,
                'chat_data': dispatcher.chat_data[chat_id]
            })

    for chat_id in blocked_ids:
        logger.info(f"Telegram chat {str(chat_id)} blocked me or is "
                    f"not Admin anymore; removing it from the chat list")

        if not is_group_chat(chat_id):
            del dispatcher.user_data[chat_id]
            del dispatcher.persistence.user_data[chat_id]

        del dispatcher.chat_data[chat_id]
        del dispatcher.persistence.chat_data[chat_id]

        # Somehow session.data does not get updated if all users block the bot.
        # That's why we delete the file ourselves.
        if len(dispatcher.persistence.chat_data) == 0:
            if os.path.exists(session_data_path):
                os.remove(session_data_path)

    try:
        new_node_accounts = get_node_accounts()
    except:
        logger.exception(
            "Fatal error! I couldn't get node accounts to update the local chat_data!",
            exc_info=True)
        return

    # Delete all node addresses and add them again to ensure all chat_data fields are up to date
    for chat_id in dispatcher.chat_data.keys():
        if 'nodes' not in dispatcher.chat_data[chat_id]:
            dispatcher.chat_data[chat_id]['nodes'] = {}

        local_node_addresses = list(
            dispatcher.chat_data[chat_id]['nodes'].keys())

        for address in local_node_addresses:
            try:
                new_node = next(n for n in new_node_accounts
                                if n['node_address'] == address)
                del dispatcher.chat_data[chat_id]['nodes'][address]
                add_thornode_to_chat_data(dispatcher.chat_data[chat_id],
                                          address, new_node)
            except StopIteration:
                obsolete_node = dispatcher.chat_data[chat_id]['nodes'][address]
                dispatcher.bot.send_message(
                    chat_id,
                    f"Your node {obsolete_node['alias']} with address {address} "
                    f"is not present in the network! "
                    f"I'm removing it...")
                del dispatcher.chat_data[chat_id]['nodes'][address]


def setup_bot_data(dispatcher):
    if 'binance_nodes' not in dispatcher.bot_data:
        dispatcher.bot_data['binance_nodes'] = {}
    for binance_node_ip in BINANCE_NODE_IPS:
        if binance_node_ip not in dispatcher.bot_data['binance_nodes']:
            dispatcher.bot_data['binance_nodes'][binance_node_ip] = {}

    dispatcher.job_queue.run_repeating(general_bot_checks,
                                       interval=JOB_INTERVAL_IN_SECONDS)
    dispatcher.job_queue.run_repeating(check_bitcoin_height_increase_job,
                                       interval=BitcoinNode.max_time_for_block_height_increase_in_seconds)
    dispatcher.job_queue.run_repeating(check_ethereum_height_increase_job,
                                       interval=EthereumNode.max_time_for_block_height_increase_in_seconds)

    syncing_checks_interval_in_seconds = 120
    dispatcher.job_queue.run_repeating(check_syncing_job,
                                       interval=syncing_checks_interval_in_seconds)


"""
######################################################################################################################################################
Handlers
######################################################################################################################################################
"""


@run_async
def start(update, context):
    """
    Send start message and display action buttons.
    """

    if not is_admin(update, context):
        return

    # Start job for user
    if 'job_started' not in context.chat_data:
        context.job_queue.run_repeating(user_specific_checks,
                                        interval=JOB_INTERVAL_IN_SECONDS,
                                        context={
                                            'chat_id': update.message.chat.id,
                                            'chat_data': context.chat_data
                                        })
        context.chat_data['job_started'] = True
        context.chat_data['nodes'] = {}

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
def show_thornode_menu_handler(update, context):
    """
    Thornode Menu Command handler
    """

    show_thornode_menu_new_msg(update, context)


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

    context.chat_data['expected'] = None
    edit = True
    call = None

    if data == 'thornode_menu':
        call = show_thornode_menu_edit_msg
    elif data == 'show_all_thorchain_nodes':
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


def show_thornode_menu_edit_msg(update, context):
    """
    Show Thornode Menu
    """

    keyboard = get_thornode_menu_buttons(chat_data=context.chat_data)
    text = 'Click an address from the list below or add a node:' if len(keyboard) > 2 else 'You do not monitor any ' \
                                                                                           'THORNodes yet.\nAdd a Node!'
    query = update.callback_query
    query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard))


@run_async
def confirm_add_all_thornodes(update, context):
    """
    Ask user if he really wants to add all available Thornodes
    """

    keyboard = [[
        InlineKeyboardButton('YES ✅', callback_data='add_all_thornodes'),
        InlineKeyboardButton('NO ❌', callback_data='thornode_menu')
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
        InlineKeyboardButton('NO ❌', callback_data='thornode_menu')
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


@run_async
def plain_input(update, context):
    """
    Handle if the users sends a message
    """

    if not is_admin(update, context):
        return

    message = update.message.text
    expected = context.chat_data[
        'expected'] if 'expected' in context.chat_data else None
    if message == '📡 MY NODES':
        return show_thornode_menu_handler(update, context)
    elif message == '🌎 NETWORK':
        return show_network_menu(update, context)
    elif message == '👀 SHOW ALL':
        return show_all_thorchain_nodes(update, context)
    elif expected == 'add_node':
        context.chat_data['expected'] = None
        return handle_add_node(update, context)
    elif expected == 'change_alias':
        context.chat_data['expected'] = None
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
        context.chat_data['expected'] = 'add_node'
        return

    add_thornode_to_chat_data(context.chat_data, address, node)

    # Send message
    update.message.reply_text('Got it! 👌')
    show_thornode_menu_new_msg(update, context)


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

    context.chat_data['nodes'][
        context.chat_data['selected_node_address']]['alias'] = alias

    # Send message
    update.message.reply_text('Got it! 👌')
    show_thornode_menu_new_msg(update, context)


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
    show_thornode_menu_new_msg(update, context)


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
        if address not in context.chat_data['nodes']:
            add_thornode_to_chat_data(context.chat_data, address, node)

    # Send message
    query.edit_message_text('Added all THORNodes! 👌')
    show_thornode_menu_new_msg(update, context)


def delete_all_thornodes(update, context):
    """
    Delete all Thornode addresses from users monitoring list
    """

    query = update.callback_query

    addresses = []
    for address in context.chat_data['nodes']:
        addresses.append(address)

    for address in addresses:
        del context.chat_data['nodes'][address]

    text = '❌ Deleted all THORNodes! ❌'
    # Send message
    query.edit_message_text(text)

    show_thornode_menu_new_msg(update, context)


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
                        'node_address'], context.chat_data['nodes']), None)
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


"""
######################################################################################################################################################
Application
######################################################################################################################################################
"""


def setup_debug_processes():
    current_dir = os.path.dirname(os.path.realpath(__file__))
    increase_block_height_path = os.sep.join(
        [current_dir, os.path.pardir, "test", "increase_block_height.py"])
    test_dir = os.sep.join([current_dir, os.path.pardir, "test"])
    mock_api_path = os.sep.join([test_dir, "mock_api.py"])

    increase_block_height_process = subprocess.Popen(
        ['python3', increase_block_height_path], cwd=test_dir)
    mock_api_process = subprocess.Popen(['python3', mock_api_path],
                                        cwd=test_dir)

    def cleanup():
        mock_api_process.terminate()
        increase_block_height_process.terminate()

    atexit.register(cleanup)
    time.sleep(
        1)  # Make sure all processes started before bot starts using them


def main():
    """
    Init telegram bot, attach handlers and wait for incoming requests.
    """
    if DEBUG:
        setup_debug_processes()

    # M messages/N milliseconds is set as M burst_limit and N time_limit_ms
    # We cannot set burst_limit to 1, because of some off-by-one if check in the library
    m_queue = messagequeue.MessageQueue(all_burst_limit=20, all_time_limit_ms=1000,
                                        group_burst_limit=2, group_time_limit_ms=7000)
    # set connection pool size for bot because
    # it only happens automatically when creating Updater() with the telegram token.
    # But we use the mq_bot to create the Updater() instance.
    # Increased 'read_timeout' from default 5 seconds to 20 seconds to mitigate Timeouts due
    # to the MessageQueue delay for group chats.
    request = Request(con_pool_size=8, read_timeout=20)

    try:
        mq_bot = MQBot(TELEGRAM_BOT_TOKEN, request=request, mqueue=m_queue)
    except InvalidToken:
        logger.error("Invalid telegram token. Please make sure to set TELEGRAM_BOT_TOKEN environmental variable with"
                     " correct Telegram bot token. Check project docs for more details.", exc_info=True)
        raise

    bot = Updater(bot=mq_bot,
                  persistence=PicklePersistence(filename=session_data_path),
                  use_context=True)

    dispatcher = bot.dispatcher

    setup_existing_users(dispatcher=dispatcher)
    setup_bot_data(dispatcher=dispatcher)

    dispatcher.add_handler(CommandHandler('start', start))
    dispatcher.add_handler(CallbackQueryHandler(dispatch_query))
    dispatcher.add_handler(MessageHandler(Filters.text, plain_input))

    # Add error handler
    dispatcher.add_error_handler(error)

    # Start the bot
    bot.start_polling()
    logger.info('THORNode Bot is running on ' + NETWORK_TYPE + ' ...')

    # Run the bot until you press Ctrl-C or the process receives SIGINT,
    # SIGTERM or SIGABRT. This should be used most of the time, since
    # start_polling() is non-blocking and will stop the bot gracefully.
    bot.idle()


if __name__ == '__main__':
    main()

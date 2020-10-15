import atexit
import re
import time

from telegram.error import BadRequest, Unauthorized
from telegram.ext import (Updater, CommandHandler, PicklePersistence,
                          CallbackQueryHandler, MessageHandler, Filters)
from telegram.ext.dispatcher import run_async

from handlers.network_info import *
from jobs import *
from messages import NETWORK_ERROR_MSG
from service.thorchain_network_service import *
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

    bot_blocked_by_ids = []

    for chat_id in dispatcher.user_data.keys():
        restart_message = 'Heil ok sæll!\n' \
                          'Me, your THORNode Bot, just got restarted on the server! 🤖\n' \
                          'To make sure you have the latest features, please start ' \
                          'a fresh chat with me by typing /start.'

        try:
            dispatcher.bot.send_message(chat_id, restart_message)
        except Unauthorized:
            bot_blocked_by_ids.append(chat_id)
            continue
        except TelegramError as e:
            logger.exception(f'USER {str(chat_id)}\n Error: {str(e)}',
                             exc_info=True)

        # Start monitoring jobs for all existing users
        if 'job_started' not in dispatcher.user_data[chat_id]:
            dispatcher.user_data[chat_id]['job_started'] = True
        dispatcher.job_queue.run_repeating(
            user_specific_checks,
            interval=JOB_INTERVAL_IN_SECONDS,
            context={
                'chat_id': chat_id,
                'user_data': dispatcher.user_data[chat_id]
            })

    for chat_id in bot_blocked_by_ids:
        logger.warning("Telegram user " + str(chat_id) +
                       " blocked me; removing him from the user list")

        del dispatcher.user_data[chat_id]
        del dispatcher.chat_data[chat_id]
        del dispatcher.persistence.user_data[chat_id]
        del dispatcher.persistence.chat_data[chat_id]

        # Somehow session.data does not get updated if all users block the bot.
        # That's why we delete the file ourselves.
        if len(dispatcher.persistence.user_data) == 0:
            if os.path.exists(session_data_path):
                os.remove(session_data_path)

    try:
        new_node_accounts = get_node_accounts()
    except:
        logger.exception(
            "Fatal error! I couldn't get node accounts to update the local user_data!",
            exc_info=True)
        return

    # Delete all node addresses and add them again to ensure all user_data fields are up to date
    for chat_id in dispatcher.user_data.keys():
        if 'nodes' not in dispatcher.user_data[chat_id]:
            dispatcher.user_data[chat_id]['nodes'] = {}

        local_node_addresses = list(
            dispatcher.user_data[chat_id]['nodes'].keys())

        for address in local_node_addresses:
            try:
                new_node = next(n for n in new_node_accounts
                                if n['node_address'] == address)
                del dispatcher.user_data[chat_id]['nodes'][address]
                add_thornode_to_user_data(dispatcher.user_data[chat_id],
                                          address, new_node)
            except StopIteration:
                obsolete_node = dispatcher.user_data[chat_id]['nodes'][address]
                dispatcher.bot.send_message(
                    chat_id,
                    f"Your node {obsolete_node['alias']} with address {address} "
                    f"is not present in the network! "
                    f"I'm removing it...")
                del dispatcher.user_data[chat_id]['nodes'][address]


def setup_bot_data(dispatcher):
    if 'binance_nodes' not in dispatcher.bot_data:
        dispatcher.bot_data['binance_nodes'] = {}
    for binance_node_ip in BINANCE_NODE_IPS:
        if binance_node_ip not in dispatcher.bot_data['binance_nodes']:
            dispatcher.bot_data['binance_nodes'][binance_node_ip] = {}

    dispatcher.job_queue.run_repeating(general_bot_checks,
                                       interval=JOB_INTERVAL_IN_SECONDS)


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
           '- after *successful churning*\n\n'
    if BINANCE_NODE_IPS:
        text += 'Furthermore I notify you about changes of your *Binance Node\'s health*.\n\n'
    text += 'Moreover, in the Admin Area you can\n' \
            '- *restart any docker container* that runs alongside my container\n\n' \
            'In the Network section you can display\n' \
            '- the *status of the whole network*\n' \
            '- the correct *vault addresses*.'

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

    context.user_data['expected'] = None
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
    elif data == 'admin_menu':
        call = admin_menu
    elif re.match('container', data):
        call = confirm_container_restart
    elif re.match('restart_container', data):
        call = restart_container
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

    keyboard = get_thornode_menu_buttons(user_data=context.user_data)
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
    message = update.message.text
    expected = context.user_data[
        'expected'] if 'expected' in context.user_data else None
    if message == '📡 MY NODES':
        return show_thornode_menu_handler(update, context)
    elif message == '🌎 NETWORK':
        return show_network_menu(update, context)
    elif message == '👀 SHOW ALL':
        return show_all_thorchain_nodes(update, context)
    elif message == '🔑 ADMIN AREA':
        return admin_menu(update, context)
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
        context.user_data['expected'] = 'change_alias'
        return

    context.user_data['nodes'][
        context.user_data['selected_node_address']]['alias'] = alias

    # Send message
    update.message.reply_text('Got it! 👌')
    show_thornode_menu_new_msg(update, context)


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
    show_thornode_menu_new_msg(update, context)


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
    show_thornode_menu_new_msg(update, context)


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

    show_thornode_menu_new_msg(update, context)


def admin_menu(update, context):
    """
    Display admin area buttons
    """

    if update.effective_user.id not in ADMIN_USER_IDS:
        text = "❌ You are not an Admin! ❌"
        try_message_with_home_menu(context,
                                   chat_id=update.effective_chat.id,
                                   text=text)
        return

    show_admin_menu_new_msg(context, update.effective_chat.id)


def confirm_container_restart(update, context):
    """
    "Are you sure?" - "YES" | "NO"
    """

    query = update.callback_query
    container_name = query.data.split("-#")[1]

    keyboard = [[
        InlineKeyboardButton('YES ✅',
                             callback_data='restart_container-#' +
                             container_name),
        InlineKeyboardButton('NO ❌', callback_data='admin_menu')
    ]]
    text = '⚠️ Do you really want to restart the container *' + container_name + '*? ⚠️\n'

    return show_confirmation_menu(update=update, text=text, keyboard=keyboard)


def restart_container(update, context):
    """
    Restart the specified docker container
    """

    query = update.callback_query
    container_name = query.data.split("-#")[1]

    try:
        containers = get_running_docker_container()
    except ProcessLookupError:
        query.edit_message_text("Error while getting running docker container")
        show_admin_menu_new_msg(context, chat_id=update.effective_chat.id)
        return

    container_id = ''
    for container in containers:
        for name in container['Names']:
            if name == "/" + container_name:
                container_id = container['Id']
                break

    bash_command = DOCKER_CURL_CMD + ' -f -v -XPOST http://localhost/containers/' + container_id + '/restart'
    process = subprocess.Popen(bash_command.split(),
                               stdout=subprocess.PIPE,
                               stderr=subprocess.PIPE)
    output, error = process.communicate()

    if process.returncode:
        print("Restart docker container error: ", error)
        print("Return Code: ", process.returncode)
        query.edit_message_text("Error while restarting the docker container")
        show_admin_menu_new_msg(context, chat_id=update.effective_chat.id)
        return

    query.edit_message_text('Container\n*' + container_name +
                            '*\nsuccessfully restarted!',
                            parse_mode='markdown')
    show_admin_menu_new_msg(context=context, chat_id=update.effective_chat.id)


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

    bot = Updater(TELEGRAM_BOT_TOKEN,
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

import atexit

from telegram.ext.dispatcher import run_async
from telegram.ext import (
    Updater,
    CommandHandler,
    PicklePersistence,
    CallbackQueryHandler,
    MessageHandler,
    Filters
)

from constants import *
from helpers import *
from jobs import *


"""
######################################################################################################################################################
Debug Processes
######################################################################################################################################################
"""

if DEBUG:
    mock_api_process = subprocess.Popen(['python3', '-m', 'http.server', '8000', '--bind', '127.0.0.1'], cwd="test/")
    increase_block_height_process = subprocess.Popen(['python3', 'increase_block_height.py'], cwd="test/")


    def cleanup():
        mock_api_process.terminate()
        increase_block_height_process.terminate()


    atexit.register(cleanup)


"""
######################################################################################################################################################
BOT RESTART SETUP
######################################################################################################################################################
"""


def setup_existing_user(dispatcher):
    """
    Tasks to ensure smooth user experience for existing users upon Bot restart
    """

    chat_ids = dispatcher.user_data.keys()
    for chat_id in chat_ids:
        dispatcher.job_queue.run_repeating(thornode_checks, interval=30, context={
            'chat_id': chat_id, 'user_data': dispatcher.user_data[chat_id]
        })
        restart_message = 'Heil ok sæll!\n' \
                          'Me, your THORNode Bot, just got restarted on the server! 🤖\n' \
                          'To make sure you have the latest features, please start ' \
                          'a fresh chat with me by typing /start.'
        dispatcher.bot.send_message(chat_id, restart_message)


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
        context.job_queue.run_repeating(thornode_checks, interval=30, context={
            'chat_id': update.message.chat.id,
            'user_data': context.user_data
        })
        context.user_data['job_started'] = True
        context.user_data['nodes'] = {}

    text = 'Heil ok sæll! I am your THORNode Bot. 🤖\n' \
           'I will notify you about changes of your node\'s *Status*, *Bond* or *Slash Points*, ' \
           'if your *Block Height* gets stuck and if your *Midgard API* gets unhealthy!\n'
    if BINANCE_NODE_IP:
        text += 'Furthermore I notify you about changes of your *Binance Node\'s health*.\n'
    text += 'Moreover, in the Admin Area you can *restart any docker container* that runs alongside my container!'

    # Send message
    update.message.reply_text(text, parse_mode='markdown')
    show_home_menu(context=context, chat_id=update.message.chat.id)


@run_async
def thornode_menu(update, context):
    """
    Display all Buttons related to thornodes
    """

    query = update.callback_query
    query.answer()

    show_thornode_menu(context=None, chat_id=None, user_data=context.user_data, query=query)
    return THORNODE_MENU


@run_async
def confirm_add_all_thornodes(update, context):
    """
    Ask user if he really wants to add all available Thornodes
    """

    keyboard = [[
        InlineKeyboardButton('YES ✅', callback_data='add_all_thornodes'),
        InlineKeyboardButton('NO ❌', callback_data='back_to_thornode_menu')
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
        InlineKeyboardButton('NO ❌', callback_data='back_to_thornode_menu')
    ]]
    text = '⚠️ Do you really want to *remove all* THORNodes from your monitoring list? ⚠️'

    return show_confirmation_menu(update=update, text=text, keyboard=keyboard)


@run_async
def add_thornode(update, context):
    """
    Initiate a conversation and prompt for user input (thornode address).
    """

    # Enable message editing
    query = update.callback_query
    query.answer()

    text = 'What\'s the address of your THORNode? (enter /cancel to return to the menu)'

    # Send message
    query.edit_message_text(text)

    return WAIT_FOR_ADDRESS


@run_async
def handle_input(update, context):
    """
    Handle text input after an user has asked to add a new thornode.
    """

    # Assume text input is an address
    address = update.message.text

    node = get_thornode_object(address=address)

    if node is None:
        update.message.reply_text(
            '⛔️ I have not found a THORNode with this address! Please try another one. (enter /cancel to return to the menu)')
        return WAIT_FOR_ADDRESS

    # Update data
    context.user_data['nodes'][address] = {}
    context.user_data['nodes'][address]['status'] = node['status']
    context.user_data['nodes'][address]['bond'] = node['bond']
    context.user_data['nodes'][address]['slash_points'] = node['slash_points']
    context.user_data['nodes'][address]['last_notification_timestamp'] = datetime.timestamp(datetime.now())
    context.user_data['nodes'][address]['notification_timeout_in_seconds'] = INITIAL_NOTIFICATION_TIMEOUT

    # Send message
    update.message.reply_text('Got it! 👌')
    show_thornode_menu(context=context, chat_id=update.message.chat.id, user_data=context.user_data)

    return END


@run_async
def confirm_thornode_deletion(update, context):
    """
    Initiate process of thornode address removal
    """

    address = context.user_data['selected_node_address']

    keyboard = [[
        InlineKeyboardButton('YES ✅', callback_data='delete_thornode'),
        InlineKeyboardButton('NO ❌', callback_data='keep_thornode')
    ]]
    text = '⚠️ Do you really want to remove the address from your monitoring list? ⚠️' + address

    return show_confirmation_menu(update=update, text=text, keyboard=keyboard)


@run_async
def delete_thornode(update, context):
    """
    Remove selected address from the monitored thornodes
    """

    query = update.callback_query
    address = context.user_data['selected_node_address']

    del context.user_data['nodes'][address]

    text = "❌ Thornode address got deleted! ❌\n" + address
    query.answer(text)
    query.edit_message_text(text)
    show_thornode_menu(context=context, chat_id=update.effective_chat.id, user_data=context.user_data)
    return END


@run_async
def thornode_details(update, context):
    """
    Shows thornode detail buttons
    """

    query = update.callback_query
    query.answer()

    address = query.data.split("-")[1]
    context.user_data['selected_node_address'] = address

    return show_detail_menu(update=update, context=context)


@run_async
def back_to_home(update, context):
    """
    Return to home menu
    """

    query = update.callback_query
    # Answer so that the small clock when you click a button disappears
    query.answer()

    show_home_menu(context=context, chat_id=update.effective_chat.id, query=query)
    return END


@run_async
def back_to_thornode_menu(update, context):
    """
    Return to thornode menu
    """

    query = update.callback_query
    # Answer so that the small clock when you click a button disappears
    query.answer()

    show_thornode_menu(context=context, chat_id=update.effective_chat.id, user_data=context.user_data, query=query)
    return END


@run_async
def cancel(update, context):
    """
    Cancel any open conversation.
    """

    show_thornode_menu(context, chat_id=update.message.chat.id, user_data=context.user_data)
    return END


@run_async
def keep_thornode(update, context):
    """
    Do not remove thornode addess and return to detail menu
    """

    query = update.callback_query
    # Answer so that the small clock when you click a button disappears
    query.answer()
    return show_detail_menu(update=update, context=context)


@run_async
def add_all_thornodes(update, context):
    """
    Add all available Thornode addresses to users monitoring list
    """

    query = update.callback_query
    query.answer()

    nodes = get_thorchain_validators()

    for node in nodes:
        address = node['node_address']

        context.user_data['nodes'][address] = {}
        context.user_data['nodes'][address]['status'] = node['status']
        context.user_data['nodes'][address]['bond'] = node['bond']
        context.user_data['nodes'][address]['slash_points'] = node['slash_points']
        context.user_data['nodes'][address]['last_notification_timestamp'] = datetime.timestamp(datetime.now())
        context.user_data['nodes'][address]['notification_timeout_in_seconds'] = INITIAL_NOTIFICATION_TIMEOUT

    # Send message
    query.edit_message_text('Added all THORNodes! 👌')
    show_thornode_menu(context=context, chat_id=update.effective_chat.id, user_data=context.user_data)

    return END


@run_async
def delete_all_thornodes(update, context):
    """
    Delete all Thornode addresses from users monitoring list
    """

    query = update.callback_query
    query.answer

    addresses = []
    for address in context.user_data['nodes']:
        addresses.append(address)

    for address in addresses:
        del context.user_data['nodes'][address]

    text = '❌ Deleted all THORNodes! ❌'
    # Send message
    query.answer(text)
    query.edit_message_text(text)

    show_thornode_menu(context=context, chat_id=update.effective_chat.id, user_data=context.user_data)


@run_async
def admin_menu(update, context):
    """
    Display admin area buttons
    """

    query = update.callback_query

    if query.from_user.id not in ADMIN_USER_IDS:
        query.answer("❌ You are not an Admin! ❌", show_alert=True)
        return END
    else:
        query.answer()

    show_admin_menu(context=None, chat_id=None, query=query)
    return ADMIN_MENU

@run_async
def confirm_container_restart(update, context):
    """
    "Are you sure?" - "YES" | "NO"
    """

    query = update.callback_query
    container_name = query.data.split("-#")[1]

    keyboard = [[
        InlineKeyboardButton('YES ✅', callback_data='restart_container-#' + container_name),
        InlineKeyboardButton('NO ❌', callback_data='keep_container_running')
    ]]
    text = '⚠️ Do you really want to restart the container *' + container_name + '*? ⚠️\n'

    return show_confirmation_menu(update=update, text=text, keyboard=keyboard)

@run_async
def restart_container(update, context):
    """
    Restart the specified docker container
    """

    query = update.callback_query
    container_name = query.data.split("-#")[1]

    containers = get_running_docker_container()
    if containers == "ERROR":
        query.answer("Error while getting running docker container", show_alert=True)
        return ADMIN_MENU
    else:
        query.answer()

    container_id = ''
    for container in containers:
        for name in container['Names']:
            if name == "/" + container_name:
                container_id = container['Id']
                break

    bash_command = DOCKER_CURL_CMD + ' -f -v -XPOST http://localhost/containers/' + container_id + '/restart'
    process = subprocess.Popen(bash_command.split(), stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    output, error = process.communicate()

    if process.returncode:
        print("Restart docker container error: ", error)
        print("Return Code: ", process.returncode)
        return

    query.edit_message_text('Container\n*' + container_name + '*\nsuccessfully restarted!', parse_mode='markdown')
    show_admin_menu(context=context, chat_id=update.effective_chat.id)
    return ADMIN_MENU

@run_async
def keep_container_running(update, context):
    """
    Do nothing and return to Admin Area
    """

    query = update.callback_query
    # Answer so that the small clock when you click a button disappears
    query.answer()

    show_admin_menu(context=None, chat_id=None, query=query)
    return ADMIN_MENU


@run_async
def show_all_thorchain_nodes(update, context):
    """
    Show the status of all Thornodes in the whole Thorchain network
    """

    query = update.callback_query
    query.answer()

    nodes = get_thorchain_validators()

    text = "Status of all THORNodes in the THORChain network:\n\n"

    for node in nodes:
        text += 'THORNode: *' + node['node_address'] + '*\n' + \
           'Version: *' + node['version'] + '*\n' + \
           'Status: *' + node['status'].capitalize() + '*\n' + \
           'Bond: *' + tor_to_rune(int(node['bond'])) + '*\n' + \
           'Slash Points: ' + '*{:,}*'.format(int(node['slash_points'])) + '\n' \
           'Status Since: ' + '*{:,}*'.format(int(node['status_since'])) + '\n\n'

    # Send message
    query.edit_message_text(text, parse_mode='markdown')
    show_home_menu(context=context, chat_id=update.effective_chat.id)

    return END


"""
######################################################################################################################################################
Application
######################################################################################################################################################
"""


def main():
    """
    Init telegram bot, attach handlers and wait for incoming requests.
    """

    # Init telegram bot
    bot = Updater(TELEGRAM_BOT_TOKEN, persistence=PicklePersistence(filename='storage/session.data'), use_context=True)
    dispatcher = bot.dispatcher

    setup_existing_user(dispatcher=dispatcher)

    # Start job for health check
    dispatcher.job_queue.run_repeating(update_health_check_file, interval=5, context={})

    # Thornode Detail conversation handler
    thornode_detail_conversation = ConversationHandler(
        entry_points=[CallbackQueryHandler(thornode_details, pattern='^thornode_details')],
        states={
            WAIT_FOR_DETAIL: [
                CommandHandler('cancel', cancel),
                CallbackQueryHandler(confirm_thornode_deletion, pattern='^confirm_thornode_deletion$',
                                     pass_chat_data=True),
                CallbackQueryHandler(back_to_thornode_menu, pattern='^back_button$')],
            WAIT_FOR_CONFIRMATION: [
                CallbackQueryHandler(delete_thornode, pattern='^delete_thornode$'),
                CallbackQueryHandler(keep_thornode, pattern='^keep_thornode$')]},
        fallbacks=[],
        allow_reentry=True,
        map_to_parent={
            # Return on END of child to parents thornode menu
            END: THORNODE_MENU
        }
    )

    # Add Thornode conversation handler
    add_thornode_conversation = ConversationHandler(
        entry_points=[CallbackQueryHandler(add_thornode, pattern='^add_thornode$')],
        states={WAIT_FOR_ADDRESS: [
            CommandHandler('cancel', cancel),
            MessageHandler(Filters.text, handle_input, pass_job_queue=True, pass_chat_data=True)
        ]},
        fallbacks=[],
        allow_reentry=True,
        map_to_parent={
            # Return on END of child to parents thornode menu
            END: THORNODE_MENU
        }
    )

    # Add all Thornodes conversation handler
    add_all_thornodes_conversation = ConversationHandler(
        entry_points=[CallbackQueryHandler(confirm_add_all_thornodes, pattern='^confirm_add_all_thornodes$')],
        states={
            WAIT_FOR_CONFIRMATION: [
                CallbackQueryHandler(add_all_thornodes, pattern='^add_all_thornodes$'),
                CallbackQueryHandler(back_to_thornode_menu, pattern='^back_to_thornode_menu')]},
        fallbacks=[],
        allow_reentry=True,
        map_to_parent={
            # Return to parents thornode menu on END of child
            END: THORNODE_MENU
        }
    )

    # Delete all Thornodes conversation handler
    delete_all_thornodes_conversation = ConversationHandler(
        entry_points=[CallbackQueryHandler(confirm_delete_all_thornodes, pattern='^confirm_delete_all_thornodes$')],
        states={
            WAIT_FOR_CONFIRMATION: [
                CallbackQueryHandler(delete_all_thornodes, pattern='^delete_all_thornodes$'),
                CallbackQueryHandler(back_to_thornode_menu, pattern='^back_to_thornode_menu')]},
        fallbacks=[],
        allow_reentry=True,
        map_to_parent={
            # Return to parents thornode menu on END of child
            END: THORNODE_MENU
        }
    )

    # Define Thornode conversation handler
    thornode_conversation = ConversationHandler(
        entry_points=[CallbackQueryHandler(thornode_menu, pattern='^thornode_menu$')],
        states={THORNODE_MENU: [
            thornode_detail_conversation,
            add_thornode_conversation,
            add_all_thornodes_conversation,
            delete_all_thornodes_conversation,
            CallbackQueryHandler(back_to_home, pattern='^back_button$')
        ]},
        fallbacks=[],
        allow_reentry=True,
    )

    # Define Thornode conversation handler
    admin_conversation = ConversationHandler(
        entry_points=[CallbackQueryHandler(admin_menu, pattern='^admin_menu$')],
        states={
            ADMIN_MENU: [
                CallbackQueryHandler(confirm_container_restart, pattern='^container'),
                CallbackQueryHandler(back_to_home, pattern='^back_button$')],
            WAIT_FOR_CONFIRMATION: [
                CallbackQueryHandler(restart_container, pattern='^restart_container'),
                CallbackQueryHandler(keep_container_running, pattern='^keep_container_running$')]
        },
        fallbacks=[],
        allow_reentry=True,
    )

    # Define Network status conversation handler
    all_thorchain_nodes_conversation = ConversationHandler(
        entry_points=[CallbackQueryHandler(show_all_thorchain_nodes, pattern='^show_all_thorchain_nodes$')],
        states={},
        fallbacks=[],
        allow_reentry=True,
    )

    # Add start commandHandler handlers
    dispatcher.add_handler(CommandHandler('start', start))

    # Add conversationHandler
    dispatcher.add_handler(thornode_conversation)
    dispatcher.add_handler(admin_conversation)
    dispatcher.add_handler(all_thorchain_nodes_conversation)

    # Add error handler
    dispatcher.add_error_handler(error)

    # Start the bot
    bot.start_polling()
    logger.info('THORNode Bot is running ...')

    # Run the bot until you press Ctrl-C or the process receives SIGINT,
    # SIGTERM or SIGABRT. This should be used most of the time, since
    # start_polling() is non-blocking and will stop the bot gracefully.
    bot.idle()


if __name__ == '__main__':
    main()

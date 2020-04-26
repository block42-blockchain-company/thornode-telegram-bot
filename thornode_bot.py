import atexit
import os
import logging
import requests
from datetime import datetime
from subprocess import Popen

from telegram.ext.dispatcher import run_async
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Updater,
    CommandHandler,
    PicklePersistence,
    CallbackQueryHandler,
    MessageHandler,
    ConversationHandler,
    Filters
)

# Enable logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

"""
######################################################################################################################################################
Static & environment variables
######################################################################################################################################################
"""

TELEGRAM_BOT_TOKEN = os.environ['TELEGRAM_BOT_TOKEN']
NODE_IP = os.environ['NODE_IP'] if 'NODE_IP' in os.environ else 'localhost'
DEBUG = bool(os.environ['DEBUG'] == 'True') if 'DEBUG' in os.environ else False

"""
######################################################################################################################################################
Debug Processes
######################################################################################################################################################
"""


if DEBUG:
    mock_api_process = Popen(['python3', '-m', 'http.server', '8000', '--bind', '127.0.0.1'], cwd="test/")
    increase_block_height_process = Popen(['python3', 'increase_block_height.py'], cwd="test/")

    def cleanup():
        mock_api_process.terminate()
        increase_block_height_process.terminate()
    atexit.register(cleanup)

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

    # Restart job for user
    if 'job_started' not in context.user_data:
        context.job_queue.run_repeating(node_checks, interval=30, context={
            'chat_id': update.message.chat.id,
            'user_data': context.user_data
        })
        context.user_data['job_started'] = True

    text = 'Heil ok sæll! I am your THORNode Bot. 🤖\n' + \
           'I will notify you about changes of your node\'s *Status*, *Bond* or *Slash Points*, ' \
           'if your *Block Height* gets stuck and if your *Midgard API* gets unhealthy!'

    # Send message
    update.message.reply_text(text, parse_mode='markdown')
    show_home_buttons(context, chat_id=update.message.chat.id, user_data=context.user_data)


@run_async
def add_thornode(update, context):
    """
    Initiate a conversation and prompt for user input (thornode address).
    """

    # Enable message editing
    query = update.callback_query
    query.answer()

    text = ''

    text += 'What\'s the address of your THORNode? (enter /cancel to return to the menu)'

    # Send message
    query.edit_message_text(text)

    return WAIT_FOR_USER_INPUT


@run_async
def show_stats(update, context):
    """
    Send thornode stats if a valid address is available.
    """

    # Enable message editing
    query = update.callback_query
    query.answer()
    address = query.data.split("-")[1]

    text = 'THORNode: ' + address + '\n' + \
           'Status: ' + context.user_data[address]['status'].capitalize() + '\n' + \
           'Bond: ' + '{:,} RUNE'.format(int(context.user_data[address]['bond'])) + '\n' + \
           'Slash Points: ' + '{:,}'.format(int(context.user_data[address]['slash_points']))

    # Send message
    query.edit_message_text(text)
    show_home_buttons(context, chat_id=update.effective_chat.id, user_data=context.user_data)

    return ConversationHandler.END


@run_async
def handle_input(update, context):
    """
    Handle text input after an user has asked to add a new thornode.
    """

    # Assume text input is an address
    address = update.message.text

    node = get_node_object(address=address)

    if node is None:
        update.message.reply_text('⛔️ I have not found a THORNode with this address! Please try another one. (enter /cancel to return to the menu)')
        return WAIT_FOR_USER_INPUT

    # Update data
    context.user_data[address] = {}
    context.user_data[address]['status'] = node['status']
    context.user_data[address]['bond'] = node['bond']
    context.user_data[address]['slash_points'] = node['slash_points']
    
    # Send message
    update.message.reply_text('Got it! 👌')
    show_home_buttons(context, chat_id=update.message.chat.id, user_data=context.user_data)

    return ConversationHandler.END


@run_async
def thornode_details(update, context):
    """
        Shows thornode detail buttons
    """

    query = update.callback_query
    query.answer()
    address = query.data.split("-")[1]

    keyboard = [[
        InlineKeyboardButton('Show THORNode Stats', callback_data='show_stats-' + address),
        InlineKeyboardButton('<< Back', callback_data='back_button')
    ]]

    # Send message
    text = "You chose\n" + address + "\nWhat do you want to do with that Node?"
    context.bot.send_message(query.message.chat_id, text, reply_markup=InlineKeyboardMarkup(keyboard))
    return WAIT_FOR_DETAIL


@run_async
def back_button(update, context):
    """
        Return to home menu
    """

    query = update.callback_query
    # Answer so that the small clock when you click a button disappears
    query.answer()

    show_home_buttons(context, chat_id=update.effective_chat.id, user_data=context.user_data)
    return ConversationHandler.END


@run_async
def cancel(update, context):
    """
    Cancel any open conversation.
    """

    show_home_buttons(context, chat_id=update.message.chat.id, user_data=context.user_data)
    return ConversationHandler.END


"""
######################################################################################################################################################
Jobs
######################################################################################################################################################
"""


def node_checks(context):
    """
        periodic checks of various stats
    """

    check_thornodes(context)
    check_block_height(context)
    check_midgard_api(context)


def check_thornodes(context):
    """
    Check the thornode for any changes.
    """

    chat_id = context.job.context['chat_id']
    user_data = context.job.context['user_data']

    # flag to show home buttons or not
    message_sent = False

    # iterate through all keys
    for address in user_data.keys():
        # Filter out the thornode addresses
        if "thor" in address:
            node = get_node_object(address=address)

            if node is None:
                text = 'THORNode is not active anymore! 💀' + '\n' + \
                       'Address: ' + user_data[address]['address'] + '\n\n' + \
                       'Please enter another THORNode address.'

                del user_data[address]
                # Send message
                context.bot.send_message(chat_id, text)
                message_sent = True
                continue

            # Check which node fields have changed
            changed_fields = [field for field in ['status', 'bond', 'slash_points'] if user_data[address][field] != node[field]]

            # Check if there are any changes
            if len(changed_fields) > 0:
                text = 'THORNode: ' + address + '\n' + \
                       'Status: ' + user_data[address]['status'].capitalize() + \
                       ' ➡️ ' + node['status'].capitalize() + '\n' + \
                       'Bond: ' + '{:,} RUNE'.format(int(user_data[address]['bond'])) + \
                       ' ➡️ ' + '{:,} RUNE'.format(int(node['bond'])) + '\n' + \
                       'Slash Points: ' + '{:,}'.format(int(user_data[address]['slash_points'])) + \
                       ' ➡️ ' + '{:,}'.format(int(node['slash_points']))

                # Update data
                user_data[address]['status'] = node['status']
                user_data[address]['bond'] = node['bond']
                user_data[address]['slash_points'] = node['slash_points']

                # Send message
                context.bot.send_message(chat_id, text)
                message_sent = True

    if message_sent:
        show_home_buttons(context, chat_id=chat_id, user_data=user_data)


def check_block_height(context):
    """
        Make sure the block height increases
    """

    chat_id = context.job.context['chat_id']
    user_data = context.job.context['user_data']

    block_height = get_block_height()

    # Check if block height got stuck
    if 'block_height' in user_data and block_height <= user_data['block_height']:

        # Increase stuck count to know if we already sent a notification
        user_data['block_height_stuck_count'] += 1
    else:
        # Check if we have to send a notification that the Height increases again
        if 'block_height_stuck_count' in user_data and user_data['block_height_stuck_count'] > 0:
            text = 'Block height is increasing again! 👌' + '\n' + \
                   'IP: ' + NODE_IP + '\n' + \
                   'Block height now at: ' + block_height + '\n'
            context.bot.send_message(chat_id, text)
            user_data['block_height_stuck_count'] = -1
        else:
            user_data['block_height_stuck_count'] = 0

    # Set current block height
    user_data['block_height'] = block_height

    # If it just got stuck send a message
    if user_data['block_height_stuck_count'] == 1:
        text = 'Block height is not increasing anymore! 💀' + '\n' + \
               'IP: ' + NODE_IP + '\n' + \
               'Block height stuck at: ' + block_height + '\n\n' + \
               'Please check your Thornode immediately!'
        context.bot.send_message(chat_id, text)

    # Show buttons if there were changes or block height just got (un)stuck
    # Stuck count:
    # 0 == everthings alright
    # 1 == just got stuck
    # -1 == just got unstuck
    # > 1 == still stuck

    if user_data['block_height_stuck_count'] == 1 or user_data['block_height_stuck_count'] == -1:
        show_home_buttons(context, chat_id=chat_id, user_data=user_data)


def check_midgard_api(context):
    """
        Check that Midgard API is ok
    """
    chat_id = context.job.context['chat_id']
    user_data = context.job.context['user_data']

    if 'is_midgard_healthy' not in user_data:
        user_data['is_midgard_healthy'] = True

    if user_data['is_midgard_healthy'] == True and not is_midgard_healthy():
        user_data['is_midgard_healthy'] = False
        text = 'Midgard API is not healthy anymore! 💀' + '\n' + \
               'IP: ' + NODE_IP + '\n\n' + \
               'Please check your Thornode immediately!'
        context.bot.send_message(chat_id, text)
        show_home_buttons(context, chat_id=chat_id)
    elif user_data['is_midgard_healthy'] == False and is_midgard_healthy():
        user_data['is_midgard_healthy'] = True
        text = 'Midgard API is healthy again! 👌' + '\n' + \
               'IP: ' + NODE_IP + '\n'
        context.bot.send_message(chat_id, text)
        show_home_buttons(context, chat_id=chat_id, user_data=user_data)


def healthy(context):
    """
        Write timestamp into health.check file for the health check
    """

    with open('storage/health.check', 'w') as healthcheck_file:
        timestamp = datetime.timestamp(datetime.now())
        healthcheck_file.write(str(timestamp))


"""
######################################################################################################################################################
Helpers
######################################################################################################################################################
"""


def show_home_buttons(context, chat_id, user_data):
    """
    Show buttons for supported actions.
    """
    keyboard = [[]]

    for key in user_data.keys():
        if "thor" in key:
            keyboard.append([InlineKeyboardButton(key, callback_data='thornode_details-' + key)])

    keyboard.append([InlineKeyboardButton('Add THORNode', callback_data='add_thornode')])

    # Send message
    context.bot.send_message(chat_id, 'Choose an address from the list below or add one:', reply_markup=InlineKeyboardMarkup(keyboard))


def get_node_object(address):
    """
        Query nodeaccounts endpoints and return the Thornode object
    """

    while True:
        response = requests.get(url=get_nodeaccounts_endpoint())
        if response.status_code == 200:
            break

    nodes = response.json()

    # get the right node
    node = next(filter(lambda node: node['node_address'] == address, nodes), None)
    return node


def get_block_height():
    """
        Return block height of your Thornode
    """

    while True:
        response = requests.get(url=get_status_endpoint())
        if response.status_code == 200:
            break

    status = response.json()
    return status['result']['sync_info']['latest_block_height']


def is_midgard_healthy():
    """
        Return status of 
    """

    response = requests.get(url=get_midgard_endpoint())
    if response.status_code != 200:
        return False

    if response.text == '"OK"':
        return True
    else:
        return False


def get_nodeaccounts_endpoint():
    """
    Return the nodeaccounts endpoint to query data from.
    """

    return 'http://localhost:8000/nodeaccounts.json' if DEBUG else 'http://' + NODE_IP + '1317/thorchain/nodeaccounts'


def get_status_endpoint():
    """
       Return the endpoint for block height checks
    """

    return 'http://localhost:8000/status.json' if DEBUG else 'http://' + NODE_IP + ':26657/status'


def get_midgard_endpoint():
    """
        Return the endpoint for Midgard API check
    """

    return 'http://localhost:8000/midgard.json' if DEBUG else 'http://' + NODE_IP + ':8080/v1/health'


def error(update, context):
    """
    Log error.
    """

    logger.warning('Update "%s" caused error: %s', update, context.error)


"""
######################################################################################################################################################
Application
######################################################################################################################################################
"""

# Conversation state(s)
WAIT_FOR_USER_INPUT,WAIT_FOR_DETAIL = range(2)


def main():
    """
    Init telegram bot, attach handlers and wait for incoming requests.
    """

    # Init telegram bot
    bot = Updater(TELEGRAM_BOT_TOKEN, persistence=PicklePersistence(filename='storage/session.data'), use_context=True)
    dispatcher = bot.dispatcher

    # Restart jobs for all users
    chat_ids = dispatcher.user_data.keys()
    for chat_id in chat_ids:
        dispatcher.job_queue.run_repeating(node_checks, interval=30, context={
            'chat_id': chat_id, 'user_data': dispatcher.user_data[chat_id]
        })

    # Start job for health check
    dispatcher.job_queue.run_repeating(healthy, interval=5, context={})

    # Add command handlers
    dispatcher.add_handler(CommandHandler('start', start))

    # Add Thornode conversation handler
    dispatcher.add_handler(ConversationHandler(
        entry_points=[CallbackQueryHandler(add_thornode, pattern='^add_thornode$')],
        states={WAIT_FOR_USER_INPUT: [
            CommandHandler('cancel', cancel),
            CallbackQueryHandler(add_thornode, pattern='^add_thornode$'),
            MessageHandler(Filters.text, handle_input, pass_job_queue=True, pass_chat_data=True)
        ]},
        fallbacks=[]
    ))
    
    # Thornode  Detail conversation handler
    dispatcher.add_handler(ConversationHandler(
        entry_points=[CallbackQueryHandler(thornode_details, pattern='^thornode_details-')],
        states={WAIT_FOR_DETAIL: [
            CommandHandler('cancel', cancel),
            CallbackQueryHandler(thornode_details, pattern='^thornode_details-'),
            CallbackQueryHandler(show_stats, pattern='^show_stats'),
            CallbackQueryHandler(back_button, pattern='^back_button$')
        ]},
        fallbacks=[]
    ))

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

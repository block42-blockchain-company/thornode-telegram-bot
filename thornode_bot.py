import os
import random
import logging
import requests

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
DEBUG = bool(os.environ['DEBUG'] == 'True') if 'DEBUG' in os.environ else False

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
        context.job_queue.run_repeating(check_thornode, interval=30, context={
            'chat_id': update.message.chat.id,
            'user_data': context.user_data
        })
        context.user_data['job_started'] = True

    text = 'Heil ok sæll! I am your THORNode Bot. 🤖\n' + \
           'I will notify you about changes of your node\'s *Status*, *Bond* or *Slash Points*!\n'

    # Send message
    update.message.reply_text(text, parse_mode='markdown')
    show_action_buttons(context, chat_id=update.message.chat.id)


@run_async
def add_thornode(update, context):
    """
    Initiate a conversation and prompt for user input (thornode address).
    """

    # Enable message editing
    query = update.callback_query
    query.answer()

    text = ''

    if 'address_valid' in context.user_data and context.user_data['address_valid'] is True:
        text += '⚠️ This will override this THORNode: ' + context.user_data['address'] + '\n\n'

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

    # Check if user has set a thornode address
    if 'address' not in context.user_data:
        text = 'You have not told me about your THORNode yet. Please add one!'
        query.edit_message_text(text)
        show_action_buttons(context, update.effective_chat.id)
        return ConversationHandler.END

    # Check if thornode address is valid
    if context.user_data['address_valid'] is True:
        text = 'THORNode: ' + context.user_data['address'] + '\n' + \
               'Status: ' + context.user_data['status'].capitalize() + '\n' + \
               'Bond: ' + '{:,} RUNE'.format(int(context.user_data['bond'])) + '\n' + \
               'Slash Points: ' + '{:,}'.format(int(context.user_data['slash_points']))
    else:
        text = 'THORNode is not active anymore! 💀' + '\n' + \
               'Address: ' + context.user_data['address'] + '\n\n' + \
               'Please enter another THORNode address.'

    # Send message
    query.edit_message_text(text)
    show_action_buttons(context, chat_id=update.effective_chat.id)

    return ConversationHandler.END


@run_async
def handle_input(update, context):
    """
    Handle text input after an user has asked to add a new thornode.
    """

    # Assume text input is an address
    address = update.message.text

    # Try to get node based on given address
    while True:
        response = requests.get(url=get_endpoint())
        if response.status_code == 200:
            break

    nodes = response.json()
    node = next(filter(lambda node: node['node_address'] == address, nodes), None)

    if node is None:
        update.message.reply_text('⛔️ I have not found a THORNode with this address! Please try another one. (enter /cancel to return to the menu)')
        return WAIT_FOR_USER_INPUT

    # Update data
    context.user_data['address'] = address
    context.user_data['address_valid'] = True
    context.user_data['status'] = node['status']
    context.user_data['bond'] = node['bond']
    context.user_data['slash_points'] = node['slash_points']

    # Send message
    update.message.reply_text('Got it! 👌')
    show_action_buttons(context, chat_id=update.message.chat.id)

    return ConversationHandler.END


@run_async
def cancel(update, context):
    """
    Cancel any open conversation.
    """

    show_action_buttons(context, chat_id=update.message.chat.id)
    return ConversationHandler.END


"""
######################################################################################################################################################
Jobs
######################################################################################################################################################
"""


def check_thornode(context):
    """
    Check the thornode for any changes.
    """

    chat_id = context.job.context['chat_id']
    user_data = context.job.context['user_data']

    # Check if address is valid
    if 'address_valid' not in user_data or user_data['address_valid'] is False:
        return

    address = user_data['address']

    # Try to get node based on given address
    while True:
        response = requests.get(url=get_endpoint())
        if response.status_code == 200:
            break

    nodes = response.json()
    node = next(filter(lambda node: node['node_address'] == address, nodes), None)

    if node is None:
        text = 'THORNode is not active anymore! 💀' + '\n' + \
               'Address: ' + user_data['address'] + '\n\n' + \
               'Please enter another THORNode address.'

        # Update data
        user_data['address_valid'] = False

        # Send message
        context.bot.send_message(chat_id, text)
        show_action_buttons(context, chat_id=chat_id)

        return

    # Check which node fields have changed
    changed_fields = [field for field in ['status', 'bond', 'slash_points'] if user_data[field] != node[field]]

    # Check if there are any changes
    if len(changed_fields) > 0:
        text = 'THORNode: ' + user_data['address'] + '\n' + \
               'Status: ' + user_data['status'].capitalize() + ' ➡️ ' + node['status'].capitalize() + '\n' + \
               'Bond: ' + '{:,} RUNE'.format(int(user_data['bond'])) + ' ➡️ ' + '{:,} RUNE'.format(int(node['bond'])) + '\n' + \
               'Slash Points: ' + '{:,}'.format(int(user_data['slash_points'])) + ' ➡️ ' + '{:,}'.format(int(node['slash_points']))

        # Update data
        user_data['status'] = node['status']
        user_data['bond'] = node['bond']
        user_data['slash_points'] = node['slash_points']

        # Send message
        context.bot.send_message(chat_id, text)
        show_action_buttons(context, chat_id=chat_id)


"""
######################################################################################################################################################
Helpers
######################################################################################################################################################
"""


def show_action_buttons(context, chat_id):
    """
    Show buttons for supported actions.
    """

    keyboard = [[
        InlineKeyboardButton('Add THORNode', callback_data='add_thornode'),
        InlineKeyboardButton('Show THORNode Stats', callback_data='show_stats')
    ]]

    # Send message
    context.bot.send_message(chat_id, 'What do you want to do?', reply_markup=InlineKeyboardMarkup(keyboard))


def get_endpoint():
    """
    Return a endpoint to query data from.
    """

    if DEBUG:
        return 'http://localhost:8000/nodeaccounts.json'

    endpoints = requests.get('https://testnet-seed.thorchain.info').json()
    random_endpoint = endpoints[random.randrange(0, len(endpoints))]

    return 'http://' + random_endpoint + ':1317/thorchain/nodeaccounts'


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
WAIT_FOR_USER_INPUT = range(1)


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
        dispatcher.job_queue.run_repeating(check_thornode, interval=5, context={
            'chat_id': chat_id, 'user_data': dispatcher.user_data[chat_id]
        })

    # Add command handlers
    dispatcher.add_handler(CommandHandler('start', start))
    dispatcher.add_handler(CallbackQueryHandler(show_stats, pattern='^show_stats$'))

    # Add conversation handler to rule them all
    dispatcher.add_handler(ConversationHandler(
        entry_points=[CallbackQueryHandler(add_thornode, pattern='^add_thornode$')],
        states={WAIT_FOR_USER_INPUT: [
            CommandHandler('cancel', cancel),
            CallbackQueryHandler(add_thornode, pattern='^add_thornode$'),
            MessageHandler(Filters.text, handle_input, pass_job_queue=True, pass_chat_data=True)
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

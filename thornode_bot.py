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

NODE_FIELDS = ['status', 'bond', 'slash_points']

# Get environment variables
TELEGRAM_BOT_TOKEN = os.environ['TELEGRAM_BOT_TOKEN']
DEBUG = os.environ['DEBUG'] if 'DEBUG' in os.environ is not None else True

# Enable logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)


@run_async
def start(update, context):
    update.message.reply_text(
        'Heil ok sæll! I am your THORNode Bot. 🤖\n' +
        'I will notify you about changes of your node\'s *Status*, *Bond* or *Slash Points*!\n',
        parse_mode='markdown'
    )

    if 'job_started' not in context.user_data:
        context.job_queue.run_repeating(check_node, 30, context={
            'chat_id': update.message.chat.id,
            'user_data': context.user_data
        })
        context.user_data['job_started'] = True

    show_actions(context, chat_id=update.message.chat.id)


@run_async
def set_address(update, context):
    query = update.callback_query
    query.answer()

    text = ''

    if 'job_running' in context.user_data and context.user_data['job_running']:
        text += '⚠️ This will override this THORNode: ' + context.user_data['address'] + '\n\n'

    text += 'What\'s the address of your THORNode? (enter /cancel to return to the menu)'

    query.edit_message_text(text)

    return WAIT_FOR_USER_INPUT


@run_async
def get_stats(update, context):
    query = update.callback_query
    query.answer()

    text = 'You have not told me about your THORNode yet. Please add one!'

    if 'address' in context.user_data and context.user_data['job_running']:
        text = 'THORNode: ' + context.user_data['address'] + '\n' + \
               'Status: ' + context.user_data['status'].capitalize() + '\n' + \
               'Bond: ' + '{:,} RUNE'.format(int(context.user_data['bond'])) + '\n' + \
               'Slash Points: ' + '{:,}'.format(int(context.user_data['slash_points']))
    elif 'address' in context.user_data and not context.user_data['job_running']:
        text = 'THORnode is not active anymore! 💀' + '\n' + \
               'Address: ' + context.user_data['address'] + '\n\n' + \
               'Please enter another THORNode address.'

    query.edit_message_text(text)
    show_actions(context, update.effective_chat.id)


@run_async
def cancel(update, context):
    show_actions(context, update.message.chat.id)
    return ConversationHandler.END


@run_async
def address_received(update, context):
    address = update.message.text

    url = get_rand_node_url()
    all_nodes_json = requests.get(url).json()
    node = get_thor_node_object(all_nodes_json, address)

    if node is None:
        update.message.reply_text('⛔️ I have not found a THORNode with this address! Please try another one. (enter /cancel to return to the menu)')
        return WAIT_FOR_USER_INPUT

    context.user_data['address'] = address
    for field in NODE_FIELDS:
        context.user_data[field] = node[field]

    update.message.reply_text('Got it! 👌')

    context.user_data['job_running'] = True

    # TODO: Show stats right away
    #get_stats(update, context)
    show_actions(context, update.message.chat.id)

    return ConversationHandler.END


def show_actions(context, chat_id):
    keyboard = [[
        InlineKeyboardButton('Add THORNode', callback_data='add_thornode'),
        InlineKeyboardButton('Show THORNode Stats', callback_data='show_stats')
    ]]
    context.bot.send_message(chat_id, 'What do you want to do?', reply_markup=InlineKeyboardMarkup(keyboard))


@run_async
def error(update, context):
    """Log Errors caused by Updates."""
    logger.warning('Update "%s" caused error "%s"', update, context.error)


def get_rand_node_url():
    endpoints = requests.get('https://testnet-seed.thorchain.info').json()
    random_endpoint = endpoints[random.randrange(0, len(endpoints))]
    return 'http://localhost:8000/nodeaccounts.json' if DEBUG else 'http://' + random_endpoint + ':1317/thorchain/nodeaccounts'


def get_thor_node_object(all_nodes_json, address):
    for i in range(0, len(all_nodes_json)):
        if all_nodes_json[i]['node_address'] == address:
            return all_nodes_json[i]

    return None


# Jobs already have their own thread each, we don't need to set @run_async
def check_node(context):
    chat_id = context.job.context['chat_id']
    user_data = context.job.context['user_data']

    if 'job_running' not in user_data or user_data['job_running'] is False:
        return

    address = user_data['address']

    url = get_rand_node_url()
    all_nodes_json = requests.get(url).json()
    new_user_data = get_thor_node_object(all_nodes_json, address)

    if new_user_data is None:
        context.bot.send_message(chat_id,
                                 'THORnode is not active anymore! 💀' + '\n' +
                                 'Address: ' + context.user_data['address'] + '\n\n' +
                                 'Please enter another THORNode address.'
                                 )
        user_data['job_running'] = False
        show_actions(context, chat_id)
        return

    changed_values = False
    for field in NODE_FIELDS:
        if user_data[field] != new_user_data[field]:
            changed_values = True

    if changed_values:
        text = 'THORNode: ' + user_data['address'] + '\n' + \
               'Status: ' + user_data['status'].capitalize() + ' ➡️ ' + new_user_data['status'].capitalize() + '\n' + \
               'Bond: ' + '{:,} RUNE'.format(int(user_data['bond'])) + ' ➡️ ' + '{:,} RUNE'.format(int(new_user_data['bond'])) + '\n' + \
               'Slash Points: ' + '{:,}'.format(int(user_data['slash_points'])) + ' ➡️ ' + '{:,}'.format(int(new_user_data['slash_points']))

        # Update user data
        user_data['status'] = new_user_data['status']
        user_data['bond'] = new_user_data['bond']
        user_data['slash_points'] = new_user_data['slash_points']

        context.bot.send_message(chat_id, text)
        show_actions(context, chat_id)


def start_monitoring_jobs(dp):
    chat_ids = dp.user_data.keys()

    for chat_id in chat_ids:
        dp.job_queue.run_repeating(check_node, 30, context={
            'chat_id': chat_id, 'user_data': dp.user_data[chat_id]
        })


# Conversation state(s)
WAIT_FOR_USER_INPUT = range(1)


def main():
    # Init telegram bot
    bot = Updater(TELEGRAM_BOT_TOKEN, persistence=PicklePersistence(filename='storage/session.data'), use_context=True)
    dispatcher = bot.dispatcher

    # Start a check_node job for everyone who ever used the bot
    start_monitoring_jobs(dispatcher)

    dispatcher.add_handler(CommandHandler('start', start))
    dispatcher.add_handler(CallbackQueryHandler(get_stats, pattern='^show_stats$'))

    conversation_handler = ConversationHandler(
        entry_points=[CallbackQueryHandler(set_address, pattern='^add_thornode$')],
        states={WAIT_FOR_USER_INPUT: [
            CommandHandler('cancel', cancel),
            CallbackQueryHandler(set_address, pattern='^add_thornode$'),
            MessageHandler(Filters.text, address_received, pass_job_queue=True, pass_chat_data=True)
        ]},
        fallbacks=[]
    )

    # Add conversation handler to rule them all
    dispatcher.add_handler(conversation_handler)

    # Log all errors
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

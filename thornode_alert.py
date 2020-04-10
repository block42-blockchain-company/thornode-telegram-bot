import logging
import random
import requests

from constants import *

from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (Updater, CommandHandler, PicklePersistence, CallbackQueryHandler, MessageHandler,
                          ConversationHandler, Filters)

from telegram.ext.dispatcher import run_async

# Enable logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)

logger = logging.getLogger(__name__)

# Give all functions that are registered Handlers in the dispatcher their own thread
@run_async
def start(update, context):
    update.message.reply_text(
        'Heil ok sæll! 😁\n'
        'This is the Telegram Alert Bot for THORnodes of THORchain.\n\n'
        'Enter the address of a THORnode, and the Bot will notify you if there is a change in the nodes status, bond or slash_points.\n')

    if 'job_started' not in context.user_data:
        context.job_queue.run_repeating(check_node, 30,
                                        context={"chat_id": update.message.chat.id, "user_data": context.user_data})
        context.user_data['job_started'] = True

    show_actions(context, update.message.chat.id)


@run_async
def set_address(update, context):
    query = update.callback_query
    query.answer()
    text = 'Please send me the address of the THORnode that you want to monitor!'
    if 'job_running' in context.user_data and context.user_data['job_running']:
        text += '\nCurrently you watch this THORnode address: ' + context.user_data['address']

    text += '\n\n(Enter /cancel to return to the menu)'

    query.edit_message_text(text)
    return TYPING_ADDRESS


@run_async
def get_stats(update, context):
    query = update.callback_query
    query.answer()

    if 'address' not in context.user_data:
        text = ('You did not set any THORnode address yet!\n Please set an address before querying its stats.')
    elif 'address' in context.user_data and context.user_data['job_running']:
        text = ('The address you listen to is: ' + context.user_data["address"] +
                '\nCurrent status: ' + context.user_data["status"] +
                '\nCurrent bond: ' + context.user_data["bond"] +
                '\nCurrent slash_points: ' + context.user_data["slash_points"])
    elif 'address' in context.user_data and not context.user_data['job_running']:
        text = ('The THORnode which address which you previously set is not active anymore.' +
                '\nYour inactive THORnode address: ' + context.user_data['address'] +
                '\n\nPlease set an address of an active THORnode!')

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

    request = requests.get(url)
    all_nodes_json = request.json()

    node = get_thor_node_object(all_nodes_json, address)
    if node is None:
        update.message.reply_text('⛔️ The THORnode address you entered does not exist! ⛔️\n'
                                  '                      Please try again.\n' +
                                  '(Enter /cancel to return to the menu)')
        return TYPING_ADDRESS

    context.user_data["address"] = address
    for field in NODE_FIELDS:
        context.user_data[field] = node[field]

    text = 'The address you monitor is: ' + address
    for field in NODE_FIELDS:
        text += '\nCurrent ' + field + ': ' + node[field]
    update.message.reply_text(text)

    context.user_data['job_running'] = True
    show_actions(context, update.message.chat.id)
    return ConversationHandler.END


def show_actions(context, chat_id):
    keyboard = [[InlineKeyboardButton("set Address", callback_data='set Address'),
                 InlineKeyboardButton("get Stats", callback_data='get Stats')]]
    context.bot.send_message(chat_id, 'Choose an action:', reply_markup=InlineKeyboardMarkup(keyboard))


@run_async
def error(update, context):
    """Log Errors caused by Updates."""
    logger.warning('Update "%s" caused error "%s"', update, context.error)


def get_rand_node_url():
    url = "https://testnet-seed.thorchain.info/"
    request = requests.get(url)
    data = request.json()

    randNodeIndex = random.randrange(0, len(data))
    randNode = data[randNodeIndex]

    return HARDCODED_LOCAL_NODE
    return 'http://' + randNode + ':1317/thorchain/nodeaccounts'



def get_thor_node_object(all_nodes_json, address):
    for i in range(0, len(all_nodes_json)):
        if all_nodes_json[i]["node_address"] == address:
            return all_nodes_json[i]
    return None

# Jobs already have their own thread each, we don't need to set @run_async
def check_node(context):
    chat_id = context.job.context["chat_id"]
    user_data = context.job.context["user_data"]

    if 'job_running' not in user_data or user_data['job_running'] is False:
        return

    address = user_data['address']
    url = get_rand_node_url()

    request = requests.get(url)
    all_nodes_json = request.json()

    node = get_thor_node_object(all_nodes_json, address)
    if node is None:
        context.bot.send_message(chat_id, '⛔️ The THORnode you monitor is not active anymore! ⛔️\n'
                                          '                Please set a new THORnode address.')
        user_data['job_running'] = False
        show_actions(context, chat_id)
        return

    changed_values = False
    text = ''
    for field in NODE_FIELDS:
        if user_data[field] != node[field]:
            changed_values = True
            text += field + ' changed! 💥\n'

    if changed_values:
        text += '\n THORnode address: ' + address + '\n'
        for field in NODE_FIELDS:
            text += '\n' + field + ': ' + user_data[field] + ' ➡️ ' + node[field]
            user_data[field] = node[field]

        context.bot.send_message(chat_id, text)
        show_actions(context, chat_id)


def start_monitoring_jobs(dp):
    chat_ids = dp.user_data.keys()
    for chat_id in chat_ids:
        dp.job_queue.run_repeating(check_node, 30,
                                   context={"chat_id": chat_id, "user_data": dp.user_data[chat_id]})


def main():
    my_persistence = PicklePersistence(filename='session_data/session_data')
    updater = Updater(TELEGRAM_TOKEN, persistence=my_persistence, use_context=True)

    # Get the dispatcher to register handlers
    dp = updater.dispatcher

    # start a check_node job for everyone who ever used the bot
    start_monitoring_jobs(dp)

    dp.add_handler(CommandHandler('start', start))
    dp.add_handler(CallbackQueryHandler(get_stats, pattern='^' + 'get Stats' + '$'))

    conv_handler = ConversationHandler(
        entry_points=[CallbackQueryHandler(set_address, pattern='^' + 'set Address' + '$')],

        states={
            TYPING_ADDRESS: [CommandHandler('cancel', cancel),
                             CallbackQueryHandler(set_address, pattern='^' + 'set Address' + '$'),
                             MessageHandler(Filters.text, address_received,
                                            pass_job_queue=True,
                                            pass_chat_data=True)]
        },
        fallbacks=[]
    )

    # add conversation handler to rule them all
    dp.add_handler(conv_handler)

    # log all errors
    dp.add_error_handler(error)

    # Start the Bot
    updater.start_polling()
    logger.info('THORnode Telegram Alert Bot is running...')

    # Run the bot until you press Ctrl-C or the process receives SIGINT,
    # SIGTERM or SIGABRT. This should be used most of the time, since
    # start_polling() is non-blocking and will stop the bot gracefully.
    updater.idle()


if __name__ == '__main__':
    main()

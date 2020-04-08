import logging
import os
import random
import requests
import json

from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (Updater, CommandHandler, PicklePersistence, CallbackQueryHandler, MessageHandler,
                          ConversationHandler, Filters)

# Enable logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)

logger = logging.getLogger(__name__)

CHOOSING, TYPING_ADDRESS = range(2)

telegram_token = os.environ["TELEGRAM_TOKEN"]

node_fields = ["status", "bond", "slash_points"]


def start(update, context):
    update.message.reply_text(
        'Heil ok sæll! 😁\n'
        'This is the Telegram Alert Bot for THORnodes of THORchain.\n\n'
        'Enter the address of a THORnode, and the Bot will notify you if there is a change in the nodes status, bond or slash_points.\n')

    if 'job_started' not in context.user_data:
        context.job_queue.run_repeating(checkNode, 30,
                                        context={"chat_id": update.message.chat.id, "user_data": context.user_data})
        context.user_data['job_started'] = True

    return show_actions(context, update.message.chat.id)


def set_address(update, context):
    query = update.callback_query
    query.answer()
    text = 'Please send me the address of the THORnode that you want to monitor!'
    if 'job_running' in context.user_data and context.user_data['job_running']:
        text += '\nCurrently you watch this THORnode address: ' + context.user_data['address']

    text += '\n\n(Enter /cancel to return to the menu)'

    query.edit_message_text(text)
    return TYPING_ADDRESS


def cancel(update, context):
    return show_actions(context, update.message.chat.id)


def address_received(update, context):
    # address = update.message.text.partition(' ')[2]
    address = update.message.text
    url = get_rand_node_url()

    request = requests.get(url)
    all_nodes_json = request.json()

    node = getThorNodeObject(all_nodes_json, address)
    if node is None:
        update.message.reply_text('⛔️ The THORnode address you entered does not exist! ⛔️\n'
                                  '                      Please try again.\n' +
                                  '(Enter /cancel to return to the menu)')
        context.user_data['job_running'] = False
        return TYPING_ADDRESS

    context.user_data["address"] = address
    for field in node_fields:
        context.user_data[field] = node[field]

    text = 'The address you monitor is: ' + address
    for field in node_fields:
        text += '\nCurrent ' + field + ': ' + node[field]
    update.message.reply_text(text)

    context.user_data['job_running'] = True
    return show_actions(context, update.message.chat.id)


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
    return show_actions(context, update.effective_chat.id)


def show_actions(context, chat_id):
    keyboard = [[InlineKeyboardButton("set Address", callback_data='set Address'),
                 InlineKeyboardButton("get Stats", callback_data='get Stats')]]
    context.bot.send_message(chat_id, 'Choose an action:', reply_markup=InlineKeyboardMarkup(keyboard))
    return CHOOSING


def error(update, context):
    """Log Errors caused by Updates."""
    logger.warning('Update "%s" caused error "%s"', update, context.error)


def get_rand_node_url():
    # url = "https://testnet-seed.thorchain.info/"
    # request = requests.get(url)
    # data = request.json()
    #
    # randNodeIndex = random.randrange(0, len(data.active))
    # randNode = data.active[randNodeIndex]

    # hardcoded_node = "http://67.205.166.241:1317/thorchain/nodeaccounts"
    hardcoded_node = "http://localhost:8000/node_data.json"
    return hardcoded_node


def getThorNodeObject(all_nodes_json, address):
    for i in range(0, len(all_nodes_json)):
        if all_nodes_json[i]["node_address"] == address:
            return all_nodes_json[i]
    return None


def checkNode(context):
    chat_id = context.job.context["chat_id"]
    user_data = context.job.context["user_data"]

    if 'job_running' not in user_data or user_data['job_running'] == False:
        return  # show_actions(context, chat_id)

    address = user_data['address']
    url = get_rand_node_url()

    request = requests.get(url)
    all_nodes_json = request.json()

    node = getThorNodeObject(all_nodes_json, address)
    if node is None:
        context.bot.send_message(chat_id, '⛔️ The THORnode you monitor is not active anymore! ⛔️\n'
                                          '                Please set a new THORnode address.')
        user_data['job_running'] = False
        return show_actions(context, chat_id)

    changed_values = False
    text = ''
    for field in node_fields:
        if user_data[field] != node[field]:
            changed_values = True
            text += field + ' changed! 💥\n'

    if changed_values:
        text += '\n THORnode address: ' + address + '\n'
        for key in node_fields:
            text += '\n' + key + ': ' + user_data[key] + ' ➡️ ' + node[key]
            user_data[key] = node[key]

        context.bot.send_message(chat_id, text)
        show_actions(context, chat_id)


def start_monitoring_jobs(dp):
    chat_ids = dp.user_data.keys()
    for chat_id in chat_ids:
        dp.job_queue.run_repeating(checkNode, 30,
                                   context={"chat_id": chat_id, "user_data": dp.user_data[chat_id]})


def main():
    # Create the Updater and pass it your bot's token.
    # Make sure to set use_context=True to use the new context based callbacks
    # Post version 12 this will no longer be necessary

    my_persistence = PicklePersistence(filename='session_data')
    updater = Updater(telegram_token, persistence=my_persistence, use_context=True)

    # Get the dispatcher to register handlers
    dp = updater.dispatcher

    # dp.add_handler(CommandHandler("start", start))
    # dp.add_handler(CommandHandler("address_received", address_received,
    #                              pass_args=True,
    #                              pass_job_queue=True,
    #                              pass_chat_data=True))
    # dp.add_handler(CommandHandler("get_stats", get_stats))
    # updater.dispatcher.add_handler(CallbackQueryHandler(address_received, pattern='^' + 'set Address' + '$'))
    # updater.dispatcher.add_handler(CallbackQueryHandler(get_stats, pattern='^' + 'get Stats' + '$'))

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start),
                      CallbackQueryHandler(get_stats, pattern='^' + 'get Stats' + '$'),
                      CallbackQueryHandler(set_address, pattern='^' + 'set Address' + '$')],

        states={
            CHOOSING: [CallbackQueryHandler(get_stats, pattern='^' + 'get Stats' + '$'),
                       CallbackQueryHandler(set_address, pattern='^' + 'set Address' + '$')],

            TYPING_ADDRESS: [CommandHandler('cancel', cancel),
                             MessageHandler(Filters.text, address_received,
                                            pass_job_queue=True,
                                            pass_chat_data=True)]
        },

        fallbacks=[]
    )

    dp.add_handler(conv_handler)

    # log all errors
    dp.add_error_handler(error)

    start_monitoring_jobs(dp)

    # Start the Bot
    updater.start_polling()
    logger.info('THORnode Telegram Alert Bot is running...')

    # Run the bot until you press Ctrl-C or the process receives SIGINT,
    # SIGTERM or SIGABRT. This should be used most of the time, since
    # start_polling() is non-blocking and will stop the bot gracefully.
    updater.idle()


if __name__ == '__main__':
    main()

import logging
import os

import requests

from telegram.ext import (Updater, CommandHandler, PicklePersistence)

# Enable logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)

logger = logging.getLogger(__name__)

telegram_token = os.environ["TELEGRAM_TOKEN"]


def start(update, context):
    update.message.reply_text(
        'Hi!. '
        'Here you will get some nice jsons of THORnodes.\n\n'
        'Look at this:')

    url = "http://35.170.66.96:1317/thorchain/nodeaccounts"
    request = requests.get(url)
    data = request.json()

    update.message.reply_text(data[0])

def add(update, context):
    address = update.message.text.partition(' ')[2]
    context.user_data["thornode_address"] = address

    update.message.reply_text('The address you listen to is: ' + address)

def get(update, context):
    update.message.reply_text('The address you listen to is: ' + context.user_data["thornode_address"])

def error(update, context):
    """Log Errors caused by Updates."""
    logger.warning('Update "%s" caused error "%s"', update, context.error)


def main():
    # Create the Updater and pass it your bot's token.
    # Make sure to set use_context=True to use the new context based callbacks
    # Post version 12 this will no longer be necessary

    my_persistence = PicklePersistence(filename='session_data')
    updater = Updater(telegram_token, persistence=my_persistence, use_context=True)

    # Get the dispatcher to register handlers
    dp = updater.dispatcher

    # Add conversation handler with the states GENDER, PHOTO, LOCATION and BIO


    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CommandHandler("add", add))
    dp.add_handler(CommandHandler("get", get))

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

from telegram.error import InvalidToken
from telegram.ext import (Updater, CommandHandler, PicklePersistence,
                          CallbackQueryHandler, MessageHandler, Filters)

from handlers.handlers import *
from service.setup import *


def main():
    """
    Init telegram bot, attach handlers and wait for incoming requests.
    """
    if DEBUG:
        setup_debug_processes()

    try:
        bot = Updater(TELEGRAM_BOT_TOKEN,
                      persistence=PicklePersistence(filename=session_data_path),
                      use_context=True)
    except InvalidToken:
        logger.error("Invalid telegram token. Please make sure to set TELEGRAM_BOT_TOKEN environmental variable with"
                     " correct Telegram bot token. Check project docs for more details.", exc_info=True)
        raise

    dispatcher = bot.dispatcher

    setup_existing_users(dispatcher=dispatcher)
    setup_bot_data(dispatcher=dispatcher)

    dispatcher.add_handler(CommandHandler('start', on_start_command))
    dispatcher.add_handler(CallbackQueryHandler(dispatch_query))
    dispatcher.add_handler(MessageHandler(Filters.text, dispatch_plain_input_query))
    dispatcher.add_error_handler(error_handler)

    # Start the bot
    bot.start_polling()
    logger.info('THORNode Bot is running on ' + NETWORK_TYPE + ' ...')

    # Run the bot until you press Ctrl-C or the process receives SIGINT,
    # SIGTERM or SIGABRT. This should be used most of the time, since
    # start_polling() is non-blocking and will stop the bot gracefully.
    bot.idle()


if __name__ == '__main__':
    main()

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

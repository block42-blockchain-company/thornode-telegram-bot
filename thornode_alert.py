import logging
import os
import random
import requests
import json

from telegram.ext import (Updater, CommandHandler, PicklePersistence)

# Enable logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)

logger = logging.getLogger(__name__)

telegram_token = os.environ["TELEGRAM_TOKEN"]

node_fields = ["status", "bond", "slash_points"]

def start(update, context):
    update.message.reply_text(
        'Heil ok sæll! 😁\n'
        'This is the Telegram Alert Bot for THORnodes of THORchain.\n\n'
        'Enter the address of a THORnode, and the Bot will notify you if there is a change in the nodes status, bond or slash_points.\n'
        'Commands:\n'
        '/enterThornodeAddress thorXXX..XXX\n'
        '/getStats')

    #url = "http://67.205.166.241:1317/thorchain/nodeaccounts"
    #request = requests.get(url)
    #data = request.json()
#
    #update.message.reply_text(data[0])


def enterThornodeAddress(update, context):
    address = update.message.text.partition(' ')[2]
    url = getRandNode() + ':1317/thorchain/nodeaccounts'

    request = requests.get(url)
    allNodesJson = request.json()

    node = getThorNodeObject(allNodesJson, address)
    if node is None:
        return update.message.reply_text('⛔️ The THORnode address you entered does not exist! ⛔️\n'
                                         '                      Please try again.')

    context.user_data["address"] = address
    for field in node_fields:
        context.user_data[field] = node[field]

    # context.user_data["status"] = node["status"]
    # context.user_data["bond"] = node["bond"]
    # context.user_data["slash_points"] = node["slash_points"]

    text = 'The address you monitor is: ' + address

    for field in node_fields:
        text += '\nCurrent ' + field + ': ' + node[field]

    update.message.reply_text(text)

    # Add job to queue and stop current one if there is a timer already
    if 'checkNodeJob' in context.user_data:
        old_job = context.user_data['checkNodeJob']
        old_job.schedule_removal()
    new_job = context.job_queue.run_repeating(checkNode, 30, context=update)
    context.user_data['checkNodeJob'] = new_job


def getStats(update, context):
    # update.message.reply_text('The address you listen to is: ' + context.user_data["thornode_address"])
    update.message.reply_text('The address you listen to is: ' + context.user_data["address"] +
                              '\nCurrent status: ' + context.user_data["status"] +
                              '\nCurrent bond: ' + context.user_data["bond"] +
                              '\nCurrent slash_points: ' + context.user_data["slash_points"])


def error(update, context):
    """Log Errors caused by Updates."""
    logger.warning('Update "%s" caused error "%s"', update, context.error)


def getRandNode():
    #url = "https://testnet-seed.thorchain.info/"
    #request = requests.get(url)
    #data = request.json()
    #
    #randNodeIndex = random.randrange(0, len(data.active))
    #randNode = data.active[randNodeIndex]

    hardcoded_node = "http://67.205.166.241"
    return hardcoded_node


def getThorNodeObject(allNodesJson, address):
    for i in range(0, len(allNodesJson)):
        if allNodesJson[i]["node_address"] == address:
            return allNodesJson[i]
    return None


def checkNode(context):
    job = context.job

    address = context.user_data['address']
    url = getRandNode() + ':1317/thorchain/nodeaccounts'

    request = requests.get(url)
    allNodesJson = request.json()

    node = getThorNodeObject(allNodesJson, address)
    if node is None:
        job.context.message.reply_text('⛔️ The THORnode you monitor is not active anymore! ⛔️\n'
                                       '                Please set a new THORnode address.')
        old_job = context.user_data['checkNodeJob']
        old_job.schedule_removal()
        return

    for field in node_fields:
        if context.user_data[field] != node[field]:
            text = field + ' changed! 💥\n THORnode address: ' + address
            for key in node_fields:
                text += '\n' + key + ': ' + context.user_data[key] + ' ➡️ ' + node[key]
                context.user_data[key] = node[key]

            job.context.message.reply_text(text)
            return

    #context.user_data["status"] = node["status"]
    #context.user_data["bond"] = node["bond"]
    #context.user_data["slash_points"] = node["slash_points"]

    #job.context.message.reply_text("hi")


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
    dp.add_handler(CommandHandler("enterThornodeAddress", enterThornodeAddress,
                                  pass_args=True,
                                  pass_job_queue=True,
                                  pass_chat_data=True))
    dp.add_handler(CommandHandler("getStats", getStats))

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

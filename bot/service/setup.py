import atexit
import time

from future.moves import subprocess
from telegram.error import Unauthorized

from jobs.jobs import *
from service.thorchain_network_service import *


def setup_existing_users(dispatcher):
    """
    Tasks to ensure smooth user experience for existing users upon Bot restart
    """
    logger.info("Setting up the user's data.")

    blocked_ids = []

    for chat_id in dispatcher.chat_data.keys():
        # about `not is_group_chat(chat_id)`: Filter out group chats, as they can't get whitelisted.
        if ALLOWED_USER_IDS != 'ALL' and not is_group_chat(chat_id) and chat_id not in ALLOWED_USER_IDS:
            blocked_ids.append(chat_id)
            continue

        restart_message = 'Heil ok sæll!\n' \
                          'Me, your THORNode Bot, just got restarted on the server! 🤖\n' \
                          'To make sure you have the latest features, please start ' \
                          'a fresh chat with me by typing /start.'

        message_result = dispatcher.bot.send_message(chat_id, restart_message)
        if isinstance(message_result.exception, Unauthorized):
            blocked_ids.append(chat_id)
            continue
        elif isinstance(message_result.exception, TelegramError):
            logger.exception(f'USER {str(chat_id)}\n Error: {str(message_result.exception)}',
                             exc_info=True)

        # Start monitoring jobs for all existing users
        if 'job_started' not in dispatcher.chat_data[chat_id]:
            dispatcher.chat_data[chat_id]['job_started'] = True
        dispatcher.job_queue.run_repeating(
            user_specific_checks,
            interval=JOB_INTERVAL_IN_SECONDS,
            context={
                'chat_id': chat_id,
                'chat_data': dispatcher.chat_data[chat_id]
            })

    for chat_id in blocked_ids:
        logger.info(f"Telegram chat {str(chat_id)} blocked me or is "
                    f"not Admin anymore; removing it from the chat list")

        if not is_group_chat(chat_id):
            del dispatcher.user_data[chat_id]
            del dispatcher.persistence.user_data[chat_id]

        del dispatcher.chat_data[chat_id]
        del dispatcher.persistence.chat_data[chat_id]

        # Somehow session.data does not get updated if all users block the bot.
        # That's why we delete the file ourselves.
        if len(dispatcher.persistence.chat_data) == 0:
            if os.path.exists(session_data_path):
                os.remove(session_data_path)

    try:
        new_node_accounts = get_node_accounts()
    except:
        logger.exception(
            "Fatal error! I couldn't get node accounts to update the local chat_data!",
            exc_info=True)
        return

    # Delete all node addresses and add them again to ensure all chat_data fields are up to date
    for chat_id in dispatcher.chat_data.keys():
        if 'nodes' not in dispatcher.chat_data[chat_id]:
            dispatcher.chat_data[chat_id]['nodes'] = {}

        local_node_addresses = list(dispatcher.chat_data[chat_id]['nodes'].keys())

        for address in local_node_addresses:
            try:
                new_node = next(n for n in new_node_accounts
                                if n['node_address'] == address)
                del dispatcher.chat_data[chat_id]['nodes'][address]
                add_thornode_to_chat_data(dispatcher.chat_data[chat_id],
                                          address, new_node)
            except StopIteration:
                obsolete_node = dispatcher.chat_data[chat_id]['nodes'][address]
                dispatcher.bot.send_message(
                    chat_id,
                    f"Your node {obsolete_node['alias']} with address {address} "
                    f"is not present in the network! "
                    f"I'm removing it...")
                del dispatcher.chat_data[chat_id]['nodes'][address]


def setup_debug_processes():
    current_dir = os.path.dirname(os.path.realpath(__file__))
    test_dir = os.sep.join([current_dir, os.path.pardir, os.path.pardir, "test"])
    increase_block_height_path = os.sep.join([test_dir, "increase_block_height.py"])
    mock_api_path = os.sep.join([test_dir, "mock_api.py"])

    increase_block_height_process = subprocess.Popen(
        ['python3', increase_block_height_path], cwd=test_dir)
    mock_api_process = subprocess.Popen(['python3', mock_api_path],
                                        cwd=test_dir)

    def cleanup():
        mock_api_process.terminate()
        increase_block_height_process.terminate()

    atexit.register(cleanup)
    time.sleep(
        1)  # Make sure all processes started before bot starts using them

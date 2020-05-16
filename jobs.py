from datetime import datetime

from constants import *
from helpers import *


"""
######################################################################################################################################################
Jobs
######################################################################################################################################################
"""


def thornode_checks(context):
    """
    Periodic checks of various node stats
    """

    check_thornodes(context)
    check_thorchain_block_height(context)
    check_thorchain_catch_up_status(context)
    check_thorchain_midgard_api(context)


def check_thornodes(context):
    """
    Check all added thornodes for any changes.
    """

    chat_id = context.job.context['chat_id']
    user_data = context.job.context['user_data']

    # Flag to show home buttons or not
    message_sent = False

    # List to delete entries after loop
    delete_addresses = []

    # Iterate through all keys
    for address in user_data['nodes'].keys():
        remote_node = get_thornode_object(address=address)
        local_node = user_data['nodes'][address]

        if remote_node is None:
            text = 'THORNode is not active anymore! 💀' + '\n' + \
                   'Address: ' + address + '\n\n' + \
                   'Please enter another THORNode address.'

            delete_addresses.append(address)

            # Send message
            context.bot.send_message(chat_id, text)
            message_sent = True
            continue

        # Check which node fields have changed
        changed_fields = [field for field in ['status', 'bond', 'slash_points'] if
                          local_node[field] != remote_node[field]]

        # Check if there are any changes
        if len(changed_fields) > 0:
            text = 'THORNode: ' + address + '\n' + \
                   'Status: ' + local_node['status'].capitalize() + \
                   ' ➡️ ' + remote_node['status'].capitalize() + '\n' + \
                   'Bond: ' + tor_to_rune(int(local_node['bond'])) + \
                   ' ➡️ ' + tor_to_rune(int(remote_node['bond'])) + '\n' + \
                   'Slash Points: ' + '{:,}'.format(int(local_node['slash_points'])) + \
                   ' ➡️ ' + '{:,}'.format(int(remote_node['slash_points']))

            # Update data
            local_node['status'] = remote_node['status']
            local_node['bond'] = remote_node['bond']
            local_node['slash_points'] = remote_node['slash_points']

            # Send message
            context.bot.send_message(chat_id, text)
            message_sent = True

    for address in delete_addresses:
        del user_data['nodes'][address]

    if message_sent:
        show_home_menu(context=context, chat_id=chat_id)


def check_thorchain_block_height(context):
    """
    Make sure the block height increases
    """

    chat_id = context.job.context['chat_id']
    user_data = context.job.context['user_data']

    block_height = get_thorchain_block_height()

    # Check if block height got stuck
    if 'block_height' in user_data and block_height <= user_data['block_height']:

        # Increase stuck count to know if we already sent a notification
        user_data['block_height_stuck_count'] += 1
    else:
        # Check if we have to send a notification that the Height increases again
        if 'block_height_stuck_count' in user_data and user_data['block_height_stuck_count'] > 0:
            text = 'Block height is increasing again! 👌' + '\n' + \
                   'IP: ' + THORCHAIN_NODE_IP + '\n' + \
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
               'IP: ' + THORCHAIN_NODE_IP + '\n' + \
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
        show_home_menu(context=context, chat_id=chat_id)


def check_thorchain_catch_up_status(context):
    """
    Check if node is some blocks behind with catch up status
    """

    chat_id = context.job.context['chat_id']
    user_data = context.job.context['user_data']

    if 'is_catching_up' not in user_data:
        user_data['is_catching_up'] = False

    is_currently_catching_up = is_thorchain_catching_up()
    if user_data['is_catching_up'] == False and is_currently_catching_up:
        user_data['is_catching_up'] = True
        text = 'The Node is behind the latest block height and catching up! 💀 ' + '\n' + \
               'IP: ' + THORCHAIN_NODE_IP + '\n' + \
               'Current block height: ' + get_thorchain_block_height() + '\n\n' + \
               'Please check your Thornode immediately!'
        context.bot.send_message(chat_id, text)
        show_home_menu(context=context, chat_id=chat_id)
    elif user_data['is_catching_up'] == True and not is_currently_catching_up:
        user_data['is_catching_up'] = False
        text = 'The node caught up to the latest block height again! 👌' + '\n' + \
               'IP: ' + THORCHAIN_NODE_IP + '\n' + \
               'Current block height: ' + get_thorchain_block_height()
        context.bot.send_message(chat_id, text)
        show_home_menu(context=context, chat_id=chat_id)


def check_thorchain_midgard_api(context):
    """
    Check that Midgard API is ok
    """

    chat_id = context.job.context['chat_id']
    user_data = context.job.context['user_data']

    if 'is_midgard_healthy' not in user_data:
        user_data['is_midgard_healthy'] = True

    is_midgard_currently_healthy = is_thorchain_midgard_healthy()
    if user_data['is_midgard_healthy'] == True and not is_midgard_currently_healthy:
        user_data['is_midgard_healthy'] = False
        text = 'Midgard API is not healthy anymore! 💀' + '\n' + \
               'IP: ' + THORCHAIN_NODE_IP + '\n\n' + \
               'Please check your Thornode immediately!'
        context.bot.send_message(chat_id, text)
        show_home_menu(context, chat_id=chat_id)
    elif user_data['is_midgard_healthy'] == False and is_midgard_currently_healthy:
        user_data['is_midgard_healthy'] = True
        text = 'Midgard API is healthy again! 👌' + '\n' + \
               'IP: ' + THORCHAIN_NODE_IP + '\n'
        context.bot.send_message(chat_id, text)
        show_home_menu(context, chat_id=chat_id)


def update_health_check_file(context):
    """
    Write timestamp into health.check file for the health check
    """

    with open('storage/health.check', 'w') as healthcheck_file:
        timestamp = datetime.timestamp(datetime.now())
        healthcheck_file.write(str(timestamp))
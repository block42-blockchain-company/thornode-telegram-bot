
from bot.helpers import *

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
    if BINANCE_NODE_IP:
        check_binance_health(context)


def check_thornodes(context):
    """
    Check all added thornodes for any changes.
    """

    chat_id = context.job.context['chat_id']
    user_data = context.job.context['user_data']

    # Flag to show home buttons or not
    # message_sent = False

    # List to delete entries after loop
    inactive_nodes = []

    for node_address, node_data in user_data['nodes'].items():
        remote_node = get_thornode_object(address=node_address)
        local_node = user_data['nodes'][node_address]

        if remote_node is None:
            text = 'THORNode ' + user_data['nodes'][node_address]['alias'] + ' is not active anymore! 💀' + '\n' + \
                   'Address: ' + node_address + '\n\n' + \
                   'Please enter another THORNode address.'

            inactive_nodes.append(node_address)

            # Send message
            try_message_with_home_menu(context=context, chat_id=chat_id, text=text)
            # message_sent = True
            continue

        node_ip_address = node_data['ip_address']
        check_thorchain_block_height(context, node_ip=node_ip_address, node_address=node_address)
        check_thorchain_catch_up_status(context, node_ip=node_ip_address)
        check_thorchain_midgard_api(context, node_ip=node_ip_address)

        # isNotBlocked = lastTimestamp < currentTimestamp - timeout
        if float(local_node['last_notification_timestamp']) < \
                float(datetime.timestamp(
                    datetime.now() - timedelta(seconds=local_node['notification_timeout_in_seconds']))):

            # Check which node fields have changed
            changed_fields = [field for field in ['status', 'bond', 'slash_points'] if
                              local_node[field] != remote_node[field]]

            # If just slash_points changed, only send message if difference is min. 3 slash points
            if len(changed_fields) == 1 and 'slash_points' in changed_fields and \
                    abs(int(local_node['slash_points']) - int(remote_node['slash_points'])) < 5:
                continue

            # Check if there are any changes
            if len(changed_fields) > 0:
                text = 'THORNode: ' + user_data['nodes'][node_address]['alias'] + '\n' + \
                       'Address: ' + node_address + '\n' + \
                       'Status: ' + local_node['status'].capitalize()
                if 'status' in changed_fields:
                    text += ' ➡️ ' + remote_node['status'].capitalize()
                text += '\nBond: ' + tor_to_rune(int(local_node['bond']))
                if 'bond' in changed_fields:
                    text += ' ➡️ ' + tor_to_rune(int(remote_node['bond']))
                text += '\nSlash Points: ' + '{:,}'.format(int(local_node['slash_points']))
                if 'slash_points' in changed_fields:
                    text += ' ➡️ ' + '{:,}'.format(int(remote_node['slash_points']))

                # Update data
                local_node['status'] = remote_node['status']
                local_node['bond'] = remote_node['bond']
                local_node['slash_points'] = remote_node['slash_points']
                local_node['last_notification_timestamp'] = datetime.timestamp(datetime.now())
                local_node['notification_timeout_in_seconds'] *= NOTIFICATION_TIMEOUT_MULTIPLIER

                # Send message
                try_message_with_home_menu(context=context, chat_id=chat_id, text=text)
                # message_sent = True
            else:
                local_node['notification_timeout_in_seconds'] = INITIAL_NOTIFICATION_TIMEOUT

    for node_address in inactive_nodes:
        del user_data['nodes'][node_address]

    # if message_sent:
    #    try_message_with_home_menu(context=context, chat_id=chat_id)


def check_thorchain_block_height(context, node_ip, node_address):
    """
    Make sure the block height increases
    """

    chat_id = context.job.context['chat_id']
    node_data = context.job.context['user_data']['nodes'][node_address]

    block_height = get_thorchain_latest_block_height(node_ip)

    # Check if block height got stuck
    if 'block_height' in node_data and block_height <= node_data['block_height']:

        # Increase stuck count to know if we already sent a notification
        node_data['block_height_stuck_count'] += 1
    else:
        # Check if we have to send a notification that the Height increases again
        if 'block_height_stuck_count' in node_data and node_data['block_height_stuck_count'] > 0:
            text = 'Block height is increasing again! 👌' + '\n' + \
                   'IP: ' + node_ip + '\n' + \
                   'THORNode: ' + node_data['alias'] + '\n' + \
                   'Node address: ' + node_address + '\n' + \
                   'Block height now at: ' + block_height + '\n'
            try_message_with_home_menu(context=context, chat_id=chat_id, text=text)
            node_data['block_height_stuck_count'] = -1
        else:
            node_data['block_height_stuck_count'] = 0

    # Set current block height
    node_data['block_height'] = block_height

    # If it just got stuck send a message
    if node_data['block_height_stuck_count'] == 1:
        text = 'Block height is not increasing anymore! 💀' + '\n' + \
               'IP: ' + node_ip + '\n' + \
               'THORNode: ' + node_data['alias'] + '\n' + \
               'Node address: ' + node_address + '\n' + \
               'Block height stuck at: ' + block_height + '\n\n' + \
               'Please check your Thornode immediately!'
        try_message_with_home_menu(context=context, chat_id=chat_id, text=text)

    # Show buttons if there were changes or block height just got (un)stuck
    # Stuck count:
    # 0 == everthings alright
    # 1 == just got stuck
    # -1 == just got unstuck
    # > 1 == still stuck

    # if user_data['block_height_stuck_count'] == 1 or user_data['block_height_stuck_count'] == -1:
    #    try_message_with_home_menu(context=context, chat_id=chat_id)


def check_thorchain_catch_up_status(context, node_ip):
    """
    Check if node is some blocks behind with catch up status
    """

    chat_id = context.job.context['chat_id']
    user_data = context.job.context['user_data']

    if 'is_catching_up' not in user_data:
        user_data['is_catching_up'] = False

    is_currently_catching_up = is_thorchain_catching_up(node_ip)
    if user_data['is_catching_up'] == False and is_currently_catching_up:
        user_data['is_catching_up'] = True
        text = 'The Node is behind the latest block height and catching up! 💀 ' + '\n' + \
               'IP: ' + node_ip + '\n' + \
               'Current block height: ' + get_thorchain_latest_block_height(node_ip) + '\n\n' + \
               'Please check your Thornode immediately!'
        try_message_with_home_menu(context=context, chat_id=chat_id, text=text)
    elif user_data['is_catching_up'] == True and not is_currently_catching_up:
        user_data['is_catching_up'] = False
        text = 'The node caught up to the latest block height again! 👌' + '\n' + \
               'IP: ' + node_ip + '\n' + \
               'Current block height: ' + get_thorchain_latest_block_height(node_ip)
        try_message_with_home_menu(context=context, chat_id=chat_id, text=text)


def check_thorchain_midgard_api(context, node_ip):
    """
    Check that Midgard API is ok
    """

    chat_id = context.job.context['chat_id']
    user_data = context.job.context['user_data']

    if 'is_midgard_healthy' not in user_data:
        user_data['is_midgard_healthy'] = True

    is_midgard_currently_healthy = is_thorchain_midgard_healthy(node_ip)
    if user_data['is_midgard_healthy'] == True and not is_midgard_currently_healthy:
        user_data['is_midgard_healthy'] = False
        text = 'Midgard API is not healthy anymore! 💀' + '\n' + \
               'IP: ' + node_ip + '\n\n' + \
               'Please check your Thornode immediately!'
        try_message_with_home_menu(context, chat_id=chat_id, text=text)
    elif user_data['is_midgard_healthy'] == False and is_midgard_currently_healthy:
        user_data['is_midgard_healthy'] = True
        text = 'Midgard API is healthy again! 👌' + '\n' + \
               'IP: ' + node_ip + '\n'
        try_message_with_home_menu(context, chat_id=chat_id, text=text)


def check_binance_health(context):
    """
    Check if Binance Node is healthy
    """

    chat_id = context.job.context['chat_id']
    user_data = context.job.context['user_data']

    if 'is_binance_node_healthy' not in user_data:
        user_data['is_binance_node_healthy'] = True

    is_binance_node_currently_healthy = is_binance_node_healthy()
    if user_data['is_binance_node_healthy'] == True and not is_binance_node_currently_healthy:
        user_data['is_binance_node_healthy'] = False
        text = 'Binance Node is not healthy anymore! 💀' + '\n' + \
               'IP: ' + BINANCE_NODE_IP + '\n\n' + \
               'Please check your Binance Node immediately!'
        try_message_with_home_menu(context, chat_id=chat_id, text=text)
    elif user_data['is_binance_node_healthy'] == False and is_binance_node_currently_healthy:
        user_data['is_binance_node_healthy'] = True
        text = 'Binance Node is healthy again! 👌' + '\n' + \
               'IP: ' + BINANCE_NODE_IP + '\n'
        try_message_with_home_menu(context, chat_id=chat_id, text=text)


def update_health_check_file(context):
    """
    Write timestamp into health.check file for the health check
    """

    current_dir = os.path.dirname(__file__)
    path = os.sep.join([current_dir, os.path.pardir, "storage", "health.check"])

    with open(path, 'w') as healthcheck_file:
        timestamp = datetime.timestamp(datetime.now())
        healthcheck_file.write(str(timestamp))
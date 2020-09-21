from helpers import *
from service.thorchain_network_service import *
from packaging import version
from messages import *


def user_specific_checks(context):
    """
    Periodic checks of nodes that the user monitors
    """

    check_versions_status(context)
    check_thornodes(context)


def general_bot_checks(context):
    """
    Periodic checks that are interesting for all users
    """

    check_churning(context)
    if BINANCE_NODE_IPS:
        check_binance_health(context)


def check_thornodes(context):
    """
    Check all added thornodes for any changes.
    """

    chat_id = context.job.context['chat_id']
    user_data = context.job.context['user_data']

    inactive_nodes = []

    for node_address, node_data in user_data['nodes'].items():

        try:
            remote_node = get_thornode_object_or_none(address=node_address)
        except Exception as e:
            logger.exception(e)
            continue

        local_node = user_data['nodes'][node_address]

        if remote_node is None:
            text = 'THORNode ' + user_data['nodes'][node_address]['alias'] + ' is not active anymore! 💀' + '\n' + \
                   'Address: ' + node_address + '\n\n' + \
                   'Please enter another THORNode address.'

            inactive_nodes.append(node_address)

            try_message_with_home_menu(context=context, chat_id=chat_id, text=text)
            continue

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
                local_node['ip_address'] = remote_node['ip_address']
                local_node['last_notification_timestamp'] = datetime.timestamp(datetime.now())
                local_node['notification_timeout_in_seconds'] *= NOTIFICATION_TIMEOUT_MULTIPLIER

                try_message_with_home_menu(context=context, chat_id=chat_id, text=text)
            else:
                local_node['notification_timeout_in_seconds'] = INITIAL_NOTIFICATION_TIMEOUT

        if local_node['status'] in MONITORED_STATUSES:
            check_thorchain_block_height(context, node_address=node_address)

            check_thorchain_catch_up_status(context, node_address=node_address)

            check_thorchain_midgard_api(context, node_address=node_address)

    for node_address in inactive_nodes:
        del user_data['nodes'][node_address]


def check_thorchain_block_height(context, node_address):
    """
    Make sure the block height increases
    """

    logger.info("I'm checking thorchain block height...")

    chat_id = context.job.context['chat_id']
    node_data = context.job.context['user_data']['nodes'][node_address]

    try:
        block_height = get_latest_block_height(node_data['ip_address'])
    except Exception as e:
        logger.exception(e)
        return

    # Send message if there were changes or block height just got (un)stuck
    # Stuck count:
    # 0 == everthings alright
    # 1 == just got stuck
    # -1 == just got unstuck
    # > 1 == still stuck

    # Check if block height got stuck
    if 'block_height' in node_data and block_height <= node_data['block_height']:

        # Increase stuck count to know if we already sent a notification
        node_data['block_height_stuck_count'] += 1
    else:
        # Check if we have to send a notification that the Height increases again
        if 'block_height_stuck_count' in node_data and node_data['block_height_stuck_count'] > 0:
            text = 'Block height is increasing again! 👌' + '\n' + \
                   'IP: ' + node_data['ip_address'] + '\n' + \
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
               'IP: ' + node_data['ip_address'] + '\n' + \
               'THORNode: ' + node_data['alias'] + '\n' + \
               'Node address: ' + node_address + '\n' + \
               'Block height stuck at: ' + block_height + '\n\n' + \
               'Please check your Thornode immediately!'
        try_message_with_home_menu(context=context, chat_id=chat_id, text=text)


def check_thorchain_catch_up_status(context, node_address):
    """
    Check if node is some blocks behind with catch up status
    """

    logger.info("I'm checking catch up status...")

    chat_id = context.job.context['chat_id']
    node_data = context.job.context['user_data']['nodes'][node_address]

    if 'is_catching_up' not in node_data:
        node_data['is_catching_up'] = False

    try:
        is_currently_catching_up = is_thorchain_catching_up(node_data['ip_address'])
    except Exception as e:
        logger.exception(e)
        return

    if node_data['is_catching_up'] != is_currently_catching_up:
        try:
            block_height = get_latest_block_height(node_data['ip_address'])
        except Exception as e:
            logger.exception(e)
            block_height = "currently unavailable"

        if is_currently_catching_up:
            node_data['is_catching_up'] = True
            text = 'The Node is behind the latest block height and catching up! 💀 ' + '\n' + \
                   'IP: ' + node_data['ip_address'] + '\n' + \
                   'THORNode: ' + node_data['alias'] + '\n' + \
                   'Node address: ' + node_address + '\n' + \
                   'Current block height: ' + block_height + '\n\n' + \
                   'Please check your Thornode immediately!'
        else:
            node_data['is_catching_up'] = False
            text = 'The node caught up to the latest block height again! 👌' + '\n' + \
                   'IP: ' + node_data['ip_address'] + '\n' + \
                   'THORNode: ' + node_data['alias'] + '\n' + \
                   'Node address: ' + node_address + '\n' + \
                   'Current block height: ' + block_height
        try_message_with_home_menu(context=context, chat_id=chat_id, text=text)


def check_thorchain_midgard_api(context, node_address):
    """
    Check that Midgard API is ok
    """

    logger.info("I'm checking Midgard health...")

    chat_id = context.job.context['chat_id']
    node_data = context.job.context['user_data']['nodes'][node_address]

    if 'is_midgard_healthy' not in node_data:
        node_data['is_midgard_healthy'] = True

    is_midgard_healthy = is_midgard_api_healthy(node_data['ip_address'])

    if node_data['is_midgard_healthy'] != is_midgard_healthy:
        if is_midgard_healthy:
            node_data['is_midgard_healthy'] = True
            text = 'Midgard API is healthy again! 👌' + '\n' + \
                   'IP: ' + node_data['ip_address'] + '\n' + \
                   'THORNode: ' + node_data['alias'] + '\n' + \
                   'Node address: ' + node_address
            try_message_with_home_menu(context, chat_id=chat_id, text=text)
        else:
            node_data['is_midgard_healthy'] = False
            text = 'Midgard API is not healthy anymore! 💀' + '\n' + \
                   'IP: ' + node_data['ip_address'] + '\n' + \
                   'THORNode: ' + node_data['alias'] + '\n' + \
                   'Node address: ' + node_address + '\n\n' + \
                   'Please check your Thornode immediately!'
            try_message_with_home_menu(context, chat_id=chat_id, text=text)


def check_binance_health(context):
    """
    Check if Binance Node is healthy
    """

    logger.info("I'm checking binance node health...")
    binance_nodes = context.bot_data['binance_nodes']

    for binance_node_ip in BINANCE_NODE_IPS:
        if 'is_binance_node_healthy' not in binance_nodes[binance_node_ip]:
            binance_nodes[binance_node_ip]['is_binance_node_healthy'] = True
        binance_node_data = binance_nodes[binance_node_ip]

        is_binance_node_currently_healthy = is_binance_node_healthy(binance_node_ip)

        if binance_node_data['is_binance_node_healthy'] != is_binance_node_currently_healthy:
            if is_binance_node_currently_healthy:
                binance_node_data['is_binance_node_healthy'] = True
                text = 'Binance Node is healthy again! 👌' + '\n' + \
                       'IP: ' + binance_node_ip + '\n'
                try_message_to_all_users(context, text=text)
            else:
                binance_node_data['is_binance_node_healthy'] = False
                text = 'Binance Node is not healthy anymore! 💀' + '\n' + \
                       'IP: ' + binance_node_ip + '\n\n' + \
                       'Please check your Binance Node immediately!'
                try_message_to_all_users(context, text=text)


def check_versions_status(context):
    logger.info("I'm checking version changes...")
    user_data = context.job.context['user_data']

    try:
        node_accounts = get_node_accounts()
    except Exception as e:
        logger.exception(e)
        try_message_with_home_menu(context, chat_id=context.job.context['chat_id'], text=NODE_LIST_UNAVAILABLE_ERROR_MSG)
        return

    highest_version = max(map(lambda n: n['version'], node_accounts), key=lambda v: version.parse(v))
    last_newest_version = user_data.get('newest_software_version', None)

    if last_newest_version is None or version.parse(highest_version) > version.parse(last_newest_version):
        user_data['newest_software_version'] = highest_version
        for node in user_data['nodes'].values():
            if version.parse(node['version']) < version.parse(highest_version):
                message = f"Consider updating the software on your node: *{node['alias']}*   ‼️\n" \
                          f"Your software version is *{node['version']}* " \
                          f"but one of the nodes already runs on *{highest_version}*"
                try_message_with_home_menu(context, chat_id=context.job.context['chat_id'],
                                           text=message)


def check_churning(context):
    logger.info("I'm checking if churning occured...")

    user_data = context.job.context['user_data']

    try:
        validators = get_node_accounts()
    except Exception as e:
        logger.exception(e)
        try_message_with_home_menu(context, chat_id=context.job.context['chat_id'], text=NODE_LIST_UNAVAILABLE_ERROR_MSG)
        return

    if 'node_statuses' not in context.bot_data:
        context.bot_data['node_statuses'] = {}
        for validator in validators:
            context.bot_data['node_statuses'][validator['node_address']] = validator['status']
        return

    local_node_statuses = context.bot_data['node_statuses']

    churned_in = []
    churned_out = []
    for validator in validators:
        remote_status = validator['status']
        local_status = local_node_statuses[validator['node_address']] if validator[
                                                                             'node_address'] in local_node_statuses else "unknown"
        if remote_status != local_status:
            if 'active' == remote_status:
                churned_in.append({"address": validator['node_address'], "bond": validator['bond']})
            elif 'active' == local_status:
                churned_out.append({"address": validator['node_address'], "bond": validator['bond']})

    if len(churned_in) or len(churned_out):
        text = "🔄 CHURN SUMMARY\n" \
               "THORChain has successfully churned:\n\n"
        text += "Nodes Added:\n" if len(churned_in) else ""
        for node in churned_in:
            text += f"*{node['address']}*\nBond: *{tor_to_rune(node['bond'])}*\n"
        text += "\nNodes Removed:\n" if len(churned_out) else ""
        for node in churned_out:
            text += f"*{node['address']}*\nBond: *{tor_to_rune(node['bond'])}*\n"
        text += "\nSystem:\n"

        try:
            network = get_network_data()
            text += f"🔓 Network Security: *{network_security_ratio_to_string(get_network_security(network))}*\n\n" \
                    f"💚 Total Active Bond: *{tor_to_rune(network['bondMetrics']['totalActiveBond'])}* (total)\n\n" \
                    "⚖️ Bonded/Staked Ratio: *" + '{:.2f}'.format(int(get_network_security(network) * 100)) + " %*\n\n" \
                    "↩️ Bond ROI: *" + '{:.2f}'.format(float(network['bondingROI']) * 100) + " %* APY\n\n" \
                    "↩️ Stake ROI: *" + '{:.2f}'.format(float(network['stakingROI']) * 100) + " %* APY"
        except Exception as e:
            logger.exception(e)
            text += NETWORK_ERROR_MSG

        try_message_to_all_users(context, text=text)

    for validator in validators:
        context.bot_data['node_statuses'][validator['node_address']] = validator['status']

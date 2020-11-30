from handlers.chat_helpers import try_message_with_home_menu, try_message_to_all_users
from packaging import version

from service.utils import *


def check_thornodes(context):
    """
    Check all added thornodes for any changes.
    """

    chat_id = context.job.context['chat_id']
    user_data = context.job.context['user_data']

    inactive_nodes = []

    for node_address, node_data in user_data.get('nodes', {}).items():

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

            try_message_with_home_menu(context=context,
                                       chat_id=chat_id,
                                       text=text)
            continue

        # isNotBlocked = lastTimestamp < currentTimestamp - timeout
        if float(local_node['last_notification_timestamp']) < \
                float(datetime.timestamp(
                    datetime.now() - timedelta(seconds=local_node['notification_timeout_in_seconds']))):

            # Check which node fields have changed
            changed_fields = [
                field for field in ['status', 'bond', 'slash_points']
                if local_node[field] != remote_node[field]
            ]

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
                text += '\nSlash Points: ' + '{:,}'.format(
                    int(local_node['slash_points']))
                if 'slash_points' in changed_fields:
                    text += ' ➡️ ' + '{:,}'.format(
                        int(remote_node['slash_points']))

                # Update data
                local_node['status'] = remote_node['status']
                local_node['bond'] = remote_node['bond']
                local_node['slash_points'] = remote_node['slash_points']
                local_node['ip_address'] = remote_node['ip_address']
                local_node['last_notification_timestamp'] = datetime.timestamp(
                    datetime.now())
                local_node[
                    'notification_timeout_in_seconds'] *= NOTIFICATION_TIMEOUT_MULTIPLIER

                try_message_with_home_menu(context=context,
                                           chat_id=chat_id,
                                           text=text)
            else:
                local_node[
                    'notification_timeout_in_seconds'] = INITIAL_NOTIFICATION_TIMEOUT

        if local_node['status'] in MONITORED_STATUSES:
            check_thorchain_block_height(context, node_address=node_address)

            check_thorchain_catch_up_status(context, node_address=node_address)

            check_thorchain_midgard_api(context, node_address=node_address)

    for node_address in inactive_nodes:
        del user_data['nodes'][node_address]


def check_versions_status(context):
    user_data = context.job.context['user_data']

    try:
        node_accounts = get_node_accounts()
    except Exception as e:
        logger.exception(e)
        logger.error("I couldn't get the node accounts while checking version status.")
        return

    highest_version = max(map(lambda n: n['version'], node_accounts),
                          key=lambda v: version.parse(v))
    last_newest_version = user_data.get('newest_software_version', None)

    if last_newest_version is None or version.parse(
            highest_version) > version.parse(last_newest_version):
        user_data['newest_software_version'] = highest_version
        for node in user_data.get('nodes', {}).values():
            if version.parse(node['version']) < version.parse(highest_version):
                message = f"Consider updating the software on your node: *{node['alias']}*   ‼️\n" \
                          f"Your software version is *{node['version']}* " \
                          f"but one of the nodes already runs on *{highest_version}*"
                try_message_with_home_menu(
                    context,
                    chat_id=context.job.context['chat_id'],
                    text=message)


def check_churning(context):
    try:
        validators = get_node_accounts()
    except Exception as e:
        logger.exception(e)
        logger.error("I couldn't get the node accounts while checking if churning occured.")
        return

    if 'node_statuses' not in context.bot_data:
        context.bot_data['node_statuses'] = {}
        for validator in validators:
            context.bot_data['node_statuses'][
                validator['node_address']] = validator['status']
        return

    local_node_statuses = context.bot_data['node_statuses']

    churned_in = []
    churned_out = []
    highest_churn_status_since = 0
    for validator in validators:
        if did_churn_happen(validator, local_node_statuses, highest_churn_status_since):
            highest_churn_status_since = int(validator['status_since'])

    for validator in validators:
        remote_status = validator['status']
        local_status = local_node_statuses[
            validator['node_address']] if validator[
                                              'node_address'] in local_node_statuses else "unknown"
        if remote_status != local_status:
            if 'active' == remote_status:
                churned_in.append({
                    "address": validator['node_address'],
                    "bond": validator['bond']
                })
            elif 'active' == local_status:
                churned_out.append({
                    "address": validator['node_address'],
                    "bond": validator['bond']
                })

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
            text += f"🔓 Network Security: *{network_security_ratio_to_string(get_network_security_ratio(network))}*\n\n" \
                    f"💚 Total Active Bond: *{tor_to_rune(network['bondMetrics']['totalActiveBond'])}* (total)\n\n" \
                    "⚖️ Bonded/Staked Ratio: *" + '{:.2f}'.format(
                int(get_network_security_ratio(network) * 100)) + " %*\n\n" \
                                                                  "↩️ Bond ROI: *" + '{:.2f}'.format(
                float(network['bondingROI']) * 100) + " %* APY\n\n" \
                                                      "↩️ Stake ROI: *" + '{:.2f}'.format(
                float(network['stakingROI']) * 100) + " %* APY"
        except Exception as e:
            logger.exception(e)

        try_message_to_all_users(context, text=text)

    for validator in validators:
        context.bot_data['node_statuses'][
            validator['node_address']] = validator['status']


def did_churn_happen(validator, local_node_statuses, highest_churn_status_since) -> bool:
    remote_status = validator['status']
    local_status = local_node_statuses[validator['node_address']] if validator[
                                                                         'node_address'] in local_node_statuses else "unknown"
    if int(validator['status_since']) > highest_churn_status_since and \
            ((local_status == 'ready' and remote_status == 'active') or (
                    local_status == 'active' and remote_status == 'standby')):
        return True
    return False


def check_thorchain_block_height(context, node_address):
    """
    Make sure the block height increases
    """

    chat_id = context.job.context['chat_id']
    node_data = context.job.context['user_data']['nodes'][node_address]

    try:
        block_height = get_latest_block_height(node_data['ip_address'])
    except Exception as e:
        logger.exception(e)
        return

    is_stuck = block_height <= node_data.setdefault('block_height', "0")
    block_height_stuck_count = node_data.setdefault("block_height_stuck_count", 0)

    if is_stuck:
        block_height_stuck_count += 1
        if block_height_stuck_count == 1:
            text = 'Block height is not increasing anymore! 💀' + '\n' + \
                   'IP: ' + node_data['ip_address'] + '\n' + \
                   'THORNode: ' + node_data['alias'] + '\n' + \
                   'Node address: ' + node_address + '\n' + \
                   'Block height stuck at: ' + block_height + '\n\n' + \
                   'Please check your Thornode immediately!'
            try_message_with_home_menu(context=context, chat_id=chat_id, text=text)
    else:
        if block_height_stuck_count >= 1:
            text = f"Block height is increasing again! 👌\n" + \
                   f"IP: {node_data['ip_address']}\n" + \
                   f"THORNode: {node_data['alias']}\n" + \
                   f"Node address: {node_address}\n" + \
                   f"Block height now at: {block_height}\n"
            try_message_with_home_menu(context=context, chat_id=chat_id, text=text)
        block_height_stuck_count = 0

    node_data['block_height'] = block_height
    node_data["block_height_stuck_count"] = block_height_stuck_count


def check_solvency(context):
    try:
        asgard_solvency = asgard_solvency_check()
        yggdrasil_solvency = yggdrasil_check()
    except Exception as e:
        # logger.exception(e) # todo: removeme
        return

    is_solvent = asgard_solvency['is_solvent'] and yggdrasil_solvency['is_solvent']
    insolvency_count = context.bot_data.setdefault("insolvency_count", 0)

    if not is_solvent:
        insolvency_count += 1
        if insolvency_count == MISSING_FUNDS_THRESHOLD:
            text = 'THORChain is *missing funds*! 💀\n\n'
            text += get_solvency_message(asgard_solvency, yggdrasil_solvency)
            try_message_to_all_users(context, text=text)
    else:
        if insolvency_count >= MISSING_FUNDS_THRESHOLD:
            text = 'THORChain is *100% solvent* again! 👌\n'
            try_message_to_all_users(context, text=text)
        insolvency_count = 0

    context.bot_data["insolvency_count"] = insolvency_count


def check_thorchain_catch_up_status(context, node_address):
    """
    Check if node is some blocks behind with catch up status
    """

    chat_id = context.job.context['chat_id']
    node_data = context.job.context['user_data']['nodes'][node_address]

    if 'is_catching_up' not in node_data:
        node_data['is_catching_up'] = False

    try:
        is_currently_catching_up = is_thorchain_catching_up(
            node_data['ip_address'])
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

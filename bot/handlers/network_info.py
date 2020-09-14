from collections import defaultdict, Counter

from helpers import *
from messages import *


def show_network_menu(update, context):
    keyboard = [[InlineKeyboardButton('📊 NETWORK STATS', callback_data='show_network_stats'),
                InlineKeyboardButton('🔒 VAULT ADDRESSES', callback_data='vault_key_addresses')]]

    try_message(context=context, chat_id=update.effective_message.chat_id, text='Choose an option:',
                reply_markup=InlineKeyboardMarkup(keyboard))


async def show_network_stats(update, context):
    """
    Show summarized information of the whole network
    """

    text = "Status of the whole THORChain network: \n"

    try:
        network = get_network_data()
        validators = get_node_accounts()

        statuses_counter = Counter(map(lambda v: v['status'], validators))
        active_validators = filter(lambda v: v['status'] == 'active', validators)
        versions_counter = Counter(map(lambda v: v['version'], active_validators))

        text += "\n📡 Nodes:\n"
        for status in statuses_counter:
            emoji = STATUS_EMOJIS[status] if status in STATUS_EMOJIS else STATUS_EMOJIS["unknown"]
            text += f"  *{str(statuses_counter[status])}* ({status} {emoji})\n"

        total_nodes = len(validators)
        text += f"  = *{str(total_nodes)}* (total)\n"

        text += "\n" + STATUS_EMOJIS["active"] + " Active Bonds:\n  *" + \
                tor_to_rune(network['bondMetrics']['totalActiveBond']) + "* (total)\n  *" + \
                tor_to_rune(network['bondMetrics']['averageActiveBond']) + "* (avg)\n  *" + \
                tor_to_rune(network['bondMetrics']['medianActiveBond']) + "* (median)\n  *" + \
                tor_to_rune(network['bondMetrics']['maximumActiveBond']) + "* (max)\n  *" + \
                tor_to_rune(network['bondMetrics']['minimumActiveBond']) + "* (min)\n"

        text += "\n" + STATUS_EMOJIS["standby"] + "  Standby Bonds:\n  *" + \
                tor_to_rune(network['bondMetrics']['totalStandbyBond']) + "* (total)\n  *" + \
                tor_to_rune(network['bondMetrics']['averageStandbyBond']) + "* (avg)\n  *" + \
                tor_to_rune(network['bondMetrics']['medianStandbyBond']) + "* (median)\n  *" + \
                tor_to_rune(network['bondMetrics']['maximumStandbyBond']) + "* (max)\n  *" + \
                tor_to_rune(network['bondMetrics']['minimumStandbyBond']) + "* (min)\n"

        text += "\n💰 Block Rewards:\n  *" + \
                tor_to_rune(network['blockRewards']['blockReward']) + "* (total)\n  *" + \
                tor_to_rune(network['blockRewards']['bondReward']) + "* (nodes)\n  *" + \
                tor_to_rune(network['blockRewards']['stakeReward']) + "* (stakers)\n  *" + \
                '{:.2f}'.format((int(network['blockRewards']['stakeReward']) / int(
                    network['blockRewards']['blockReward']) * 100)) + " %* (staker share)\n"

        text += f"\n🔓 Network Security: *{network_security_ratio_to_string(get_network_security(network))}*\n"

        text += "\n↩️ Node ROI: *" + \
                '{:.2f}'.format(float(network['bondingROI']) * 100) \
                + " %* APY\n"

        text += "\n📀 Versions:\n"

        counter_versions = sum(versions_counter.values())

        for version in versions_counter:
            text += "  *" + version + "* (" + '{:.2f}'.format(
                (versions_counter[version] / counter_versions) * 100) + "%)\n"

        latest_block_height = get_latest_block_height()
        text += f'\n⛏ Block Height: *{int(latest_block_height):,}*\n'

    except Exception as e:
        logger.exception(e)
        text += NETWORK_ERROR_MSG
    finally:
        try_message_with_home_menu(context=context, chat_id=update.effective_chat.id, text=text)


async def save_pool_address(ip_address, chain_to_node_addresses, unavailable_addresses):
    try:
        pool_addresses = await get_pool_addresses(ip_address)
    except Exception as exc:
        unavailable_addresses.append(ip_address)
        logger.exception(exc)
        return

    for chain_data in pool_addresses['current']:
        chain_to_node_addresses[chain_data['chain']].append(chain_data['address'])


async def show_vault_key_addresses(update, context):
    chain_to_node_addresses = defaultdict(list)
    unavailable_addresses = []

    try:
        node_accounts = get_node_accounts()
    except Exception as e:
        logger.exception(e)
        try_message_with_home_menu(context=context, chat_id=update.effective_chat.id,
                                   text=NODE_LIST_UNAVAILABLE_ERROR_MSG)
        return

    monitored_node_accounts = list(filter(lambda x: x['status'] == 'active', node_accounts))
    ip_addresses = list(map(lambda x: x['ip_address'], monitored_node_accounts))

    await for_each_async(ip_addresses, lambda ip: save_pool_address(ip, chain_to_node_addresses, unavailable_addresses))

    message = ''

    for chain, addresses in chain_to_node_addresses.items():
        message += f"*{chain}*\n"
        distinct_addresses = set(addresses)

        for address in distinct_addresses:
            nodes_agreeing_count = addresses.count(address)
            message += f"{address} (*{str(nodes_agreeing_count)}* "
            message += "node" if nodes_agreeing_count == 1 else "nodes"
            message += ")\n"
        message += "\n"

    if len(unavailable_addresses) > 0:
        message += "😱 I couldn't get pool addresses from these nodes 😱:\n"
        for address in unavailable_addresses:
            message += f"{str(address)}\n"

    try_message_with_home_menu(context=context, chat_id=update.effective_chat.id, text=message)

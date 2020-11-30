from telegram import InlineKeyboardButton
from collections import Counter

from constants.messages import *
from handlers.chat_helpers import *
from service.utils import *


def show_network_menu(update, context):
    keyboard = [[
        InlineKeyboardButton('📊 NETWORK STATS',
                             callback_data='show_network_stats'),
    ], [
        InlineKeyboardButton('💰 SOLVENCY',
                             callback_data='solvency'),
        InlineKeyboardButton('🔒 VAULT ADDRESSES',
                             callback_data='vault_key_addresses')
    ]]

    try_message(context=context,
                chat_id=update.effective_message.chat_id,
                text='Choose an option:',
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
        active_validators = filter(lambda v: v['status'] == 'active',
                                   validators)
        versions_counter = Counter(
            map(lambda v: v['version'], active_validators))

        text += "\n📡 Nodes:\n"
        for status in statuses_counter:
            emoji = STATUS_EMOJIS[
                status] if status in STATUS_EMOJIS else STATUS_EMOJIS["unknown"]
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

        text += f"\n🔓 Network Security: *{network_security_ratio_to_string(get_network_security_ratio(network))}*\n"

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
        try_message_with_home_menu(context=context,
                                   chat_id=update.effective_chat.id,
                                   text=text)

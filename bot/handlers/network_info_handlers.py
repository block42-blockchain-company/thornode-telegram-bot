from constants.messages import *
from handlers.chat_helpers import try_message_with_home_menu
from service.utils import *


def solvency_stats(update, context):
    logger.info("I'm getting the Solvency Stats...")
    try:
        asgard_solvency = asgard_solvency_check()
        yggdrasil_solvency = yggdrasil_check()
    except Exception as e:
        logger.exception(e)
        try_message_with_home_menu(context, update.effective_chat.id, NETWORK_ERROR_MSG)
        return

    message = "💰 Solvency Check\n"

    message += "THORChain is *100% Solvent* ✅\n\n" \
        if asgard_solvency['is_solvent'] and yggdrasil_solvency['is_solvent'] \
        else "THORChain is *missing funds*! 😱\n\n"

    message += get_solvency_message(asgard_solvency, yggdrasil_solvency)

    try_message_with_home_menu(context, update.effective_chat.id, message)


async def save_pool_address(ip_address, chain_to_node_addresses,
                            unavailable_addresses):
    try:
        pool_addresses = await get_pool_addresses(ip_address)
    except Exception as exc:
        unavailable_addresses.append(ip_address)
        logger.exception(exc)
        return

    for chain_data in pool_addresses['current']:
        chain_to_node_addresses[chain_data['chain']].append(
            chain_data['address'])


async def show_vault_key_addresses(update, context):
    chain_to_node_addresses = defaultdict(list)
    unavailable_addresses = []

    try:
        node_accounts = get_node_accounts()
    except Exception as e:
        logger.exception(e)
        logger.error("Couldn't get node accounts while showing vault_key_addresses.")
        return

    monitored_node_accounts = list(
        filter(lambda x: x['status'] == 'active', node_accounts))
    ip_addresses = list(map(lambda x: x['ip_address'], monitored_node_accounts))

    await for_each_async(
        ip_addresses, lambda ip: save_pool_address(ip, chain_to_node_addresses,
                                                   unavailable_addresses))

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

    try_message_with_home_menu(context=context,
                               chat_id=update.effective_chat.id,
                               text=message)

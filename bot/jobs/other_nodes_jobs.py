from constants.node_ips import *
from handlers.chat_helpers import *
from models.nodes import *


def check_other_nodes_health(context):
    nodes = []
    nodes.extend(BinanceNode.from_ips(BINANCE_NODE_IPS))
    nodes.extend(EthereumNode.from_ips(ETHEREUM_NODE_IPS))
    nodes.extend(BitcoinNode.from_ips(BITCOIN_NODE_IPS))

    for node in nodes:
        message = check_health(node, context)
        if message:
            try_message_to_all_users(context, text=message)


def check_health(node: Node, context) -> [str, None]:
    try:
        is_node_currently_healthy = node.is_healthy()
    except UnauthorizedException:
        return f"😱 Your {node.to_string()} returns 401 - Unauthorized! 😱\n" \
               f" Please make sure the credentials you set are correct!"
    except Exception as e:
        logger.error(e)
        return None

    was_node_healthy = context.bot_data.setdefault(node.node_id, {}).get('health', True)

    if was_node_healthy != is_node_currently_healthy:
        context.bot_data[node.node_id]['health'] = is_node_currently_healthy

        if is_node_currently_healthy:
            text = f'{node.to_string()} is healthy again! 👌\n'
        else:
            text = f'{node.to_string()} is not healthy anymore! 💀 \n' \
                   f'Please check your node immediately'

        return text
    else:
        return None


def check_bitcoin_height_increase_job(context):
    for node in BitcoinNode.from_ips(BITCOIN_NODE_IPS):
        message = check_block_height_increase(context, node)
        if message:
            try_message_to_all_users(context, message)


def check_ethereum_height_increase_job(context):
    for node in EthereumNode.from_ips(ETHEREUM_NODE_IPS):
        message = check_block_height_increase(context, node)
        if message:
            try_message_to_all_users(context, message)


def check_block_height_increase(context, node: Node) -> [str, None]:
    try:
        current_block_height = node.get_block_height()
    except UnauthorizedException:
        return f"😱 Your {node.to_string()} returns 401 - Unauthorized! 😱\n" \
               f" Please make sure the credentials you set are correct!"
    except Exception as e:
        logger.error(e)
        return None

    # Stuck count:
    # 0 == everything's alright
    # 1 == just got stuck
    # -1 == just got unstuck
    # > 1 == still stuck

    node_data = context.bot_data.setdefault(node.node_id, {})
    last_block_height = node_data.get('block_height', float('-inf'))
    message = None

    if current_block_height <= last_block_height:
        node_data['block_height_stuck_count'] = node_data.get('block_height_stuck_count', 0) + 1
    elif node_data.get('block_height_stuck_count', 0) > 0:
        message = f"Block height is increasing again! 👌\n" \
                  f"{node.to_string()}"
        node_data['block_height_stuck_count'] = -1

    if node_data.get('block_height_stuck_count', 0) == 1:
        message = 'Block height is not increasing anymore! 💀\n' \
                  f"{node.to_string()}"

    node_data['block_height'] = current_block_height

    return message


def check_other_nodes_syncing_job(context):
    """
    Check if node is syncing or not and send appropriate notification
    """

    nodes = []
    nodes.extend(EthereumNode.from_ips(ETHEREUM_NODE_IPS))
    nodes.extend(BitcoinNode.from_ips(BITCOIN_NODE_IPS))

    for node in nodes:
        message = check_other_nodes_syncing(node, context)
        if message:
            try_message_to_all_users(context, text=message)


def check_other_nodes_syncing(node: Node, context) -> [str, None]:
    try:
        is_synced = node.is_fully_synced()
    except UnauthorizedException:
        return f"😱 Your {node.to_string()} returns 401 - Unauthorized! 😱\n" \
               f" Please make sure the credentials you set are correct!"

    was_synced = context.bot_data.setdefault(node.node_id, {}).get('syncing', True)

    if is_synced != was_synced:
        if is_synced:
            message = f"Your {node.to_string()} is fully synced again!👌\n"
        else:
            message = f"Your {node.to_string()} node is syncing with the network... 🚧\n"

        context.bot_data[node.node_id]['syncing'] = is_synced
        return message
    else:
        return None

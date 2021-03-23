from constants.globals import logger
from constants.messages import NetworkHealthStatus, NETWORK_HEALTHY_AGAIN, get_network_health_warning
from handlers.chat_helpers import try_message_to_all_users
from service.thorchain_network_service import get_network_data, get_thorchain_network_constants
from service.utils import network_security_ratio_to_string, get_network_security_ratio, flatten_dictionary


def check_network_security_job(context):
    text = check_network_security(context)
    if text is not None:
        try_message_to_all_users(context, text=text)


def check_network_security(context):
    network_health_status = network_security_ratio_to_string(get_network_security_ratio(get_network_data()))
    logger.info(f"Network Health Status: {network_health_status}")

    if 'network_health_status' not in context.bot_data:
        context.bot_data["network_health_status"] = network_health_status
        return None

    if network_health_status != context.bot_data["network_health_status"]:
        context.bot_data["network_health_status"] = network_health_status.value

        if network_health_status is NetworkHealthStatus.OPTIMAL:
            logger.info(f"Network is healthy again: {network_health_status.value}")
            return NETWORK_HEALTHY_AGAIN

        logger.info(f"Network is unhealthy: {network_health_status.value}")
        return get_network_health_warning(network_health_status)
    else:
        return None


def check_thorchain_constants_job(context):
    changed_values = check_thorchain_constants(context)

    if changed_values is not None:
        try_message_to_all_users(context, changed_values)


def check_thorchain_constants(context) -> [str, None]:
    new_constants = flatten_dictionary(get_thorchain_network_constants())

    if "constants" not in context.bot_data:
        context.bot_data["constants"] = new_constants
        return None

    old_constants = context.bot_data["constants"]

    try:
        if old_constants != new_constants:
            changed_keys = set()

            # Detect Changes
            difference = new_constants.items() - old_constants.items()  # Get added and changed keys
            difference |= old_constants.items() - new_constants.items()  # Merge removed and changed keys
            changed_keys.update([k for k, v in list(difference)])  # Register keys

            # Generate Message
            text = "Global Network Constants Change 📢:\n"
            for key in changed_keys:
                if key in new_constants and key in old_constants:
                    text += f"{key} has changed " \
                            f"from {old_constants[key]} " \
                            f"to {new_constants[key]}.\n"

                elif key in new_constants and key not in old_constants:
                    text += f"{key} with value {new_constants[key]} has been added.\n"

                elif key not in new_constants and key in old_constants:
                    text += f"{key} has been removed.\n"

            # Update Data
            context.bot_data["constants"] = new_constants
            return text

        return None

    except:
        context.bot_data["constants"] = None
        return None

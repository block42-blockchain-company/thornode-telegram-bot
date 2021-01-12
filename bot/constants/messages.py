from constants.globals import HEALTH_EMOJIS, NetworkHealthStatus

NETWORK_ERROR = '😱 There was an error while getting data 😱\nAn API endpoint is down!'
HEALTH_LEGEND = f'\n*Node health*:\n{HEALTH_EMOJIS[True]} - *healthy*\n{HEALTH_EMOJIS[False]} - *unhealthy*\n' \
                f'{HEALTH_EMOJIS[None]} - *unknown*\n'

NETWORK_HEALTH_CURATION = "The network is safe again."


def NETWORK_HEALTH_WARNING(network_security_state: NetworkHealthStatus) -> str:
    return f"Network not safe! 💀💀💀 {network_security_state.value}"


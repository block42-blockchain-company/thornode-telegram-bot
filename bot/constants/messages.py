from constants.globals import HEALTH_EMOJIS, NetworkHealthStatus

NETWORK_ERROR = '😱 There was an error while getting data 😱\nAn API endpoint is down!'
HEALTH_LEGEND = f'\n*Node health*:\n{HEALTH_EMOJIS[True]} - *healthy*\n{HEALTH_EMOJIS[False]} - *unhealthy*\n' \
                f'{HEALTH_EMOJIS[None]} - *unknown*\n'

NETWORK_HEALTH_CURATION = "The network is safe and efficient again! ✅"


def NETWORK_HEALTH_WARNING(network_health_status: NetworkHealthStatus) -> str:
    severity = "🤒"
    if network_health_status is NetworkHealthStatus.INSECURE:
        severity = "💀"
    elif network_health_status is NetworkHealthStatus.INEFFICIENT:
        severity = "🦥"

    return f"Network health is not optimal: {network_health_status.value} {severity}"


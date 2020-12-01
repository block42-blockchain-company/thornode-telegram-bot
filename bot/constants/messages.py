from constants.globals import HEALTH_EMOJIS

NETWORK_ERROR_MSG = '😱 There was an error while getting data 😱\nAn API endpoint is down!'
HEALTH_LEGEND = f'\n*Node health*:\n{HEALTH_EMOJIS[True]} - *healthy*\n{HEALTH_EMOJIS[False]} - *unhealthy*\n' \
                f'{HEALTH_EMOJIS[None]} - *unknown*\n'

import os
from datetime import datetime, timedelta

from bot.constants import storage_path

HEALTHY = 0
UNHEALTHY = 1


def check_health():
    last_thornode_bot_timestamp = open(os.sep.join([storage_path, 'health.check'])).read()

    if float(last_thornode_bot_timestamp) >= float(datetime.timestamp(datetime.now() - timedelta(seconds=30))):
        return HEALTHY
    else:
        return UNHEALTHY


if __name__ == '__main__':
    exit(check_health())

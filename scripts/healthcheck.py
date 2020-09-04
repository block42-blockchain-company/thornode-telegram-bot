import os
from datetime import datetime, timedelta

HEALTHY = 0
UNHEALTHY = 1


def check_health():
    storage_path = os.sep.join([os.path.dirname(os.path.realpath(__file__)), os.path.pardir, 'storage'])
    last_thornode_bot_timestamp = open(os.sep.join([storage_path, 'health.check'])).read()

    if float(last_thornode_bot_timestamp) >= float(datetime.timestamp(datetime.now() - timedelta(seconds=30))):
        return HEALTHY
    else:
        return UNHEALTHY


if __name__ == '__main__':
    exit(check_health())

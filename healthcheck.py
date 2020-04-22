from datetime import datetime, timedelta

HEALTHY = 0
UNHEALTHY = 1


def check_health():
    return UNHEALTHY
    timestamp_benchmark = datetime.timestamp(datetime.now() - timedelta(seconds=30))
    with open('storage/health.check') as healthcheck_file:
        thornode_bot_timestamp = healthcheck_file.read()

    if float(thornode_bot_timestamp) > timestamp_benchmark:
        return HEALTHY
    else:
        return UNHEALTHY


if __name__ == '__main__':
    exit(check_health())

import os
import logging
import random

# Enable logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO)
logger = logging.getLogger(__name__)

DEBUG = bool(os.environ['DEBUG'] == 'True') if 'DEBUG' in os.environ else False
TELEGRAM_BOT_TOKEN = os.environ['TELEGRAM_BOT_TOKEN']

NETWORK_TYPES = ["TESTNET", "CHAOSNET"]
NETWORK_TYPE = os.environ['NETWORK_TYPE'] \
    if 'NETWORK_TYPE' in os.environ and os.environ['NETWORK_TYPE'] in NETWORK_TYPES and not DEBUG else 'TESTNET'

# Set BINANCE_NODE_IP depending on mode (if None, no Binance jobs are not executed)
if DEBUG:
    BINANCE_NODE_IPS = ['localhost', '0.0.0.0']
    BINANCE_DEX_ENDPOINT = "https://testnet-dex-atlantic.binance.org"
else:
    BINANCE_NODE_IPS = [binance_ip for binance_ip in
                        os.environ['BINANCE_NODE_IPS'].split(",")] \
        if 'BINANCE_NODE_IPS' in os.environ and os.environ['BINANCE_NODE_IPS'] != "" \
        else []
    if BINANCE_NODE_IPS:
        BINANCE_DEX_ENDPOINT = f"http://{random.choice(BINANCE_NODE_IPS)}:27146"
    else:
        BINANCE_DEX_ENDPOINT = "https://dex.binance.org" if NETWORK_TYPE == 'CHAOSNET' \
            else "https://testnet-dex-atlantic.binance.org"

BITCOIN_NODE_IPS = list(filter(None, os.environ.get('BITCOIN_NODE_IPS', '').split(",")))
BITCOIN_NODE_USERNAMES = list(filter(None, os.environ.get('BITCOIN_NODE_USERNAMES', '').split(",")))
BITCOIN_NODE_PASSWORDS = list(filter(None, os.environ.get('BITCOIN_NODE_PASSWORDS', '').split(",")))

if (len(BITCOIN_NODE_IPS) != len(BITCOIN_NODE_USERNAMES)) | (len(BITCOIN_NODE_IPS) != len(BITCOIN_NODE_PASSWORDS)):
    logger.warning("Error while reading your bitcoin nodes ip addresses!\n"
                   "You must set exactly the same number of IPs, usernames and passwords to the json-rpc api.\n"
                   "You set:\n"
                   f"BITCOIN_NODE_IPS array length: ({len(BITCOIN_NODE_IPS)})\n"
                   f"BITCOIN_NODE_USERNAMES array length: ({len(BITCOIN_NODE_USERNAMES)})\n"
                   f"BITCOIN_NODE_PASSWORDS array length: ({len(BITCOIN_NODE_PASSWORDS)})\n")
    BITCOIN_NODE_IPS.clear()

ETHEREUM_NODE_IPS = os.environ.get('ETHEREUM_NODE_IPS', '').split(",")

ADMIN_USER_IDS = [
    int(admin_id) for admin_id in os.environ['ADMIN_USER_IDS'].split(",")
] if 'ADMIN_USER_IDS' in os.environ else []
DOCKER_CURL_CMD = "curl --max-time 30 --no-buffer -s --unix-socket /var/run/docker.sock"

# By how much we multiply the notifiction timeout in case of continous Thornode attribute changes
NOTIFICATION_TIMEOUT_MULTIPLIER = 1.5
# Base notification timeout in seconds
INITIAL_NOTIFICATION_TIMEOUT = 15

# Emojis for status of THORNodes
STATUS_EMOJIS = {
    "unknown": "❓",
    "whitelisted": "📋",
    "standby": "📆",
    "ready": "🙋🏽‍♂️",
    "active": "💚",
    "disabled": "🔴"
}

MONITORED_STATUSES = ["standby", "ready", "active"]

JOB_INTERVAL_IN_SECONDS = 5 if DEBUG else 30

# Paths
storage_path = os.sep.join(
    [os.path.dirname(os.path.realpath(__file__)), os.path.pardir, 'storage'])
session_data_path = os.sep.join([storage_path, 'session.data'])

CONNECTION_TIMEOUT = 10

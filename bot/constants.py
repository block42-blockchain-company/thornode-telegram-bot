import os
import logging
import random

# Enable logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO)
logger = logging.getLogger(__name__)

DEBUG = bool(os.environ['DEBUG'] == 'True') if 'DEBUG' in os.environ else False
TELEGRAM_BOT_TOKEN = os.environ.get('TELEGRAM_BOT_TOKEN', '')

NETWORK_TYPES = ["TESTNET", "CHAOSNET"]
NETWORK_TYPE = os.getenv("NETWORK_TYPE").upper() \
    if os.getenv("NETWORK_TYPE", "notFound").upper() in NETWORK_TYPES and not DEBUG else 'TESTNET'

# Set BINANCE_NODE_IP depending on mode (if None, no Binance jobs are not executed)
if DEBUG:
    BINANCE_NODE_IPS = ['localhost', '0.0.0.0']
    BINANCE_DEX_ENDPOINT = "https://testnet-dex-atlantic.binance.org"
else:
    BINANCE_NODE_IPS = [binance_ip for binance_ip in
                        os.environ['BINANCE_NODE_IPS'].split(",")] \
        if 'BINANCE_NODE_IPS' in os.environ and os.environ['BINANCE_NODE_IPS'] != "" \
        else []
    BINANCE_DEX_ENDPOINT = "https://dex.binance.org" if NETWORK_TYPE == 'CHAOSNET' \
        else "https://testnet-dex-atlantic.binance.org"

ETHEREUM_NODE_IPS = list(filter(None, os.environ.get('ETHEREUM_NODE_IPS', '').split(",")))
BITCOIN_NODE_IPS = list(filter(None, os.environ.get('BITCOIN_NODE_IPS', '').split(",")))
BITCOIN_NODE_USERNAMES = list(filter(None, os.environ.get('BITCOIN_NODE_USERNAMES', '').split(",")))
BITCOIN_NODE_PASSWORDS = list(filter(None, os.environ.get('BITCOIN_NODE_PASSWORDS', '').split(",")))

if (len(BITCOIN_NODE_IPS) != len(BITCOIN_NODE_USERNAMES)) or (len(BITCOIN_NODE_IPS) != len(BITCOIN_NODE_PASSWORDS)):
    logger.warning("Error while reading your bitcoin nodes ip addresses!\n"
                   "You must set exactly the same number of IPs, usernames and passwords to the json-rpc api.\n"
                   "You set:\n"
                   f"BITCOIN_NODE_IPS array length: ({len(BITCOIN_NODE_IPS)})\n"
                   f"BITCOIN_NODE_USERNAMES array length: ({len(BITCOIN_NODE_USERNAMES)})\n"
                   f"BITCOIN_NODE_PASSWORDS array length: ({len(BITCOIN_NODE_PASSWORDS)})\n")
    BITCOIN_NODE_IPS.clear()

ALLOWED_USER_IDS = 'ALL' if os.getenv("ALLOWED_USER_IDS", "notFound").upper() == 'ALL' \
    else [int(allowed_id) for allowed_id in os.getenv("ALLOWED_USER_IDS", []).split(",")]

# By how much we multiply the notification timeout in case of continuous Thornode attribute changes
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
MISSING_FUNDS_THRESHOLD = 10  # Number of cycles that thorchain can be insolvent before a message is sent

REQUEST_POSTFIX = '?height=0'  # currently needed to get correct results due to a bug in thornodes

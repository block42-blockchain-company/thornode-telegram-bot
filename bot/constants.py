import os
import logging

DEBUG = bool(os.environ['DEBUG'] == 'True') if 'DEBUG' in os.environ else False
TELEGRAM_BOT_TOKEN = os.environ['TELEGRAM_BOT_TOKEN']

NETWORK_TYPES = ["TESTNET", "CHAOSNET"]
NETWORK_TYPE = os.environ['NETWORK_TYPE'] \
    if 'NETWORK_TYPE' in os.environ and os.environ['NETWORK_TYPE'] in NETWORK_TYPES and not DEBUG else 'TESTNET'

# Set BINANCE_NODE_IP depending on mode (if None, no Binance jobs are not executed)
if DEBUG:
    BINANCE_NODE_IP = 'localhost'
elif 'BINANCE_NODE_IP' in os.environ and os.environ['BINANCE_NODE_IP']:
    BINANCE_NODE_IP = os.environ['BINANCE_NODE_IP']
else:
    BINANCE_NODE_IP = None

ADMIN_USER_IDS = [int(admin_id) for admin_id in
                  os.environ['ADMIN_USER_IDS'].split(",")] if 'ADMIN_USER_IDS' in os.environ else []
DOCKER_CURL_CMD = "curl --max-time 30 --no-buffer -s --unix-socket /var/run/docker.sock"

# By how much we multiply the notifiction timeout in case of continous Thornode attribute changes
NOTIFICATION_TIMEOUT_MULTIPLIER = 1.5
# Base notification timeout in seconds
INITIAL_NOTIFICATION_TIMEOUT = 15

# Emojis for status of THORNodes
STATUS_EMOJIS = {"unknown": "❓", "whitelisted": "📋", "standby": "📆", "ready": "🙋🏽‍♂️", "active": "💚", "disabled": "🔴"}

JOB_INTERVAL_IN_SECONDS = 5 if DEBUG else 30

# Enable logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

# Paths
storage_path = os.sep.join([os.path.dirname(os.path.realpath(__file__)), os.path.pardir, 'storage'])
session_data_path = os.sep.join([storage_path, 'session.data'])

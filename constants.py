import os
import logging
from telegram.ext import (
    ConversationHandler,
)

DEBUG = bool(os.environ['DEBUG'] == 'True') if 'DEBUG' in os.environ else False
TELEGRAM_BOT_TOKEN = os.environ['TELEGRAM_BOT_TOKEN']

# Set THORCHAIN_NODE_IP depending on mode (if None, certain node health jobs are not executed)
if DEBUG:
    THORCHAIN_NODE_IP = 'localhost'
elif 'THORCHAIN_NODE_IP' in os.environ and os.environ['THORCHAIN_NODE_IP']:
    THORCHAIN_NODE_IP = os.environ['THORCHAIN_NODE_IP']
else:
    THORCHAIN_NODE_IP = None

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
STATUS_EMOJIS = {"active": "💚", "standby": "📆", "deactive": "🔴"}

# Enable logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

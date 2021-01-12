import os
import logging
from enum import Enum

# LOGGING
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO)
logger = logging.getLogger(__name__)

DEBUG = bool(os.environ['DEBUG'] == 'True') if 'DEBUG' in os.environ else False
TELEGRAM_BOT_TOKEN = os.environ.get('TELEGRAM_BOT_TOKEN', '')

# WHITELISTED USERS
if os.getenv("ALLOWED_USER_IDS", "notFound").upper() == 'ALL':
    ALLOWED_USER_IDS = 'ALL'
elif os.getenv("ALLOWED_USER_IDS"):
    ALLOWED_USER_IDS = [int(allowed_id) for allowed_id in os.getenv("ALLOWED_USER_IDS").split(",")]
else:
    ALLOWED_USER_IDS = []

# By how much we multiply the notification timeout in case of continuous Thornode attribute changes
NOTIFICATION_TIMEOUT_MULTIPLIER = 1.5
# Base notification timeout in seconds
INITIAL_NOTIFICATION_TIMEOUT = 15

# Emojis

# Be aware that keys of STATUS_EMOJIS are displayed to the user
STATUS_EMOJIS = {
    "unknown": "❓",
    "whitelisted": "📋",
    "standby": "📆",
    "ready": "✔️",
    "active": "💚",
    "disabled": "🔴"
}

HEALTH_EMOJIS = {
    None: '❓',
    True: '💗',
    False: '🖤‼'
}

# Paths
storage_path = os.sep.join(
    [os.path.dirname(os.path.realpath(__file__)), os.path.pardir, os.path.pardir, 'storage'])
session_data_path = os.sep.join([storage_path, 'session.data'])

CONNECTION_TIMEOUT = 10
MISSING_FUNDS_THRESHOLD = 10  # Number of cycles that thorchain can be insolvent before a message is sent

REQUEST_POSTFIX = '?height=0'  # currently needed to get correct results due to a bug in thornodes

# Other

MONITORED_STATUSES = ["standby", "ready", "active"]

JOB_INTERVAL_IN_SECONDS = 5 if DEBUG else 30

# SETTINGS
SLASH_POINTS_NOTIFICATION_THRESHOLD_DEFAULT = 3


class NetworkHealthStatus(Enum):
    INEFFICIENT = "Inefficient"
    OVERBONDED = "Overbonded"
    OPTIMAL = "Optimal"
    UNDBERBONDED = "Underbonded"
    INSECURE = "Insecure"

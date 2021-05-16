import os
import logging

# LOGGING
logging.basicConfig(
    format='%(asctime)s - %(filename)s - %(levelname)s - %(message)s',
    level=logging.INFO)
logger = logging.getLogger()

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

# Keyboard Limit for a single message
KEYBOARD_PAGE_SIZE = 30

# Emojis
# Be aware that keys of STATUS_EMOJIS are displayed to the user
STATUS_EMOJIS = {
    "Unknown": "❓",
    "Whitelisted": "📋",
    "Standby": "📆",
    "Ready": "✔️",
    "Active": "💚",
    "Disabled": "🔴"
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

MONITORED_STATUSES = ["STANDBY", "READY", "ACTIVE"]
JOB_INTERVAL_IN_SECONDS = 5 if DEBUG else 30

# Thorchain
NETWORK_TYPES = ["TESTNET", "CHAOSNET"]
NETWORK_TYPE = os.getenv("NETWORK_TYPE").upper() \
    if os.getenv("NETWORK_TYPE", "notFound").upper() in NETWORK_TYPES and not DEBUG else 'TESTNET'

SLASH_POINTS_NOTIFICATION_THRESHOLD_DEFAULT = 3
THORCHAIN_ONCHAIN_API_URL = "https://thorchain-service.b42.tech/v1/"

DEFAULT_SEED_LIST = "https://seed.thorchain.info/" \
    if NETWORK_TYPE == "CHAOSNET" else "https://testnet.seed.thorchain.info/"

SEED_LIST_URL = os.environ.get("SEED_LIST_URL", DEFAULT_SEED_LIST)

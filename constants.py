import os
import logging
from telegram.ext import (
    ConversationHandler,
)

TELEGRAM_BOT_TOKEN = os.environ['TELEGRAM_BOT_TOKEN']
THORCHAIN_NODE_IP = os.environ['THORCHAIN_NODE_IP'] if 'THORCHAIN_NODE_IP' in os.environ else 'localhost'
DEBUG = bool(os.environ['DEBUG'] == 'True') if 'DEBUG' in os.environ else False
ADMIN_USER_IDS = [int(admin_id) for admin_id in
                  os.environ['ADMIN_USER_IDS'].split(",")] if 'ADMIN_USER_IDS' in os.environ else []
DOCKER_CURL_CMD = "curl --max-time 30 --no-buffer -s --unix-socket /var/run/docker.sock"

# Shortcut for ConversationHandler.END
END = ConversationHandler.END
# Conversation state(s)
THORNODE_MENU, WAIT_FOR_ADDRESS, WAIT_FOR_DETAIL, WAIT_FOR_CONFIRMATION, ADMIN_MENU = range(5)

# Enable logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

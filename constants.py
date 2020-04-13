import os

TYPING_ADDRESS = range(1)

TELEGRAM_BOT_TOKEN = os.environ["TELEGRAM_BOT_TOKEN"]

NODE_FIELDS = ["status", "bond", "slash_points"]

HARDCODED_NODE = "http://67.205.166.241:1317/thorchain/nodeaccounts"
HARDCODED_LOCAL_NODE = "http://localhost:8000/node_data.json"
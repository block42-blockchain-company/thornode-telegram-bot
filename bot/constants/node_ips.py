import os

from constants.globals import DEBUG, logger

NETWORK_TYPES = ["TESTNET", "CHAOSNET"]
NETWORK_TYPE = os.getenv("NETWORK_TYPE").upper() \
    if os.getenv("NETWORK_TYPE", "notFound").upper() in NETWORK_TYPES and not DEBUG else 'TESTNET'

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

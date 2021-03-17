import os

from constants.globals import DEBUG

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


SCHASS = os.environ.get('BITCOIN_NODE_IPS', '')

ETHEREUM_NODE_IPS = list(filter(None, os.environ.get('ETHEREUM_NODE_IPS', '').split(",")))
BITCOIN_NODE_IPS = list(filter(None, os.environ.get('BITCOIN_NODE_IPS', '').split(",")))  # user1:password1@1.2.3.4:1337
BITCOIN_CASH_NODE_IPS = list(filter(None, os.environ.get('BITCOIN_CASH_NODE_IPS', '').split(",")))
LITECOIN_NODE_IPS = list(filter(None, os.environ.get('LITECOIN_NODE_IPS', '').split(",")))

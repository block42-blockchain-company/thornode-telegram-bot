# For new API mocked calls, instead of writing from files, simply return data from here.
# In the future let's consider some form of dependency injections depending on the DEBUG flag.
# Or form of map in form {"url_path":{"result_map"}}

thorchain_last_block_mock = {
    "chain": "BNB",
    "lastobservedin": "129145816",
    "lastsignedout": "1520564",
    "thorchain": "1520569"
}

# BINANCE
binance_is_syncing_mock = False
binance_last_block_mock = 10000
binance_node_healthy_mock = True

# ETH
eth_is_syncing_mock = False
eth_last_block_mock = 10000
eth_node_healthy_mock = True

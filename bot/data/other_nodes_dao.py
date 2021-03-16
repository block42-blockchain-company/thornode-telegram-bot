import itertools
from typing import List

from constants.node_ips import *
from models.nodes import *


class Singleton(type):
    _instances = {}

    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            cls._instances[cls] = super(Singleton, cls).__call__(*args, **kwargs)
        return cls._instances[cls]


class OtherNodesDao(metaclass=Singleton):
    other_nodes = None

    def __init__(self):
        self.other_nodes = {}
        all_nodes = itertools.chain(EthereumNode.from_ips(ETHEREUM_NODE_IPS),
                                    BitcoinNode.from_ips(BITCOIN_NODE_IPS),
                                    BinanceNode.from_ips(BINANCE_NODE_IPS),
                                    BitcoinCashNode.from_ips(BITCOIN_CASH_NODE_IPS),
                                    LiteCoinNode.from_ips(LITECOIN_NODE_IPS))
        for node in all_nodes:
            self.other_nodes[str(hash(node))] = node

    def get_all_nodes(self) -> List[Node]:
        return list(self.other_nodes.values())

    def get_node_by_hash(self, node_hash) -> [Node, None]:
        return self.other_nodes.get(str(node_hash), None)

    def get_nodes_by_network_names(self, names: List) -> List[Node]:
        return list(filter(lambda n: n.network_name in names, self.get_all_nodes()))

import abc

import requests

from helpers import eth_rpc_request, btc_rpc_request
from service.thorchain_network_service import is_binance_node_healthy


class Node(abc.ABC):
    node_id: str
    node_ip: str
    network_name: str

    def __init__(self, node_ip, network_name):
        self.node_ip = node_ip
        self.network_name = network_name
        self.node_id = f'{network_name}-{node_ip}'

    @abc.abstractmethod
    def is_healthy(self) -> bool:
        pass

    @abc.abstractmethod
    def is_fully_synced(self) -> bool:
        pass

    @abc.abstractmethod
    def get_block_height(self):
        pass

    def to_string(self):
        return f"{self.network_name} node ({self.node_ip})"



class BitcoinNode(Node):
    max_time_for_block_height_increase_in_seconds = 60 * 60  # 1 hour

    def __init__(self, node_ip, username, password):
        super().__init__(node_ip, "Bitcoin")
        self.username = username
        self.password = password

    def is_fully_synced(self) -> bool:
        node_block_count = self.get_block_height()
        public_block_count = requests.get(
            "https://blockchain.info/q/getblockcount").json()

        difference = abs(public_block_count - node_block_count)

        return difference <= 1  # For difference 1 and 0 we assume that it is synced

    def get_block_height(self):
        block_count_res = btc_rpc_request(ip=self.node_ip, username=self.username, password=self.password,
                                          method='getblockcount')
        if block_count_res.status_code == 401:
            raise UnauthorizedException()

        return block_count_res.json()['result']

    def is_healthy(self) -> bool:
        res = btc_rpc_request(ip=self.node_ip, username=self.username, password=self.password,
                              method='getblockchaininfo')
        if res.status_code == 401:
            raise UnauthorizedException()

        return res.ok

    @staticmethod
    def from_ips_with_credentials(ips, usernames, passwords) -> list:
        if (len(ips) != len(usernames)) or (len(ips) != len(passwords)):
            raise ValueError("Ips, usernames and passwords arguments must be of the same lenght!")

        btc_nodes = []

        for index, btc_ip in enumerate(ips):
            username = usernames[index]
            password = passwords[index]
            btc_nodes.append(BitcoinNode(btc_ip, username, password))

        return btc_nodes


class EthereumNode(Node):
    max_time_for_block_height_increase_in_seconds = 60 * 2  # 2 mins

    def __init__(self, node_ip):
        super().__init__(node_ip, "Ethereum")

    def is_fully_synced(self) -> bool:
        is_syncing = eth_rpc_request(self.node_ip, method="eth_syncing").json()['result']

        return not is_syncing

    def get_block_height(self):
        return int(eth_rpc_request(self.node_ip, method="eth_blockNumber").json()['result'], 16)

    def is_healthy(self) -> bool:
        return eth_rpc_request(ip=self.node_ip, method="eth_protocolVersion").ok

    @staticmethod
    def from_ips(ips) -> list:
        return list(map(lambda n: EthereumNode(n), ips))


class BinanceNode(Node):
    def __init__(self, node_ip):
        super().__init__(node_ip, "Binance")

    def is_fully_synced(self) -> bool:
        # We didn't implement it for Binance yet
        return True

    def get_block_height(self):
        # We didn't implement it for Binance yet
        raise NotImplementedError()

    def is_healthy(self) -> bool:
        return is_binance_node_healthy(self.node_ip)

    @staticmethod
    def from_ips(ips) -> list:
        return list(map(lambda n: BinanceNode(n), ips))


class UnauthorizedException(Exception):
    pass

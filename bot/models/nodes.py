import abc

from service.general_network_service import *
from service.thorchain_network_service import *


class Node(abc.ABC):
    node_id: str
    node_ip: str
    network_name: str
    network_short_name: str

    def __init__(self, node_ip, network_name, network_short_name):
        self.node_ip = node_ip
        self.network_name = network_name
        self.node_id = f'{network_name}-{node_ip}'
        self.network_short_name = network_short_name

    @abc.abstractmethod
    def is_healthy(self) -> bool:
        pass

    @abc.abstractmethod
    def is_fully_synced(self) -> bool:
        pass

    @abc.abstractmethod
    def get_block_height(self):
        pass

    @abc.abstractmethod
    def get_network_block_count(self):
        pass

    def __hash__(self):
        return hash(self.node_id)

    def to_string(self):
        return f"{self.network_name} node ({self.node_ip})"


class BitcoinNode(Node):
    max_time_for_block_height_increase_in_seconds = 60 * 60  # 1 hour
    network_name = "Bitcoin"
    ip_with_credentials: str = None

    def __init__(self, address):
        self.ip_with_credentials = address
        ip = address.split("@")[-1].split(":")[0]
        super().__init__(ip, self.network_name, "BTC")
        self.address = address

    def is_fully_synced(self) -> bool:
        info = btc_rpc_request(address=self.ip_with_credentials, method='getblockchaininfo').json()['result']

        return info['blocks'] == info['headers']

    def get_block_height(self):
        block_count_res = btc_rpc_request(address=self.ip_with_credentials, method='getblockcount')
        if block_count_res.status_code == 401:
            raise UnauthorizedException()

        return block_count_res.json()['result']

    def is_healthy(self) -> bool:
        res = btc_rpc_request(address=self.ip_with_credentials,
                              method='getblockchaininfo')
        if res.status_code == 401:
            raise UnauthorizedException()

        return res.ok

    def get_network_block_count(self):
        info = btc_rpc_request(address=self.ip_with_credentials,
                               method='getblockchaininfo').json()

        return info['result']['headers']

    @staticmethod
    def from_ips(ips) -> list:
        btc_nodes = []

        for index, btc_address in enumerate(ips):
            btc_nodes.append(BitcoinNode(btc_address))

        return btc_nodes


class EthereumNode(Node):
    max_time_for_block_height_increase_in_seconds = 60 * 2  # 2 mins
    network_name = "Ethereum"

    def __init__(self, node_ip):
        super().__init__(node_ip, self.network_name, "ETH")

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

    def get_network_block_count(self):
        syncing = eth_rpc_request(ip=self.node_ip, method="eth_syncing").json()['result']

        if not syncing:
            return self.get_block_height()
        else:
            return int(syncing['highestBlock'], 16)


class BinanceNode(Node):
    network_name = "Binance"

    def __init__(self, node_ip):
        super().__init__(node_ip, self.network_name, "BNB")

    def is_fully_synced(self) -> bool:
        return not is_binance_node_syncing(self.node_ip)

    def get_block_height(self):
        return get_binance_node_block_height(self.node_ip)

    def is_healthy(self) -> bool:
        return is_binance_node_healthy(self.node_ip)

    @staticmethod
    def from_ips(ips) -> list:
        return list(map(lambda n: BinanceNode(n), ips))

    def get_network_block_count(self):
        return get_binance_block_count()


class UnauthorizedException(Exception):
    pass

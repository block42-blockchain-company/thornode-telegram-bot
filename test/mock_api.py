import http.server
import socketserver
from threading import Thread

MIDGARD_SERVER_PORT = 8080
RPC_SERVER_PORT = 26657


class RpcHttpServerHandler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        endpoint = self.path.rstrip('/').split('?')[0]
        if endpoint == '/status':
            self.path = 'mock_files/status.json'
        elif endpoint == '/num_unconfirmed_txs':
            self.path = 'mock_files/unconfirmed_txs.json'
        elif endpoint == '/health':
            self.path = 'mock_files/binance_health.json'
        else:
            self.path = 'mock_files' + endpoint
        return http.server.SimpleHTTPRequestHandler.do_GET(self)

    def log_message(self, format, *args):
        pass


class MidgardHttpServerHandler(http.server.SimpleHTTPRequestHandler):
    pool_addresses_counter = 0

    # Midgard queries had to be with "?height=0" at the end of the endpoint.
    # That's why we remove http arguments
    def do_GET(self):
        endpoint = self.path.rstrip('/').split('?')[0]
        if '/v1/health' == endpoint:
            self.path = 'mock_files/midgard.json'
        elif '/v1/network' == endpoint:
            self.path = 'mock_files/network.json'
        elif '/v1/thorchain/constants' == endpoint:
            self.path = 'mock_files/thorchain_constants.json'
        elif '/v1/thorchain/pool_addresses' == endpoint:
            MidgardHttpServerHandler.pool_addresses_counter += 1
            self.path = 'mock_files/pool_addresses_' + str(
                MidgardHttpServerHandler.pool_addresses_counter % 3 + 1) + '.json'
        elif '/v1/thorchain/lastblock' == endpoint:
            self.path = 'mock_files/lastblock.json'
        else:
            self.path = 'mock_files' + endpoint
        return http.server.SimpleHTTPRequestHandler.do_GET(self)

    def log_message(self, format, *args):
        pass


def main():
    socketserver.TCPServer.allow_reuse_address = True
    midgard_process = Thread(
        target=socketserver.TCPServer(("", MIDGARD_SERVER_PORT), MidgardHttpServerHandler).serve_forever)
    midgard_process.daemon = True
    midgard_process.start()
    print('Midgard mock server is running on localhost:' + str(MIDGARD_SERVER_PORT))

    rpc_process = Thread(target=socketserver.TCPServer(("", RPC_SERVER_PORT), RpcHttpServerHandler).serve_forever)
    rpc_process.daemon = True
    rpc_process.start()
    print('RPC mock server is running on localhost:' + str(RPC_SERVER_PORT))

    while True:
        pass


if __name__ == '__main__':
    main()

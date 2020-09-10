import http.server
import socketserver
from threading import Thread

MIDGARD_SERVER_PORT = 8080
RPC_SERVER_PORT = 26657


class RpcHttpServerHandler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        endpoint = self.path.rstrip('/')
        if endpoint == '/status':
            self.path = 'mock_files/status.json'
        elif endpoint == '/num_unconfirmed_txs':
            self.path = 'mock_files/unconfirmed_txs.json'
        elif endpoint == '/health':
            self.path = 'mock_files/binance_health.json'
        else:
            self.path = 'mock_files' + endpoint
        return http.server.SimpleHTTPRequestHandler.do_GET(self)


class MidgardHttpServerHandler(http.server.SimpleHTTPRequestHandler):
    pool_addresses_counter = 0

    def do_GET(self):
        endpoint = self.path.rstrip('/')
        if endpoint == '/v1/health':
            self.path = 'mock_files/midgard.json'
        elif endpoint == '/v1/network':
            self.path = 'mock_files/network.json'
        elif endpoint == '/v1/thorchain/constants':
            self.path = 'mock_files/thorchain_constants.json'
        elif endpoint == '/v1/thorchain/pool_addresses':
            MidgardHttpServerHandler.pool_addresses_counter += 1
            self.path = 'mock_files/pool_addresses_' + str(MidgardHttpServerHandler.pool_addresses_counter % 3 + 1) + '.json'
        else:
            self.path = 'mock_files' + endpoint
        return http.server.SimpleHTTPRequestHandler.do_GET(self)


def main():
    midgard_process = Thread(target=socketserver.TCPServer(("", MIDGARD_SERVER_PORT), MidgardHttpServerHandler).serve_forever)
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

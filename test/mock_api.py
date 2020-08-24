import http.server
import socketserver
from threading import Thread

MIDGARD_SERVER_PORT = 8080
RPC_SERVER_PORT = 26657


class RpcHttpServerHandler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        endpoint = self.path.rstrip('/')
        if endpoint == '/status':
            self.path = 'status.json'
        elif endpoint == '/num_unconfirmed_txs':
            self.path = 'unconfirmed_txs.json'
        elif endpoint == '/health':
            self.path = 'binance_health.json'
        return http.server.SimpleHTTPRequestHandler.do_GET(self)


class MidgardHttpServerHandler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        if self.path.rstrip('/') == '/v1/health':
            self.path = 'midgard.json'
        return http.server.SimpleHTTPRequestHandler.do_GET(self)


def main():
    Thread(target=socketserver.TCPServer(("", MIDGARD_SERVER_PORT), MidgardHttpServerHandler).serve_forever).start()
    print('Midgard mock server is running on localhost:' + str(MIDGARD_SERVER_PORT))

    Thread(target=socketserver.TCPServer(("", RPC_SERVER_PORT), RpcHttpServerHandler).serve_forever).start()
    print('RPC mock server is running on localhost:' + str(RPC_SERVER_PORT))


if __name__ == '__main__':
    main()

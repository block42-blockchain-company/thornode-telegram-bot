import requests
from requests.adapters import HTTPAdapter
from urllib3 import Retry

from constants.globals import CONNECTION_TIMEOUT


def get_request_json(url: str) -> dict:
    response = requests.get(url=url, timeout=CONNECTION_TIMEOUT)
    return parse_response(response)


def get_request_json_with_retries(url: str) -> dict:
    response = requests_retry_session().get(url=url, timeout=CONNECTION_TIMEOUT)
    return parse_response(response)


def requests_retry_session(retries=6,
                           backoff_factor=1,
                           status_forcelist=(500, 502, 504),
                           session=None):
    """
    Creates a request session that has auto retry.
    Implementation by Adam @mcadm34
    https://gitlab.com/thorchain/devops/node-launcher/-/blob/master/telegram-bot/templates/configmap.yaml#L192-212
    """

    session = session or requests.Session()
    retry = Retry(total=retries,
                  read=retries,
                  connect=retries,
                  backoff_factor=backoff_factor,
                  status_forcelist=status_forcelist)

    adapter = HTTPAdapter(max_retries=retry)
    session.mount("http://", adapter)
    session.mount("https://", adapter)
    return session


def parse_response(response) -> dict:
    if response.status_code != 200:
        raise BadStatusException(response)

    return response.json()


def btc_rpc_request(address: str, method: str, params=None):
    return rpc_request(url=f'http://{address}', jsonrpc_version="1.0", method=method,
                       params=params)


def eth_rpc_request(ip: str, method: str, params=None):
    return rpc_request(url=f'http://{ip}:8545/', jsonrpc_version="2.0", method=method,
                       params=params)


def rpc_request(url: str, method: str, jsonrpc_version: str, params=None):
    if params is None:
        params = []
    json = {"jsonrpc": jsonrpc_version, "id": None, "method": method, "params": params}

    return requests.post(url, json=json)


class BadStatusException(Exception):

    def __init__(self, response: requests.Response):
        self.message = f"Error while network request.\n" \
                       f"Received status code: {str(response.status_code)}\n" \
                       f"Received response: {response.text}"

    def __str__(self):
        return self.message

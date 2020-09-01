from attr import dataclass


@dataclass
class Node:
    address: str
    last_saved_version: str


class LocalStorageService:
    def __init__(self, context):
        self.context = context
        user_data = self.context.job.context['user_data']
        if 'version' not in user_data:
            user_data['versions'] = []

    def has_changed_version(self, node_address: str, current_version: str) -> bool:
        user_data = self.context.job.context['user_data']



        try:
            node_data = user_data['version'][nodes][node_address]
        except KeyError:
            node_data = user_data['nodes'][node_address] = {}

        if 'version' not in node_data:
            node_data['version'] = current_version

        return node_data['version'] != current_version

    def get_saved_version(self, node_address: str) -> str:
        return self.context.job.context['user_data']['nodes'][node_address]['version']

    def save_new_version(self, node_address: str, current_version: str):
        if node_address not in self.context.job.context['user_data']['nodes']:
            self.context.job.context['user_data']['nodes'][node_address] = {}

        self.context.job.context['user_data']['nodes'][node_address]['version'] = current_version

class LocalStorageService:
    def __init__(self, context):
        self.context = context

        user_data = self.context.job.context['user_data']
        if 'versions' not in user_data:
            user_data['versions'] = {}

    def has_changed_version(self, node_address: str, current_version: str) -> bool:
        versions = self.context.job.context['user_data']['versions']

        try:
            node_data = versions[node_address]
        except KeyError:
            node_data = versions[node_address] = current_version

        return node_data != current_version

    def get_saved_version(self, node_address: str) -> str:
        return self.context.job.context['user_data']['versions'][node_address]

    def save_new_version(self, node_address: str, current_version: str):
        self.context.job.context['user_data']['versions'][node_address] = current_version

class LocalStorageService:
    def __init__(self, context):
        self.context = context

    def has_changed_version(self, node_address: str, current_version: str) -> bool:
        user_data = self.context.job.context['user_data']
        if user_data['nodes'][node_address]['version'] is None:
            user_data['nodes'][node_address]['version'] = current_version

        return user_data['nodes'][node_address]['version'] != current_version

    def get_saved_version(self, node_address: str) -> str:
        return self.context.job.context['user_data']['nodes'][node_address]['version']

    def save_new_version(self, node_address: str, current_version: str):
        if node_address not in self.context.job.context['user_data']['nodes']:
            self.context.job.context['user_data']['nodes'][node_address] = {}

        self.context.job.context['user_data']['nodes'][node_address]['version'] = current_version

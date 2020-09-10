from typing import Optional


class LocalStorageService:
    def __init__(self, context):
        self.context = context

    def get_last_newest_software_version(self) -> Optional[str]:
        return self.context.job.context['user_data'].get('newest_software_version', None)

    def get_my_nodes(self):
        return self.context.job.context['user_data']['nodes']

    def save_newer_version(self, version: str):
        self.context.job.context['user_data']['newest_software_version'] = version

    def get_node_statuses(self):
        if 'node_statuses' not in self.context.job.context['user_data']:
            self.context.job.context['user_data']['node_statuses'] = {}
        return self.context.job.context['user_data']['node_statuses']

    def set_node_statuses(self, validators):
        for validator in validators:
            self.context.job.context['user_data']['node_statuses'][validator['node_address']] = validator['status']
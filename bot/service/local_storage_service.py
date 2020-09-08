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
        return self.context.job.context['user_data']['node_statuses']
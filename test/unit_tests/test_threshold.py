import copy
import unittest

from constants.globals import SLASH_POINTS_NOTIFICATION_THRESHOLD_DEFAULT
from handlers.settings_handlers import set_slash_points_threshold
from jobs.thornodes_jobs import build_notification_message_for_active_node
from service.utils import get_slash_points_threshold
from test.unit_tests.helpers import ContextMock, node_mock, JobContextMock


class ThresholdTest(unittest.TestCase):

    def test_setting_threshold(self):
        context = ContextMock()
        self.assertNotIn("settings", context.bot_data)

        value = get_slash_points_threshold(context)
        self.assertIn("settings", context.bot_data)
        self.assertEqual(value, SLASH_POINTS_NOTIFICATION_THRESHOLD_DEFAULT)

        new_val = 0
        set_slash_points_threshold(new_val=new_val, context=context)
        value = get_slash_points_threshold(context)
        self.assertEqual(value, new_val)

        with self.assertRaises(Exception):
            set_slash_points_threshold(new_val=-1, context=context)
        with self.assertRaises(Exception):
            set_slash_points_threshold(new_val="block42", context=context)

    def test_slash_points_notification(self):
        context = JobContextMock()
        local_node = copy.deepcopy(node_mock)
        remote_node = copy.deepcopy(node_mock)

        message = build_notification_message_for_active_node(local_node, remote_node, context)
        self.assertIsNone(message)

        slash_points_change = SLASH_POINTS_NOTIFICATION_THRESHOLD_DEFAULT + 1
        old_slash_points = int(remote_node['slash_points'])
        remote_node['slash_points'] = str(old_slash_points + slash_points_change)

        message = build_notification_message_for_active_node(local_node, remote_node, context)
        self.assertIn(f"Slash Points: {old_slash_points} ➡️ {remote_node['slash_points']}", message)

        local_node = copy.deepcopy(remote_node)
        new_threshold = 5
        set_slash_points_threshold(new_threshold, context)
        remote_node['slash_points'] = str(int(remote_node['slash_points']) + new_threshold)
        message = build_notification_message_for_active_node(local_node, remote_node, context)
        self.assertIsNone(message)

        local_node = copy.deepcopy(remote_node)
        new_threshold = 5
        set_slash_points_threshold(new_threshold, context)
        old_slash_points = int(remote_node['slash_points'])
        remote_node['slash_points'] = str(old_slash_points + new_threshold + 1)
        message = build_notification_message_for_active_node(local_node, remote_node, context)
        self.assertIn(f"Slash Points: {old_slash_points} ➡️ {remote_node['slash_points']}", message)

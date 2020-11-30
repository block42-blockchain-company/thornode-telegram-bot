import unittest
from datetime import timedelta

from service.utils import format_to_days_and_hours


class UnitTests(unittest.TestCase):

    def test_days_formatter(self):
        self.assertEqual(format_to_days_and_hours(timedelta(days=-1)), '< 1 hour')
        self.assertEqual(format_to_days_and_hours(timedelta(days=0)), '< 1 hour')
        self.assertEqual(format_to_days_and_hours(timedelta(days=1 / 24)), '1 hour')
        self.assertEqual(format_to_days_and_hours(timedelta(days=2 / 24)), '2 hours')
        self.assertEqual(format_to_days_and_hours(timedelta(days=6 / 24)), '6 hours')
        self.assertEqual(format_to_days_and_hours(timedelta(days=1)), '1 day')
        self.assertEqual(format_to_days_and_hours(timedelta(days=69)), '69 days')
        self.assertEqual(format_to_days_and_hours(timedelta(days=1 + 12 / 24)), '1 day 12 hours')
        self.assertEqual(format_to_days_and_hours(timedelta(days=1 + 1 / 24)), '1 day 1 hour')

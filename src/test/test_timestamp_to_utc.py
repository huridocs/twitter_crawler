from datetime import datetime, timedelta, timezone
from unittest import TestCase

from timestamp_to_recent_utc import timestamp_to_recent_utc


class TestTimestampToRecentUtc(TestCase):
    def test_timestamp_to_utc(self):
        now = datetime.now()
        utc_time = timestamp_to_recent_utc(int(now.timestamp()))

        self.assertEqual(utc_time[-5:], '00:00')
        self.assertEqual(int(utc_time[:4]), now.year)
        self.assertEqual(int(utc_time[5:7]), now.month)
        self.assertEqual(int(utc_time[8:10]), now.day)

    def test_avoid_dates_older_than_7_days(self):
        old_date = datetime.now(tz=timezone.utc) - timedelta(days=8)
        utc_time = timestamp_to_recent_utc(int(old_date.timestamp()))

        start_valid_date = (datetime.now(tz=timezone.utc) - timedelta(days=7)).replace(tzinfo=timezone.utc)
        self.assertTrue(start_valid_date < datetime.fromisoformat(utc_time))

    def test_avoid_dates_newer_than_10_seconds(self):
        too_recent_date = datetime.now(tz=timezone.utc)
        utc_time = timestamp_to_recent_utc(int(too_recent_date.timestamp()))

        end_valid_date = (datetime.now(tz=timezone.utc) - timedelta(seconds=30)).replace(tzinfo=timezone.utc)
        self.assertTrue(datetime.fromisoformat(utc_time) < end_valid_date)
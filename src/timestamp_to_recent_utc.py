from datetime import datetime, timezone, timedelta


def timestamp_to_recent_utc(timestamp: int):
    utc_time = datetime.fromtimestamp(timestamp).replace(tzinfo=timezone.utc)
    start_valid_date = (datetime.now(tz=timezone.utc) - timedelta(days=7) + timedelta(hours=8)).replace(tzinfo=timezone.utc)

    if utc_time < start_valid_date:
        return start_valid_date.isoformat()

    end_valid_date = (datetime.now(tz=timezone.utc) - timedelta(seconds=60)).replace(tzinfo=timezone.utc)

    if end_valid_date < utc_time:
        return end_valid_date.isoformat()

    return utc_time.isoformat()
"""
datetime.py
"""

from datetime import datetime
import pytz


class DateTime:
    """date time utils"""

    def to_local(self, utc: str) -> str:
        """convert to local date time"""
        utc_time = datetime.strptime(utc, "%Y-%m-%dT%H:%M:%S.%fZ")
        utc_time = pytz.utc.localize(utc_time)
        local_timezone = pytz.timezone(pytz.country_timezones('US')[0])
        local_time = utc_time.astimezone(local_timezone)
        return local_time.strftime('%d-%B-%Y %I:%M %p')

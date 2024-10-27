from datetime import datetime
from datetime import timedelta
from typing import Optional

import pytz
# Define the date string

def convert_string_to_date(date_string: str,
                           /,
                           *,
                           date_format:str = None,
                           ) -> datetime:
    if not date_format:
        date_format = "%a, %d %b %Y %H:%M:%S %z"

    return datetime.strptime(date_string, date_format)


def convert_to_utc_naive(a: Optional[datetime],
                         /) -> Optional[datetime]:
    """
    This function checks if the datetime has a timezone configured.
    If it has, it converted to UTC timezone and removes the tz info.

    :param a: datetime to check
    :return: a datetime that has no tz info
    """
    if a is None:
        return None

    if not a.tzinfo:
        return a

    return a.astimezone(pytz.UTC).replace(tzinfo=None)


def ensure_utc_aware(a: Optional[datetime],
                     /) -> Optional[datetime]:
    """
    This function checks if the datetime has a timezone configured.
    If it's not, it switches to UTC.

    :param a: datetime to check
    :return: a datetime that has tz info
    """
    if a is None:
        return None

    if a.tzinfo:
        return a

    return a.replace(tzinfo=pytz.UTC)


def compare(a: datetime,
            b: datetime,
            /) -> int:
    a = convert_to_utc_naive(a)
    b = convert_to_utc_naive(b)

    if a < b:
        return -1

    if a > b:
        return 1

    return 0


def was_recently_updated(t: Optional[datetime],
                         threshold: timedelta,
                         /) -> bool:
    """
    Checks to see if a timestamp is within a certain timeframe.
    A value of None is considered outside the valid range.

    :param t: the timestamp to check
    :param threshold: how old the timestamp can be
    :return: True if the timestamp was updated in the expected timeframe
    """
    if t is None:
        return False

    t = convert_to_utc_naive(t)

    now = datetime.now()
    return t > now - threshold




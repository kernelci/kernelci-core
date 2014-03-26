# UTC implementation borrowed from the Python docs:
# http://docs.python.org/2/library/datetime.html#tzinfo-objects
# License is the same as the example one.

from datetime import (
    timedelta,
    tzinfo,
)

ZERO = timedelta(0)


class UTC(tzinfo):
    """UTC"""

    def utcoffset(self, dt):
        return ZERO

    def tzname(self, dt):
        return "UTC"

    def dst(self, dt):
        return ZERO

utc = UTC()

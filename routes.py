from datetime import datetime as dt
from datetime import timezone

date = (2024, 9, 10)
tz = timezone.utc
routes = [
    ("complete route", dt(*date, 6, 30, tzinfo=tz), dt(*date, 7, 44, tzinfo=tz)),
    ("RPM control", dt(*date, 6, 40, tzinfo=tz), dt(*date, 6, 57, tzinfo=tz)),
    ("load control", dt(*date, 6, 57, 35, tzinfo=tz), dt(*date, 7, 5, 45, tzinfo=tz)),
    ("idle", dt(*date, 7, 22, tzinfo=tz), dt(*date, 7, 36, tzinfo=tz)),
]

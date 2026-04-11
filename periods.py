from __future__ import annotations

from datetime import datetime, time, timedelta

from .config import PeriodKey
from .models import PeriodRange


def current_period(period: PeriodKey, now: datetime) -> PeriodRange:
    if period == "weekly":
        start_date = now.date() - timedelta(days=now.weekday())
        end_date = start_date + timedelta(days=7)
        label = "This week"
    elif period == "monthly":
        start_date = now.date().replace(day=1)
        if start_date.month == 12:
            end_date = start_date.replace(year=start_date.year + 1, month=1)
        else:
            end_date = start_date.replace(month=start_date.month + 1)
        label = "This month"
    else:
        start_date = now.date().replace(month=1, day=1)
        end_date = start_date.replace(year=start_date.year + 1)
        label = "This year"

    tzinfo = now.tzinfo
    start = datetime.combine(start_date, time.min, tzinfo=tzinfo)
    end = datetime.combine(end_date, time.min, tzinfo=tzinfo)
    return PeriodRange(key=period, label=label, start=start, end=end)

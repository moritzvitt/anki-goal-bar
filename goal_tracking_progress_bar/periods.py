from __future__ import annotations

from datetime import date, datetime, time, timedelta

from .config import GoalDefinition
from .models import PeriodRange


def current_period(goal: GoalDefinition, now: datetime) -> PeriodRange:
    if goal.period == "weekly":
        start_date = now.date() - timedelta(days=now.weekday())
        end_date = start_date + timedelta(days=7)
        label = "This week"
    elif goal.period == "monthly":
        start_date = now.date().replace(day=1)
        if start_date.month == 12:
            end_date = start_date.replace(year=start_date.year + 1, month=1)
        else:
            end_date = start_date.replace(month=start_date.month + 1)
        label = "This month"
    elif goal.period == "custom":
        start_date = _safe_date(goal.start_year, goal.start_month, goal.start_day)
        end_date = start_date + timedelta(days=max(1, goal.duration_days))
        label = f"{start_date.strftime('%d %b %Y')} - {(end_date - timedelta(days=1)).strftime('%d %b %Y')}"
    else:
        start_date, end_date = _current_year_window(now.date(), goal.start_month, goal.start_day)
        label = "This year"

    tzinfo = now.tzinfo
    start = datetime.combine(start_date, time.min, tzinfo=tzinfo)
    end = datetime.combine(end_date, time.min, tzinfo=tzinfo)
    return PeriodRange(key=goal.period, label=label, start=start, end=end)


def elapsed_ratio(period: PeriodRange, now: datetime) -> float:
    if period.key in {"weekly", "monthly"}:
        total_days = (period.end.date() - period.start.date()).days
        if total_days <= 0:
            return 0.0
        current_day = min(max(now.date(), period.start.date()), period.end.date())
        elapsed_days = (current_day - period.start.date()).days
        return min(1.0, max(0.0, elapsed_days / total_days))

    total = (period.end - period.start).total_seconds()
    if total <= 0:
        return 0.0
    elapsed = (min(max(now, period.start), period.end) - period.start).total_seconds()
    return min(1.0, max(0.0, elapsed / total))


def milestone_datetime(period: PeriodRange, ratio: float) -> datetime:
    clamped_ratio = min(1.0, max(0.0, ratio))
    total = period.end - period.start
    return period.start + total * clamped_ratio


def _current_year_window(today: date, start_month: int, start_day: int) -> tuple[date, date]:
    this_year_start = _safe_date(today.year, start_month, start_day)
    if today >= this_year_start:
        start = this_year_start
        end = _safe_date(today.year + 1, start_month, start_day)
    else:
        start = _safe_date(today.year - 1, start_month, start_day)
        end = this_year_start
    return start, end


def _safe_date(year: int, month: int, day: int) -> date:
    while True:
        try:
            return date(year, month, day)
        except ValueError:
            day -= 1

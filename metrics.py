from __future__ import annotations

from collections.abc import Iterable

from anki.collection import Collection

from .models import PeriodMetrics, PeriodRange


class GoalMetricsRepository:
    def __init__(self, col: Collection) -> None:
        self._col = col

    def load_metrics(self, periods: Iterable[PeriodRange]) -> dict[str, PeriodMetrics]:
        metrics_by_period: dict[str, PeriodMetrics] = {}
        for period in periods:
            reviews, total_ms = self._col.db.first(
                """
                SELECT COUNT(*), COALESCE(SUM(time), 0)
                FROM revlog
                WHERE id >= ? AND id < ?
                """,
                period.start_ms,
                period.end_ms,
            )
            new_cards = self._col.db.scalar(
                """
                SELECT COUNT(*)
                FROM (
                    SELECT cid
                    FROM revlog
                    GROUP BY cid
                    HAVING MIN(id) >= ? AND MIN(id) < ?
                )
                """,
                period.start_ms,
                period.end_ms,
            )

            metrics_by_period[period.key] = PeriodMetrics(
                reviews=int(reviews or 0),
                new_cards=int(new_cards or 0),
                study_minutes=int(round((total_ms or 0) / 60000)),
            )

        return metrics_by_period

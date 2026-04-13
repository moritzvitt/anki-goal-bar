from __future__ import annotations

from collections.abc import Iterable, Sequence

from anki.collection import Collection

from .models import PeriodMetrics, PeriodRange


class GoalMetricsRepository:
    def __init__(self, col: Collection) -> None:
        self._col = col

    def load_metrics(
        self,
        deck_ids: Sequence[int],
        periods: Iterable[PeriodRange],
    ) -> dict[str, PeriodMetrics]:
        clause, params = _deck_clause(deck_ids)
        if not clause:
            return {}

        metrics_by_period: dict[str, PeriodMetrics] = {}
        for period in periods:
            metrics_by_period[period.key] = self.load_period_metrics(deck_ids, period)

        return metrics_by_period

    def load_period_metrics(self, deck_ids: Sequence[int], period: PeriodRange) -> PeriodMetrics:
        clause, params = _deck_clause(deck_ids)
        if not clause:
            return PeriodMetrics(reviews=0, new_cards=0, study_minutes=0)

        reviews, total_ms = self._col.db.first(
            f"""
            SELECT COUNT(*), COALESCE(SUM(time), 0)
            FROM revlog
            WHERE cid IN (
                SELECT id
                FROM cards
                WHERE {clause}
            )
            AND id >= ? AND id < ?
            """,
            *params,
            period.start_ms,
            period.end_ms,
        )
        new_cards = self._col.db.scalar(
            f"""
            SELECT COUNT(*)
            FROM (
                SELECT cid
                FROM revlog
                WHERE cid IN (
                    SELECT id
                    FROM cards
                    WHERE {clause}
                )
                GROUP BY cid
                HAVING MIN(id) >= ? AND MIN(id) < ?
            )
            """,
            *params,
            period.start_ms,
            period.end_ms,
        )

        return PeriodMetrics(
            reviews=int(reviews or 0),
            new_cards=int(new_cards or 0),
            study_minutes=int(round((total_ms or 0) / 60000)),
        )


def _deck_clause(deck_ids: Sequence[int]) -> tuple[str, list[int]]:
    unique_ids: list[int] = []
    for deck_id in dict.fromkeys(deck_ids):
        try:
            unique_ids.append(int(deck_id))
        except (TypeError, ValueError):
            continue
    if not unique_ids:
        return "", []

    placeholders = ", ".join("?" for _ in unique_ids)
    return f"did IN ({placeholders})", unique_ids

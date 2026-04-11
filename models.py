from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from .config import GoalDefinition, LayoutMode, MetricType, PeriodKey


@dataclass(frozen=True)
class PeriodRange:
    key: PeriodKey
    label: str
    start: datetime
    end: datetime

    @property
    def start_ms(self) -> int:
        return int(self.start.timestamp() * 1000)

    @property
    def end_ms(self) -> int:
        return int(self.end.timestamp() * 1000)


@dataclass(frozen=True)
class PeriodMetrics:
    reviews: int
    new_cards: int
    study_minutes: int

    def value_for(self, metric: MetricType) -> int:
        return getattr(self, metric)


@dataclass(frozen=True)
class GoalProgress:
    goal: GoalDefinition
    label: str
    metric_label: str
    current: int
    target: int
    percent: int

    @property
    def ratio(self) -> float:
        if self.target <= 0:
            return 0.0
        return min(1.0, self.current / self.target)


@dataclass(frozen=True)
class DeckProgress:
    deck_id: int
    deck_name: str
    goals: tuple[GoalProgress, ...]


@dataclass(frozen=True)
class RenderPayload:
    layout_mode: LayoutMode
    decks: tuple[DeckProgress, ...]

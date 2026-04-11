from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Callable

from aqt.main import AnkiQt

from .config import AddonConfig, config_signature
from .metrics import GoalMetricsRepository
from .models import GoalProgress
from .periods import current_period
from .render import metric_label, render_widget


@dataclass(frozen=True)
class _CacheEntry:
    html: str
    col_mod: int
    local_day: str
    config_key: tuple[tuple[str, bool, str, int], ...]


class GoalProgressService:
    def __init__(self, main_window: AnkiQt, config_loader: Callable[[], AddonConfig]) -> None:
        self._mw = main_window
        self._config_loader = config_loader
        self._cache: _CacheEntry | None = None

    def render_widget(self) -> str:
        config = self._config_loader()
        now = datetime.now().astimezone()
        config_key = config_signature(config)

        if self._cache and self._cache_still_valid(now, config_key):
            return self._cache.html

        html = render_widget(self._build_goal_progress(config, now))
        self._cache = _CacheEntry(
            html=html,
            col_mod=self._mw.col.mod,
            local_day=now.date().isoformat(),
            config_key=config_key,
        )
        return html

    def _build_goal_progress(self, config: AddonConfig, now: datetime) -> list[GoalProgress]:
        active_goals = config.active_goals
        if not active_goals:
            return []

        periods = {goal.period: current_period(goal.period, now) for goal in active_goals}
        metrics = GoalMetricsRepository(self._mw.col).load_metrics(periods.values())

        progress_items: list[GoalProgress] = []
        for goal in active_goals:
            period = periods[goal.period]
            current = metrics[goal.period].value_for(goal.metric)
            percent = min(999, int((current / goal.target) * 100)) if goal.target > 0 else 0
            progress_items.append(
                GoalProgress(
                    goal=goal,
                    label=period.label,
                    metric_label=metric_label(goal.metric),
                    current=current,
                    target=goal.target,
                    percent=percent,
                )
            )
        return progress_items

    def _cache_still_valid(
        self,
        now: datetime,
        config_key: tuple[tuple[str, bool, str, int], ...],
    ) -> bool:
        return (
            self._cache is not None
            and self._cache.col_mod == self._mw.col.mod
            and self._cache.local_day == now.date().isoformat()
            and self._cache.config_key == config_key
        )

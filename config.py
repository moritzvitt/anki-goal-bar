from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

from aqt import mw

MetricType = Literal["reviews", "new_cards", "study_minutes"]
PeriodKey = Literal["weekly", "monthly", "yearly"]

DEFAULT_CONFIG = {
    "weekly": {"enabled": True, "metric": "reviews", "target": 400},
    "monthly": {"enabled": False, "metric": "study_minutes", "target": 120},
    "yearly": {"enabled": False, "metric": "new_cards", "target": 2000},
}

VALID_METRICS = {"reviews", "new_cards", "study_minutes"}
PERIODS: tuple[PeriodKey, ...] = ("weekly", "monthly", "yearly")


@dataclass(frozen=True)
class GoalDefinition:
    period: PeriodKey
    enabled: bool
    metric: MetricType
    target: int

    @property
    def is_active(self) -> bool:
        return self.enabled and self.target > 0


@dataclass(frozen=True)
class AddonConfig:
    goals: tuple[GoalDefinition, ...]

    @property
    def active_goals(self) -> tuple[GoalDefinition, ...]:
        return tuple(goal for goal in self.goals if goal.is_active)


def load_config() -> AddonConfig:
    addon_name = __name__.split(".", 1)[0]
    raw = mw.addonManager.getConfig(addon_name) or {}
    return AddonConfig(
        goals=tuple(_goal_from_raw(period, raw.get(period, {})) for period in PERIODS)
    )


def config_signature(config: AddonConfig) -> tuple[tuple[str, bool, str, int], ...]:
    return tuple((goal.period, goal.enabled, goal.metric, goal.target) for goal in config.goals)


def _goal_from_raw(period: PeriodKey, raw_goal: dict) -> GoalDefinition:
    defaults = DEFAULT_CONFIG[period]
    metric = raw_goal.get("metric", defaults["metric"])
    if metric not in VALID_METRICS:
        metric = defaults["metric"]

    target = raw_goal.get("target", defaults["target"])
    try:
        target_int = max(0, int(target))
    except (TypeError, ValueError):
        target_int = defaults["target"]

    return GoalDefinition(
        period=period,
        enabled=bool(raw_goal.get("enabled", defaults["enabled"])),
        metric=metric,  # type: ignore[arg-type]
        target=target_int,
    )

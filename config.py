from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from typing import Literal

from aqt import mw

MetricType = Literal["reviews", "new_cards", "study_minutes"]
PeriodKey = Literal["weekly", "monthly", "yearly"]
LayoutMode = Literal["all", "carousel"]

PERIODS: tuple[PeriodKey, ...] = ("weekly", "monthly", "yearly")
VALID_METRICS = {"reviews", "new_cards", "study_minutes"}
VALID_LAYOUTS = {"all", "carousel"}

DEFAULT_GOALS = {
    "weekly": {"enabled": True, "metric": "reviews", "target": 400},
    "monthly": {"enabled": False, "metric": "study_minutes", "target": 120},
    "yearly": {
        "enabled": False,
        "metric": "new_cards",
        "target": 2000,
        "start_month": 1,
        "start_day": 1,
    },
}

DEFAULT_DECK_ENTRY = {
    "deck_id": None,
    "deck_name": "",
    "weekly": DEFAULT_GOALS["weekly"],
    "monthly": DEFAULT_GOALS["monthly"],
    "yearly": DEFAULT_GOALS["yearly"],
}

DEFAULT_CONFIG = {
    "layout": {"mode": "all", "show_behind_pace": False},
    "decks": [],
}


@dataclass(frozen=True)
class GoalDefinition:
    period: PeriodKey
    enabled: bool
    metric: MetricType
    target: int
    start_month: int = 1
    start_day: int = 1

    @property
    def is_active(self) -> bool:
        return self.enabled and self.target > 0


@dataclass(frozen=True)
class DeckGoalDefinition:
    deck_id: int | None
    deck_name: str
    goals: tuple[GoalDefinition, ...]

    @property
    def active_goals(self) -> tuple[GoalDefinition, ...]:
        return tuple(goal for goal in self.goals if goal.is_active)


@dataclass(frozen=True)
class AddonConfig:
    layout_mode: LayoutMode
    show_behind_pace: bool
    decks: tuple[DeckGoalDefinition, ...]

    @property
    def active_decks(self) -> tuple[DeckGoalDefinition, ...]:
        return tuple(deck for deck in self.decks if deck.active_goals and deck.deck_id is not None)


def load_config() -> AddonConfig:
    addon_name = __name__.split(".", 1)[0]
    raw = mw.addonManager.getConfig(addon_name) or {}
    normalized = _normalize_raw_config(raw)

    layout_mode = normalized.get("layout", {}).get("mode", DEFAULT_CONFIG["layout"]["mode"])
    if layout_mode not in VALID_LAYOUTS:
        layout_mode = DEFAULT_CONFIG["layout"]["mode"]
    show_behind_pace = bool(
        normalized.get("layout", {}).get(
            "show_behind_pace",
            DEFAULT_CONFIG["layout"]["show_behind_pace"],
        )
    )

    decks = tuple(_deck_from_raw(raw_deck) for raw_deck in normalized.get("decks", []))
    return AddonConfig(
        layout_mode=layout_mode,
        show_behind_pace=show_behind_pace,
        decks=decks,
    )  # type: ignore[arg-type]


def config_signature(config: AddonConfig) -> tuple:
    return (
        config.layout_mode,
        config.show_behind_pace,
        tuple(
            (
                deck.deck_id,
                deck.deck_name,
                tuple(
                    (
                        goal.period,
                        goal.enabled,
                        goal.metric,
                        goal.target,
                        goal.start_month,
                        goal.start_day,
                    )
                    for goal in deck.goals
                ),
            )
            for deck in config.decks
        ),
    )


def export_config(config: AddonConfig) -> dict:
    return {
        "layout": {
            "mode": config.layout_mode,
            "show_behind_pace": config.show_behind_pace,
        },
        "decks": [_export_deck(deck) for deck in config.decks],
    }


def clamp_month_day(month: int, day: int) -> tuple[int, int]:
    month = min(12, max(1, int(month)))
    max_day = _days_in_month(month)
    day = min(max_day, max(1, int(day)))
    return month, day


def _normalize_raw_config(raw: dict) -> dict:
    if "decks" in raw or "layout" in raw:
        return raw

    if any(period in raw for period in PERIODS):
        current_deck = mw.col.decks.current() if mw and mw.col else None
        return {
            "layout": {"mode": "all"},
            "decks": [
                {
                    "deck_id": int(current_deck["id"]) if current_deck else None,
                    "deck_name": str(current_deck["name"]) if current_deck else "",
                    "weekly": raw.get("weekly", DEFAULT_GOALS["weekly"]),
                    "monthly": raw.get("monthly", DEFAULT_GOALS["monthly"]),
                    "yearly": raw.get("yearly", DEFAULT_GOALS["yearly"]),
                }
            ],
        }

    return DEFAULT_CONFIG


def _deck_from_raw(raw_deck: dict) -> DeckGoalDefinition:
    deck_id = raw_deck.get("deck_id")
    try:
        parsed_deck_id = int(deck_id) if deck_id is not None else None
    except (TypeError, ValueError):
        parsed_deck_id = None

    deck_name = str(raw_deck.get("deck_name", "") or "")
    goals = tuple(_goal_from_raw(period, raw_deck.get(period, {})) for period in PERIODS)
    return DeckGoalDefinition(deck_id=parsed_deck_id, deck_name=deck_name, goals=goals)


def _goal_from_raw(period: PeriodKey, raw_goal: dict) -> GoalDefinition:
    defaults = DEFAULT_GOALS[period]
    metric = raw_goal.get("metric", defaults["metric"])
    if metric not in VALID_METRICS:
        metric = defaults["metric"]

    target = raw_goal.get("target", defaults["target"])
    try:
        target_int = max(0, int(target))
    except (TypeError, ValueError):
        target_int = int(defaults["target"])

    start_month = raw_goal.get("start_month", defaults.get("start_month", 1))
    start_day = raw_goal.get("start_day", defaults.get("start_day", 1))
    start_month_int, start_day_int = clamp_month_day(start_month, start_day)

    return GoalDefinition(
        period=period,
        enabled=bool(raw_goal.get("enabled", defaults["enabled"])),
        metric=metric,  # type: ignore[arg-type]
        target=target_int,
        start_month=start_month_int,
        start_day=start_day_int,
    )


def _days_in_month(month: int) -> int:
    if month == 2:
        return 29
    if month in {4, 6, 9, 11}:
        return 30
    return 31


def _export_deck(deck: DeckGoalDefinition) -> dict:
    exported = {
        "deck_id": deck.deck_id,
        "deck_name": deck.deck_name,
    }
    for goal in deck.goals:
        payload = {
            "enabled": goal.enabled,
            "metric": goal.metric,
            "target": goal.target,
        }
        if goal.period == "yearly":
            payload["start_month"] = goal.start_month
            payload["start_day"] = goal.start_day
        exported[goal.period] = payload
    return exported

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

DEFAULT_REWARDS: dict[PeriodKey, tuple[str, ...]] = {
    "weekly": (
        "🍦 Have ice cream for no academically valid reason",
        "🥨 Buy the fancy pretzel, not the sensible snack",
        "🧦 Wear your lucky socks like a champion",
        "☕ Upgrade to an unnecessarily dramatic coffee",
        "🎮 Take a guilt-free gaming detour",
        "🍔 Order the burger with the chaotic extra topping",
        "🛋️ Declare a horizontal recovery session on the couch",
        "🎬 Watch one episode and pretend it is research",
        "🧋 Get a bubble tea with maximum pearl density",
        "📚 Visit a bookstore and judge covers professionally",
        "🍕 Claim two bonus slices in the name of progress",
        "🛒 Buy one tiny treat with big main-character energy",
        "🎧 Curate a victory playlist and strut around the room",
        "🍰 Eat cake on an ordinary day like royalty",
        "🕹️ Unlock an entire evening of unserious hobbies",
        "🚲 Take the scenic route purely for vibes",
        "🧖 Enjoy a deluxe bath or shower with spa delusions",
        "🎟️ Book a movie night and rate the popcorn harshly",
        "🛍️ Buy the absurdly specific thing from your wishlist",
        "🎉 Throw yourself a microscopic parade of triumph",
    ),
    "monthly": (
        "🍣 Go out for sushi and order one mysterious roll",
        "🪴 Adopt a plant and promise this one is different",
        "🧁 Visit a cafe and get the dessert with the least practical shape",
        "📦 Open a tiny gift to yourself like a celebrity unboxing",
        "🎳 Plan a wildly competitive bowling night",
        "🧩 Spend an evening with a puzzle and dramatic narration",
        "🕯️ Upgrade your room with a candle that sounds expensive",
        "🍜 Hunt down elite ramen and slurp with purpose",
        "🎨 Buy art supplies for your future renaissance phase",
        "🧥 Wear your best outfit to a completely ordinary errand",
        "🚆 Take a day trip and romanticize public transport",
        "🧀 Assemble an unnecessarily confident snack board",
        "📷 Do a mini photo walk like a mysterious traveler",
        "🎫 Book tickets for something fun before responsibility notices",
        "🍽️ Try the restaurant you've been talking about for ages",
        "🛏️ Reserve one majestic sleep-in morning with zero alarms",
        "🏨 Plan a tiny weekend escape with suspiciously plush pillows",
        "💆 Get a massage or invent a deluxe self-care day",
        "🎁 Buy the nice version instead of the responsible version",
        "✈️ Take yourself on a glorious mini vacation mission",
    ),
    "yearly": (
        "🎒 Take a proud day off and disappear into a museum",
        "🚄 Ride a fast train somewhere just because you can",
        "🎢 Visit a theme park and scream out the stress",
        "🍾 Host a ridiculous celebration dinner for your own honor",
        "🏕️ Escape for a cabin weekend with dramatic hot chocolate",
        "🎭 See a live show and clap like you financed it",
        "🏖️ Book a beach getaway and become a lounge chair icon",
        "🗺️ Take a city break with an overambitious food map",
        "🚢 Go on a boat and wave like minor nobility",
        "🎿 Plan a winter trip and fall down in scenic locations",
        "🏰 Stay somewhere old enough to have ghost rumors",
        "🌋 Visit a landscape that looks suspiciously fictional",
        "🛫 Take an international trip and order breakfast in another language",
        "🗽 Do a big-city adventure with maximal tourist confidence",
        "🦒 Go on a safari or wildlife trip and narrate like a documentary",
        "🚁 Book one absurdly dramatic activity with a helmet waiver",
        "🛎️ Stay at a hotel where the robe feels too powerful",
        "🌌 Chase a bucket-list view and take smug photos",
        "💎 Plan a luxury escape that makes your inbox jealous",
        "🇯🇵 Holiday in Japan and live your final-form montage",
    ),
}

DEFAULT_GOALS = {
    "weekly": {
        "enabled": True,
        "metric": "reviews",
        "target": 400,
        "rewards": list(DEFAULT_REWARDS["weekly"]),
    },
    "monthly": {
        "enabled": False,
        "metric": "study_minutes",
        "target": 120,
        "rewards": list(DEFAULT_REWARDS["monthly"]),
    },
    "yearly": {
        "enabled": False,
        "metric": "new_cards",
        "target": 2000,
        "start_month": 1,
        "start_day": 1,
        "rewards": list(DEFAULT_REWARDS["yearly"]),
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
    "layout": {"mode": "all", "show_behind_pace": False, "show_rewards": True},
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
    rewards: tuple[str, ...] = ()
    show_reward: bool = True

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
    show_rewards: bool
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
    show_rewards = bool(
        normalized.get("layout", {}).get(
            "show_rewards",
            DEFAULT_CONFIG["layout"]["show_rewards"],
        )
    )

    decks = tuple(_deck_from_raw(raw_deck) for raw_deck in normalized.get("decks", []))
    return AddonConfig(
        layout_mode=layout_mode,
        show_behind_pace=show_behind_pace,
        show_rewards=show_rewards,
        decks=decks,
    )  # type: ignore[arg-type]


def config_signature(config: AddonConfig) -> tuple:
    return (
        config.layout_mode,
        config.show_behind_pace,
        config.show_rewards,
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
                        goal.rewards,
                        goal.show_reward,
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
            "show_rewards": config.show_rewards,
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
            "layout": {"mode": "all", "show_rewards": True},
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
    rewards = _normalize_rewards(period, raw_goal.get("rewards"))

    return GoalDefinition(
        period=period,
        enabled=bool(raw_goal.get("enabled", defaults["enabled"])),
        metric=metric,  # type: ignore[arg-type]
        target=target_int,
        start_month=start_month_int,
        start_day=start_day_int,
        rewards=rewards,
        show_reward=bool(raw_goal.get("show_reward", True)),
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
            "rewards": list(goal.rewards),
            "show_reward": goal.show_reward,
        }
        if goal.period == "yearly":
            payload["start_month"] = goal.start_month
            payload["start_day"] = goal.start_day
        exported[goal.period] = payload
    return exported


def _normalize_rewards(period: PeriodKey, raw_rewards: object) -> tuple[str, ...]:
    if isinstance(raw_rewards, list):
        rewards = tuple(
            str(reward).strip()
            for reward in raw_rewards
            if str(reward).strip()
        )
        if rewards:
            return rewards

    return DEFAULT_REWARDS[period]

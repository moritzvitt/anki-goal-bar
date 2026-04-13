from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from typing import Literal

from aqt import mw

MetricType = Literal["reviews", "new_cards", "study_minutes"]
PeriodKey = Literal["weekly", "monthly", "yearly", "custom"]
LayoutMode = Literal["all", "carousel"]
MilestoneKey = Literal["quarter", "half", "three_quarter"]
MilestoneDisplayMode = Literal["all", "next"]
StreakDisplayMode = Literal["all", "last"]

PERIODS: tuple[PeriodKey, ...] = ("weekly", "monthly", "yearly")
VALID_METRICS = {"reviews", "new_cards", "study_minutes"}
VALID_LAYOUTS = {"all", "carousel"}
VALID_MILESTONE_DISPLAY_MODES = {"all", "next"}
VALID_STREAK_DISPLAY_MODES = {"all", "last"}
MILESTONE_KEYS: tuple[MilestoneKey, ...] = ("quarter", "half", "three_quarter")
MILESTONE_RATIOS: dict[MilestoneKey, float] = {
    "quarter": 0.25,
    "half": 0.5,
    "three_quarter": 0.75,
}

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
        "enabled": True,
        "metric": "study_minutes",
        "target": 120,
        "rewards": list(DEFAULT_REWARDS["monthly"]),
    },
    "yearly": {
        "enabled": True,
        "metric": "new_cards",
        "target": 2000,
        "start_month": 1,
        "start_day": 1,
        "rewards": list(DEFAULT_REWARDS["yearly"]),
    },
}

DEFAULT_CUSTOM_GOAL = {
    "title": "Custom goal",
    "deck_id": None,
    "deck_name": "",
    "custom": {
        "enabled": True,
        "metric": "reviews",
        "target": 100,
        "start_year": date.today().year,
        "start_month": date.today().month,
        "start_day": date.today().day,
        "duration_days": 30,
        "rewards": list(DEFAULT_REWARDS["monthly"]),
        "show_reward": True,
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
    "layout": {
        "mode": "carousel",
        "show_behind_pace": False,
        "show_motivation": True,
        "show_streaks": True,
        "streak_display_mode": "all",
        "show_rewards": True,
        "show_milestones": True,
        "milestone_display_mode": "all",
        "motivation": (
            "Anki Japanese Learning Plan (Start: ~5000 Words)\n\n"
            "Goal: ~20k+ vocabulary and very high reading ability by ~2028.\n\n"
            "Current Setup\n"
            "Anki vocabulary deck\n"
            "RTK kanji deck\n"
            "Daily Japanese input already started\n\n"
            "2026 - Build Advanced Foundation\n"
            "Daily: 15-20 new words / 5 RTK kanji\n"
            "Input: podcasts, YouTube, shows\n"
            "Reading: 20-40 minutes per day\n"
            "Result: +5.5k-7.3k words -> total ~10k-12k\n\n"
            "2027 - Transition to Reading\n"
            "Daily: 10-15 new words (mostly mined from content)\n"
            "Reading: 45-60 minutes per day\n"
            "Content: books / essays / news\n"
            "Result: +3.6k-5.5k words -> total ~14k-17k\n\n"
            "2028 - Advanced Phase\n"
            "Daily: 5-10 new words\n"
            "Reading: 1-2 hours per day\n"
            "Most new vocabulary comes from reading\n"
            "Result: +2k-3.5k words -> total ~18k-20k+\n\n"
            "Milestones\n"
            "~8k words -> podcasts and simple texts comfortable\n"
            "~12k words -> news and many books readable\n"
            "~15k+ words -> most general texts understandable\n"
            "~20k+ words -> very high proficiency\n\n"
            "日本語勉強モチベーション\n\n"
            "就活をするため、いい会社に入りたいから\n"
            "日本人の友だちをつくるようになる\n"
            "本や映画や日本の文化のもの日本語でたのしめるようになる"
        ),
        "milestones": {
            "quarter": True,
            "half": True,
            "three_quarter": True,
        },
    },
    "decks": [],
    "custom_goals": [],
}


@dataclass(frozen=True)
class GoalDefinition:
    period: PeriodKey
    enabled: bool
    metric: MetricType
    target: int
    start_month: int = 1
    start_day: int = 1
    start_year: int = 0
    duration_days: int = 30
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
class CustomGoalDefinition:
    title: str
    deck_id: int | None
    deck_name: str
    goal: GoalDefinition

    @property
    def is_active(self) -> bool:
        return self.goal.is_active


@dataclass(frozen=True)
class AddonConfig:
    layout_mode: LayoutMode
    show_behind_pace: bool
    show_motivation: bool
    show_streaks: bool
    streak_display_mode: StreakDisplayMode
    show_rewards: bool
    show_milestones: bool
    milestone_display_mode: MilestoneDisplayMode
    motivation: str
    milestones: dict[MilestoneKey, bool]
    decks: tuple[DeckGoalDefinition, ...]
    custom_goals: tuple[CustomGoalDefinition, ...]

    @property
    def active_decks(self) -> tuple[DeckGoalDefinition, ...]:
        return tuple(deck for deck in self.decks if deck.active_goals and deck.deck_id is not None)

    @property
    def active_custom_goals(self) -> tuple[CustomGoalDefinition, ...]:
        return tuple(goal for goal in self.custom_goals if goal.is_active)


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
    show_motivation = bool(
        normalized.get("layout", {}).get(
            "show_motivation",
            DEFAULT_CONFIG["layout"]["show_motivation"],
        )
    )
    show_streaks = bool(
        normalized.get("layout", {}).get(
            "show_streaks",
            DEFAULT_CONFIG["layout"]["show_streaks"],
        )
    )
    streak_display_mode = normalized.get("layout", {}).get(
        "streak_display_mode",
        DEFAULT_CONFIG["layout"]["streak_display_mode"],
    )
    if streak_display_mode not in VALID_STREAK_DISPLAY_MODES:
        streak_display_mode = DEFAULT_CONFIG["layout"]["streak_display_mode"]
    show_rewards = bool(
        normalized.get("layout", {}).get(
            "show_rewards",
            DEFAULT_CONFIG["layout"]["show_rewards"],
        )
    )
    show_milestones = bool(
        normalized.get("layout", {}).get(
            "show_milestones",
            DEFAULT_CONFIG["layout"]["show_milestones"],
        )
    )
    milestone_display_mode = normalized.get("layout", {}).get(
        "milestone_display_mode",
        DEFAULT_CONFIG["layout"]["milestone_display_mode"],
    )
    if milestone_display_mode not in VALID_MILESTONE_DISPLAY_MODES:
        milestone_display_mode = DEFAULT_CONFIG["layout"]["milestone_display_mode"]
    motivation = str(
        normalized.get("layout", {}).get(
            "motivation",
            DEFAULT_CONFIG["layout"]["motivation"],
        )
        or ""
    )
    raw_milestones = normalized.get("layout", {}).get("milestones", {})
    milestones = {
        key: bool(raw_milestones.get(key, DEFAULT_CONFIG["layout"]["milestones"][key]))
        for key in MILESTONE_KEYS
    }

    raw_decks = list(normalized.get("decks", []))
    if not raw and not raw_decks:
        raw_decks = [_export_deck(default_deck_definition())]

    raw_custom_goals = list(normalized.get("custom_goals", []))
    decks = tuple(_deck_from_raw(raw_deck) for raw_deck in raw_decks)
    custom_goals = tuple(_custom_goal_from_raw(raw_goal) for raw_goal in raw_custom_goals)
    return AddonConfig(
        layout_mode=layout_mode,
        show_behind_pace=show_behind_pace,
        show_motivation=show_motivation,
        show_streaks=show_streaks,
        streak_display_mode=streak_display_mode,
        show_rewards=show_rewards,
        show_milestones=show_milestones,
        milestone_display_mode=milestone_display_mode,
        motivation=motivation,
        milestones=milestones,
        decks=decks,
        custom_goals=custom_goals,
    )  # type: ignore[arg-type]


def config_signature(config: AddonConfig) -> tuple:
    return (
        config.layout_mode,
        config.show_behind_pace,
        config.show_motivation,
        config.show_streaks,
        config.streak_display_mode,
        config.show_rewards,
        config.show_milestones,
        config.milestone_display_mode,
        config.motivation,
        tuple((key, config.milestones[key]) for key in MILESTONE_KEYS),
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
        tuple(
            (
                goal.title,
                goal.deck_id,
                goal.deck_name,
                goal.goal.period,
                goal.goal.enabled,
                goal.goal.metric,
                goal.goal.target,
                goal.goal.start_year,
                goal.goal.start_month,
                goal.goal.start_day,
                goal.goal.duration_days,
                goal.goal.rewards,
                goal.goal.show_reward,
            )
            for goal in config.custom_goals
        ),
    )


def export_config(config: AddonConfig) -> dict:
    return {
        "layout": {
            "mode": config.layout_mode,
            "show_behind_pace": config.show_behind_pace,
            "show_motivation": config.show_motivation,
            "show_streaks": config.show_streaks,
            "streak_display_mode": config.streak_display_mode,
            "show_rewards": config.show_rewards,
            "show_milestones": config.show_milestones,
            "milestone_display_mode": config.milestone_display_mode,
            "motivation": config.motivation,
            "milestones": {
                key: bool(config.milestones.get(key, DEFAULT_CONFIG["layout"]["milestones"][key]))
                for key in MILESTONE_KEYS
            },
        },
        "decks": [_export_deck(deck) for deck in config.decks],
        "custom_goals": [_export_custom_goal(goal) for goal in config.custom_goals],
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
            "layout": {
                "mode": "carousel",
                "show_rewards": True,
                "show_milestones": True,
                "milestone_display_mode": "all",
                "milestones": dict(DEFAULT_CONFIG["layout"]["milestones"]),
            },
            "decks": [
                _legacy_default_deck_entry(raw, current_deck)
            ],
        }

    return DEFAULT_CONFIG


def default_deck_definition() -> DeckGoalDefinition:
    deck_id, deck_name = _preferred_default_deck()
    return DeckGoalDefinition(
        deck_id=deck_id,
        deck_name=deck_name,
        goals=tuple(
            GoalDefinition(
                period=period,
                enabled=DEFAULT_DECK_ENTRY[period]["enabled"],
                metric=DEFAULT_DECK_ENTRY[period]["metric"],
                target=DEFAULT_DECK_ENTRY[period]["target"],
                start_month=DEFAULT_DECK_ENTRY[period].get("start_month", 1),
                start_day=DEFAULT_DECK_ENTRY[period].get("start_day", 1),
                rewards=DEFAULT_REWARDS[period],
            )
            for period in PERIODS
        ),
    )


def default_config() -> AddonConfig:
    return AddonConfig(
        layout_mode=DEFAULT_CONFIG["layout"]["mode"],
        show_behind_pace=DEFAULT_CONFIG["layout"]["show_behind_pace"],
        show_motivation=DEFAULT_CONFIG["layout"]["show_motivation"],
        show_streaks=DEFAULT_CONFIG["layout"]["show_streaks"],
        streak_display_mode=DEFAULT_CONFIG["layout"]["streak_display_mode"],
        show_rewards=DEFAULT_CONFIG["layout"]["show_rewards"],
        show_milestones=DEFAULT_CONFIG["layout"]["show_milestones"],
        milestone_display_mode=DEFAULT_CONFIG["layout"]["milestone_display_mode"],
        motivation=DEFAULT_CONFIG["layout"]["motivation"],
        milestones={key: True for key in MILESTONE_KEYS},
        decks=(default_deck_definition(),),
        custom_goals=(),
    )


def _deck_from_raw(raw_deck: dict) -> DeckGoalDefinition:
    deck_id = raw_deck.get("deck_id")
    try:
        parsed_deck_id = int(deck_id) if deck_id is not None else None
    except (TypeError, ValueError):
        parsed_deck_id = None

    deck_name = str(raw_deck.get("deck_name", "") or "")
    goals = tuple(_goal_from_raw(period, raw_deck.get(period, {})) for period in PERIODS)
    return DeckGoalDefinition(deck_id=parsed_deck_id, deck_name=deck_name, goals=goals)


def _legacy_default_deck_entry(raw: dict, current_deck: dict | None) -> dict:
    deck_id, deck_name = _preferred_default_deck()
    if deck_id is None and current_deck:
        deck_id = int(current_deck["id"])
        deck_name = str(current_deck["name"])

    return {
        "deck_id": deck_id,
        "deck_name": deck_name,
        "weekly": raw.get("weekly", DEFAULT_GOALS["weekly"]),
        "monthly": raw.get("monthly", DEFAULT_GOALS["monthly"]),
        "yearly": raw.get("yearly", DEFAULT_GOALS["yearly"]),
    }


def _preferred_default_deck() -> tuple[int | None, str]:
    if mw is None or mw.col is None:
        return (None, "")

    all_decks = [(deck.name, int(deck.id)) for deck in mw.col.decks.all_names_and_ids()]
    name_by_id = {deck_id: deck_name for deck_name, deck_id in all_decks}

    most_used = mw.col.db.first(
        """
        SELECT c.did, COUNT(*) AS review_count
        FROM revlog r
        JOIN cards c ON c.id = r.cid
        GROUP BY c.did
        ORDER BY review_count DESC
        LIMIT 1
        """
    )
    if most_used:
        most_used_id = int(most_used[0])
        deck_name = name_by_id.get(most_used_id, "")
        if deck_name:
            root_name = deck_name.split("::", 1)[0]
            for candidate_name, candidate_id in all_decks:
                if candidate_name == root_name:
                    return (candidate_id, candidate_name)
            return (most_used_id, deck_name)

    current_deck = mw.col.decks.current()
    if current_deck:
        return (int(current_deck["id"]), str(current_deck["name"]))

    return (None, "")


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


def default_custom_goal_definition() -> CustomGoalDefinition:
    custom = DEFAULT_CUSTOM_GOAL["custom"]
    return CustomGoalDefinition(
        title=str(DEFAULT_CUSTOM_GOAL["title"]),
        deck_id=None,
        deck_name="",
        goal=GoalDefinition(
            period="custom",
            enabled=bool(custom["enabled"]),
            metric=custom["metric"],  # type: ignore[arg-type]
            target=int(custom["target"]),
            start_year=int(custom["start_year"]),
            start_month=int(custom["start_month"]),
            start_day=int(custom["start_day"]),
            duration_days=int(custom["duration_days"]),
            rewards=_normalize_rewards("monthly", custom["rewards"]),
            show_reward=bool(custom["show_reward"]),
        ),
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


def _custom_goal_from_raw(raw_goal: dict) -> CustomGoalDefinition:
    deck_id = raw_goal.get("deck_id")
    try:
        parsed_deck_id = int(deck_id) if deck_id is not None else None
    except (TypeError, ValueError):
        parsed_deck_id = None

    title = str(raw_goal.get("title", DEFAULT_CUSTOM_GOAL["title"]) or DEFAULT_CUSTOM_GOAL["title"])
    deck_name = str(raw_goal.get("deck_name", "") or "")
    payload = raw_goal.get("custom", {})
    metric = payload.get("metric", DEFAULT_CUSTOM_GOAL["custom"]["metric"])
    if metric not in VALID_METRICS:
        metric = DEFAULT_CUSTOM_GOAL["custom"]["metric"]
    target = payload.get("target", DEFAULT_CUSTOM_GOAL["custom"]["target"])
    try:
        target_int = max(0, int(target))
    except (TypeError, ValueError):
        target_int = int(DEFAULT_CUSTOM_GOAL["custom"]["target"])
    start_year = payload.get("start_year", DEFAULT_CUSTOM_GOAL["custom"]["start_year"])
    try:
        start_year_int = max(1, int(start_year))
    except (TypeError, ValueError):
        start_year_int = int(DEFAULT_CUSTOM_GOAL["custom"]["start_year"])
    start_month_int, start_day_int = clamp_month_day(
        payload.get("start_month", DEFAULT_CUSTOM_GOAL["custom"]["start_month"]),
        payload.get("start_day", DEFAULT_CUSTOM_GOAL["custom"]["start_day"]),
    )
    duration_days = payload.get("duration_days", DEFAULT_CUSTOM_GOAL["custom"]["duration_days"])
    try:
        duration_days_int = max(1, int(duration_days))
    except (TypeError, ValueError):
        duration_days_int = int(DEFAULT_CUSTOM_GOAL["custom"]["duration_days"])
    rewards = _normalize_rewards("monthly", payload.get("rewards"))
    return CustomGoalDefinition(
        title=title,
        deck_id=parsed_deck_id,
        deck_name=deck_name,
        goal=GoalDefinition(
            period="custom",
            enabled=bool(payload.get("enabled", True)),
            metric=metric,  # type: ignore[arg-type]
            target=target_int,
            start_year=start_year_int,
            start_month=start_month_int,
            start_day=start_day_int,
            duration_days=duration_days_int,
            rewards=rewards,
            show_reward=bool(payload.get("show_reward", True)),
        ),
    )


def _export_custom_goal(goal: CustomGoalDefinition) -> dict:
    return {
        "title": goal.title,
        "deck_id": goal.deck_id,
        "deck_name": goal.deck_name,
        "custom": {
            "enabled": goal.goal.enabled,
            "metric": goal.goal.metric,
            "target": goal.goal.target,
            "start_year": goal.goal.start_year,
            "start_month": goal.goal.start_month,
            "start_day": goal.goal.start_day,
            "duration_days": goal.goal.duration_days,
            "rewards": list(goal.goal.rewards),
            "show_reward": goal.goal.show_reward,
        },
    }


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

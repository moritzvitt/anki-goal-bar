from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from unicodedata import category

from .config import GoalDefinition, LayoutMode, MetricType, MilestoneKey, PeriodKey, VisualStyle


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
    expected_current: int
    percent: int
    milestones: tuple["GoalMilestone", ...] = ()
    streak_badges: tuple["StreakBadge", ...] = ()

    @property
    def ratio(self) -> float:
        if self.target <= 0:
            return 0.0
        return min(1.0, self.current / self.target)

    @property
    def expected_ratio(self) -> float:
        if self.target <= 0:
            return 0.0
        return min(1.0, self.expected_current / self.target)

    @property
    def behind_amount(self) -> int:
        return max(0, self.expected_current - self.current)

    @property
    def behind_ratio(self) -> float:
        return max(0.0, self.expected_ratio - self.ratio)

    @property
    def reward_count(self) -> int:
        return len(self.goal.rewards)

    @property
    def reward_level(self) -> int:
        if self.reward_count == 0:
            return 0
        return min(self.reward_count, int(self.ratio * self.reward_count))

    @property
    def reward_badge(self) -> str:
        if self.reward_count == 0:
            return ""
        if self.reward_level <= 0:
            return f"Next reward: {self.goal.rewards[0]}"
        return f"Reward Lv {self.reward_level}/{self.reward_count}: {self.goal.rewards[self.reward_level - 1]}"

    @property
    def reward_detail(self) -> str:
        if self.reward_count == 0:
            return ""
        if self.reward_level <= 0:
            return f"Next reward: {self.goal.rewards[0]}"
        return self.goal.rewards[self.reward_level - 1]

    @property
    def reward_chip_label(self) -> str:
        if self.reward_count == 0:
            return ""
        return f"Lv {max(1, self.reward_level)}/{self.reward_count}"

    @property
    def reward_chip_emoji(self) -> str:
        if self.reward_count == 0:
            return ""
        reward = self.goal.rewards[max(0, self.reward_level - 1)]
        parts = reward.split(maxsplit=1)
        if parts and _looks_like_emoji(parts[0]):
            return parts[0]
        return "🏆"


def _looks_like_emoji(value: str) -> bool:
    return any(category(char).startswith("S") for char in value)


@dataclass(frozen=True)
class DeckProgress:
    deck_id: int
    deck_name: str
    goals: tuple[GoalProgress, ...]


@dataclass(frozen=True)
class GoalMilestone:
    key: MilestoneKey
    label: str
    ratio: float
    date_label: str
    short_date_label: str
    full_date_label: str


@dataclass(frozen=True)
class StreakBadge:
    emoji: str
    title: str
    tooltip: str


@dataclass(frozen=True)
class RenderPayload:
    layout_mode: LayoutMode
    visual_style: VisualStyle
    visual_style_auto: bool
    show_brief_page: bool
    show_brief_page_horizontal: bool
    show_behind_pace: bool
    show_catchup_button: bool
    show_motivation: bool
    show_streaks: bool
    streak_display_mode: str
    show_rewards: bool
    show_milestones: bool
    milestone_display_mode: str
    motivation: str
    decks: tuple[DeckProgress, ...]

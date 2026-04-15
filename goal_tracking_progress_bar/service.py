from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Callable

from aqt.main import AnkiQt

from .config import AddonConfig, MILESTONE_KEYS, MILESTONE_RATIOS, config_signature
from .metrics import GoalMetricsRepository
from .models import DeckProgress, GoalMilestone, GoalProgress, RenderPayload, StreakBadge
from .periods import current_period, elapsed_ratio, milestone_datetime, previous_period
from .render import metric_label, render_widget


@dataclass(frozen=True)
class _CacheEntry:
    html: str
    col_mod: int
    period_key: tuple
    config_key: tuple


class GoalProgressService:
    def __init__(self, main_window: AnkiQt, config_loader: Callable[[], AddonConfig]) -> None:
        self._mw = main_window
        self._config_loader = config_loader
        self._cache: _CacheEntry | None = None

    def render_widget(self) -> str:
        config = self._config_loader()
        now = datetime.now().astimezone()
        config_key = config_signature(config)
        period_key = _render_period_key(config, now)

        if self._cache and self._cache_still_valid(period_key, config_key):
            return self._cache.html

        payload = RenderPayload(
            layout_mode=config.layout_mode,
            visual_style=config.visual_style,
            visual_style_auto=config.visual_style_auto,
            show_brief_page=config.show_brief_page,
            show_brief_page_horizontal=config.show_brief_page_horizontal,
            show_behind_pace=config.show_behind_pace,
            show_catchup_button=config.show_catchup_button,
            show_motivation=config.show_motivation,
            show_streaks=config.show_streaks,
            streak_display_mode=config.streak_display_mode,
            show_rewards=config.show_rewards,
            show_milestones=config.show_milestones,
            milestone_display_mode=config.milestone_display_mode,
            motivation=config.motivation,
            decks=tuple(self._build_deck_progress(config, now)),
        )
        html = render_widget(payload)
        self._cache = _CacheEntry(
            html=html,
            col_mod=self._mw.col.mod,
            period_key=period_key,
            config_key=config_key,
        )
        return html

    def _build_deck_progress(self, config: AddonConfig, now: datetime) -> list[DeckProgress]:
        if not config.active_decks and not config.active_custom_goals:
            return []

        repo = GoalMetricsRepository(self._mw.col)
        available_decks = {int(deck.id): deck.name for deck in self._mw.col.decks.all_names_and_ids()}
        all_names = list(available_decks.items())

        payloads: list[DeckProgress] = []
        for deck_config in config.active_decks:
            if deck_config.deck_id not in available_decks:
                continue

            deck_name = available_decks[deck_config.deck_id]
            deck_ids = [
                deck_id
                for deck_id, name in all_names
                if name == deck_name or name.startswith(f"{deck_name}::")
            ]
            if not deck_ids:
                continue

            periods = {
                goal.period: current_period(goal, now)
                for goal in deck_config.active_goals
            }
            metrics = repo.load_metrics(deck_ids, periods.values())
            goals: list[GoalProgress] = []
            for goal in deck_config.active_goals:
                period = periods[goal.period]
                period_metrics = metrics.get(goal.period)
                if period_metrics is None:
                    continue
                current = period_metrics.value_for(goal.metric)
                expected_current = int(round(goal.target * elapsed_ratio(period, now)))
                percent = min(999, int((current / goal.target) * 100)) if goal.target > 0 else 0
                goals.append(
                    GoalProgress(
                        goal=goal,
                        label=period.label,
                        metric_label=metric_label(goal.metric),
                        current=current,
                        target=goal.target,
                        expected_current=expected_current,
                        percent=percent,
                        milestones=self._build_milestones(
                            config,
                            goal.period,
                            period,
                            now,
                            current,
                            goal.target,
                        ),
                        streak_badges=self._build_streak_badges(
                            repo,
                            deck_ids,
                            goal,
                            period,
                            current,
                        ),
                    )
                )

            if goals:
                payloads.append(
                    DeckProgress(
                        deck_id=deck_config.deck_id,
                        deck_name=deck_name,
                        goals=tuple(goals),
                    )
                )

        all_deck_ids = list(available_decks.keys())
        for custom_goal in config.active_custom_goals:
            deck_ids = all_deck_ids
            if custom_goal.deck_id is not None:
                if custom_goal.deck_id not in available_decks:
                    continue
                deck_name = available_decks[custom_goal.deck_id]
                deck_ids = [
                    deck_id
                    for deck_id, name in all_names
                    if name == deck_name or name.startswith(f"{deck_name}::")
                ]
            if not deck_ids:
                continue

            period = current_period(custom_goal.goal, now)
            metrics = repo.load_metrics(deck_ids, [period])
            period_metrics = metrics.get(custom_goal.goal.period)
            if period_metrics is None:
                continue
            current = period_metrics.value_for(custom_goal.goal.metric)
            expected_current = int(round(custom_goal.goal.target * elapsed_ratio(period, now)))
            percent = min(999, int((current / custom_goal.goal.target) * 100)) if custom_goal.goal.target > 0 else 0
            payloads.append(
                DeckProgress(
                    deck_id=custom_goal.deck_id or (-1000 - len(payloads)),
                    deck_name=custom_goal.title,
                    goals=(
                        GoalProgress(
                            goal=custom_goal.goal,
                            label=period.label,
                            metric_label=metric_label(custom_goal.goal.metric),
                            current=current,
                            target=custom_goal.goal.target,
                            expected_current=expected_current,
                            percent=percent,
                            milestones=self._build_milestones(
                                config,
                                custom_goal.goal.period,
                                period,
                                now,
                                current,
                                custom_goal.goal.target,
                            ),
                            streak_badges=self._build_streak_badges(
                                repo,
                                deck_ids,
                                custom_goal.goal,
                                period,
                                current,
                            ),
                        ),
                    ),
                )
            )

        return payloads

    def _cache_still_valid(self, period_key: tuple, config_key: tuple) -> bool:
        return (
            self._cache is not None
            and self._cache.col_mod == self._mw.col.mod
            and self._cache.period_key == period_key
            and self._cache.config_key == config_key
        )

    def _build_milestones(
        self,
        config: AddonConfig,
        period_key: str,
        period,
        now: datetime,
        current: int,
        target: int,
    ) -> tuple[GoalMilestone, ...]:
        if not config.show_milestones:
            return ()

        enabled_keys = (
            MILESTONE_KEYS
            if config.milestone_display_mode == "next"
            else tuple(key for key in MILESTONE_KEYS if config.milestones.get(key, False))
        )
        milestone_entries: list[tuple[GoalMilestone, datetime]] = []
        for key in enabled_keys:
            ratio = MILESTONE_RATIOS[key]
            moment = milestone_datetime(period, ratio)
            milestone_entries.append(
                (
                    GoalMilestone(
                        key=key,
                        label=_milestone_label(key),
                        ratio=ratio,
                        date_label=_milestone_date_label(period_key, moment),
                        short_date_label=_milestone_short_date_label(period_key, moment),
                        full_date_label=_milestone_date_label(period_key, moment),
                    ),
                    moment,
                )
            )
        milestones = tuple(milestone for milestone, _moment in milestone_entries)
        if config.milestone_display_mode == "next":
            if target > 0 and current >= target:
                preferred = next(
                    (milestone for milestone, _moment in milestone_entries if milestone.key == "half"),
                    None,
                )
                if preferred is not None:
                    return (preferred,)
                if milestones:
                    return (milestones[0],)
                return ()

            today = now.date()
            for milestone, moment in milestone_entries:
                if moment.date() > today:
                    return (milestone,)
            return ()
        return milestones

    def _build_streak_badges(
        self,
        repo: GoalMetricsRepository,
        deck_ids: list[int],
        goal,
        current_period_range,
        current_value: int,
    ) -> tuple[StreakBadge, ...]:
        badges: list[StreakBadge] = []
        candidate_period = current_period_range
        candidate_value = current_value

        if candidate_value >= goal.target:
            badges.append(_streak_badge(goal.period, candidate_period.label, candidate_value, goal.target, goal.metric))
            candidate_period = previous_period(goal, candidate_period)
        else:
            candidate_period = previous_period(goal, candidate_period)

        for _index in range(23):
            metrics = repo.load_period_metrics(deck_ids, candidate_period)
            value = metrics.value_for(goal.metric)
            if value < goal.target:
                break
            badges.append(_streak_badge(goal.period, candidate_period.label, value, goal.target, goal.metric))
            candidate_period = previous_period(goal, candidate_period)

        return tuple(badges)


def _milestone_label(key: str) -> str:
    return {
        "quarter": "1/4",
        "half": "1/2",
        "three_quarter": "3/4",
    }[key]


def _full_date_label(moment: datetime) -> str:
    return f"{moment.day}. {moment.strftime('%B')}"


def _short_date_label(moment: datetime) -> str:
    return moment.strftime("%d.%m")


def _weekday_label(moment: datetime) -> str:
    return moment.strftime("%A")


def _milestone_date_label(period_key: str, moment: datetime) -> str:
    if period_key == "weekly":
        return _weekday_label(moment)
    return _full_date_label(moment)


def _milestone_short_date_label(period_key: str, moment: datetime) -> str:
    if period_key == "weekly":
        return _weekday_label(moment)
    return _short_date_label(moment)


def _streak_badge(period_key: str, label: str, value: int, target: int, metric: str) -> StreakBadge:
    emoji = {
        "weekly": "🔥",
        "monthly": "🏅",
        "yearly": "👑",
        "custom": "🌟",
    }.get(period_key, "🏅")
    metric_copy = metric_label(metric)  # type: ignore[arg-type]
    tooltip = f"{label}: {value:,}/{target:,} {metric_copy}"
    return StreakBadge(emoji=emoji, title=label, tooltip=tooltip)


def _render_period_key(config: AddonConfig, now: datetime) -> tuple:
    periods: list[tuple[int | None, str, str, str]] = []
    for deck in config.active_decks:
        for goal in deck.active_goals:
            period = current_period(goal, now)
            periods.append(
                (
                    deck.deck_id,
                    goal.period,
                    period.start.isoformat(),
                    period.end.isoformat(),
                )
            )
    for custom_goal in config.active_custom_goals:
        period = current_period(custom_goal.goal, now)
        periods.append(
            (
                custom_goal.deck_id,
                custom_goal.goal.period,
                period.start.isoformat(),
                period.end.isoformat(),
            )
        )
    return tuple(periods)

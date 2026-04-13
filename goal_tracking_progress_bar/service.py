from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Callable

from aqt.main import AnkiQt

from .config import AddonConfig, MILESTONE_KEYS, MILESTONE_RATIOS, config_signature
from .metrics import GoalMetricsRepository
from .models import DeckProgress, GoalMilestone, GoalProgress, RenderPayload
from .periods import current_period, elapsed_ratio, milestone_datetime
from .render import metric_label, render_widget


@dataclass(frozen=True)
class _CacheEntry:
    html: str
    col_mod: int
    local_day: str
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

        if self._cache and self._cache_still_valid(now, config_key):
            return self._cache.html

        payload = RenderPayload(
            layout_mode=config.layout_mode,
            show_behind_pace=config.show_behind_pace,
            show_rewards=config.show_rewards,
            show_milestones=config.show_milestones,
            motivation=config.motivation,
            decks=tuple(self._build_deck_progress(config, now)),
        )
        html = render_widget(payload)
        self._cache = _CacheEntry(
            html=html,
            col_mod=self._mw.col.mod,
            local_day=now.date().isoformat(),
            config_key=config_key,
        )
        return html

    def _build_deck_progress(self, config: AddonConfig, now: datetime) -> list[DeckProgress]:
        if not config.active_decks:
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

        return payloads

    def _cache_still_valid(self, now: datetime, config_key: tuple) -> bool:
        return (
            self._cache is not None
            and self._cache.col_mod == self._mw.col.mod
            and self._cache.local_day == now.date().isoformat()
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

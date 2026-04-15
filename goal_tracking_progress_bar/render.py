from __future__ import annotations

from html import escape

from aqt import mw

from .config import LayoutMode, MetricType
from .models import DeckProgress, GoalMilestone, GoalProgress, RenderPayload, StreakBadge

_METRIC_LABELS: dict[MetricType, str] = {
    "reviews": "reviews",
    "new_cards": "new cards",
    "study_minutes": "minutes",
}
_HEATMAP_COLOR_LEVELS = 10
_HEATMAP_CELL_COUNT = 18
_HEATMAP_CELL_COUNT_COMPACT = 16


def metric_label(metric: MetricType) -> str:
    return _METRIC_LABELS[metric]


def render_widget(payload: RenderPayload) -> str:
    if not payload.decks:
        return _render_empty_state(payload.visual_style)

    wrap_classes = "gpb-wrap"
    if payload.layout_mode == "carousel":
        wrap_classes += " gpb-wrap-carousel"
    if payload.visual_style == "heatmap":
        wrap_classes += " gpb-style-heatmap"

    deck_blocks = "\n".join(
        _render_deck(
            deck,
            payload.layout_mode,
            payload.visual_style,
            payload.show_brief_page,
            payload.show_brief_page_horizontal,
            payload.brief_summary_periods,
            payload.show_behind_pace,
            payload.show_catchup_button,
            payload.show_streaks,
            payload.streak_display_mode,
            payload.show_rewards,
            payload.show_milestones,
            payload.milestone_display_mode,
        )
        for deck in payload.decks
    )
    scripts = [_MOTIVATION_SCRIPT, _CATCHUP_SCRIPT]
    if payload.layout_mode == "carousel":
        scripts.append(_CAROUSEL_SCRIPT)
    if payload.visual_style == "heatmap":
        scripts.append(_HEATMAP_MERGE_SCRIPT)
    script = "".join(scripts)

    return (
        f"{_STYLE_BLOCK}"
        f"<div class=\"{wrap_classes}\" data-layout-mode=\"{payload.layout_mode}\" data-visual-style=\"{payload.visual_style}\">"
        f"{_render_header(payload.layout_mode, payload.visual_style, len(payload.decks), payload.show_motivation, payload.motivation)}"
        f"<div class=\"gpb-decks\">{deck_blocks}</div>"
        f"</div>"
        f"{script}"
    )


def _render_deck(
    deck: DeckProgress,
    layout_mode: LayoutMode,
    visual_style: str,
    show_brief_page: bool,
    show_brief_page_horizontal: bool,
    brief_summary_periods: tuple[str, ...],
    show_behind_pace: bool,
    show_catchup_button: bool,
    show_streaks: bool,
    streak_display_mode: str,
    show_rewards: bool,
    show_milestones: bool,
    milestone_display_mode: str,
) -> str:
    brief_goals = tuple(
        goal
        for goal in deck.goals
        if goal.goal.period in brief_summary_periods
    )
    use_brief_page = layout_mode == "carousel" and show_brief_page and bool(brief_goals)
    rows: list[str] = []
    if use_brief_page:
        rows.append(
            _render_brief_goal_page(
                brief_goals,
                visual_style,
                show_brief_page_horizontal,
                show_behind_pace,
                show_milestones,
                milestone_display_mode,
            )
        )
    rows.extend(
        _render_goal(
            deck.deck_id,
            goal,
            visual_style,
            layout_mode == "carousel",
            index == 0 and not use_brief_page,
            show_behind_pace,
            show_catchup_button,
            show_streaks,
            streak_display_mode,
            show_rewards,
            show_milestones,
        )
        for index, goal in enumerate(deck.goals)
    )
    controls = ""
    if layout_mode == "carousel" and len(rows) > 1:
        controls = """
        <div class="gpb-deck-controls">
            <button class="gpb-cycle hm-btn-like" data-gpb-prev title="Previous goal" aria-label="Previous goal">‹</button>
            <button class="gpb-cycle hm-btn-like" data-gpb-next title="Next goal" aria-label="Next goal">›</button>
        </div>
        """

    return f"""
    <div class="gpb-widget gpb-deck" data-deck-id="{deck.deck_id}">
        <div class="gpb-deck-top">
            <div class="gpb-deck-title">{escape(deck.deck_name)}</div>
            {controls}
        </div>
        {"".join(rows)}
    </div>
    """


def _render_goal(
    deck_id: int,
    goal: GoalProgress,
    visual_style: str,
    carousel_mode: bool,
    is_initial: bool,
    show_behind_pace: bool,
    show_catchup_button: bool,
    show_streaks: bool,
    streak_display_mode: str,
    show_rewards: bool,
    show_milestones: bool,
) -> str:
    summary = f"{goal.current:,} / {goal.target:,} {goal.metric_label} {goal.label.lower()}"
    hidden_class = ""
    if carousel_mode and not is_initial:
        hidden_class = " gpb-goal-hidden"
    if show_milestones and goal.milestones:
        hidden_class += " gpb-goal-with-milestones"
    behind_note = ""
    if show_behind_pace and goal.behind_amount > 0:
        catch_up_button = ""
        if show_catchup_button and goal.goal.metric == "new_cards" and deck_id > 0:
            catch_up_button = (
                f'<button class="gpb-catchup" type="button" '
                f'data-gpb-catchup-deck="{deck_id}" '
                f'data-gpb-catchup-period="{escape(goal.label.lower())}" '
                f'data-gpb-catchup-amount="{goal.behind_amount}"'
                f'>Catch up</button>'
            )
        behind_note = (
            f'<div class="gpb-behind"><span>Behind pace by '
            f'{goal.behind_amount:,} {escape(goal.metric_label)}</span>{catch_up_button}</div>'
        )
    reward_badge = ""
    if show_rewards and goal.goal.show_reward and goal.reward_badge:
        reward_badge = f"""
        <div
            class="gpb-reward-badge"
            title="{escape(goal.reward_badge)}"
            aria-label="{escape(goal.reward_badge)}"
            tabindex="0"
        >
            <span class="gpb-reward-emoji">{escape(goal.reward_chip_emoji)}</span>
            <span class="gpb-reward-level">{escape(goal.reward_chip_label)}</span>
            <span class="gpb-reward-detail">{escape(goal.reward_detail)}</span>
        </div>
        """
    streaks = ""
    if show_streaks and goal.streak_badges:
        streaks = _render_streaks(goal.streak_badges, streak_display_mode)
    meter_html = _render_goal_meter(
        goal,
        visual_style=visual_style,
        show_behind_pace=show_behind_pace,
        show_milestones=show_milestones,
        compact=False,
    )

    return f"""
    <div class="gpb-goal{hidden_class}">
        <div class="gpb-header">
            <div class="gpb-title">{escape(goal.label)}</div>
            <div class="gpb-percent">{goal.percent}%</div>
        </div>
        <div class="gpb-summary">{escape(summary)}</div>
        {streaks}
        {reward_badge}
        {behind_note}
        {meter_html}
    </div>
    """


def _render_brief_goal_page(
    goals: tuple[GoalProgress, ...],
    visual_style: str,
    horizontal: bool,
    show_behind_pace: bool,
    show_milestones: bool,
    milestone_display_mode: str,
) -> str:
    brief_list_class = "gpb-brief-list gpb-brief-list-horizontal" if horizontal else "gpb-brief-list"
    rows = "".join(
        _render_brief_goal_row(
            goal,
            visual_style,
            show_behind_pace,
            show_milestones,
            milestone_display_mode,
        )
        for goal in goals
    )
    return f"""
    <div class="gpb-goal gpb-goal-brief">
        <div class="{brief_list_class}">{rows}</div>
    </div>
    """


def _render_brief_goal_row(
    goal: GoalProgress,
    visual_style: str,
    show_behind_pace: bool,
    show_milestones: bool,
    milestone_display_mode: str,
) -> str:
    summary = f"{goal.current:,}/{goal.target:,} {goal.metric_label}"
    milestones = _brief_milestones(goal.milestones, milestone_display_mode) if show_milestones else ()
    milestone_class = ""
    if milestones:
        milestone_class = " gpb-brief-row-with-milestones"
    meter_html = _render_goal_meter(
        goal,
        visual_style=visual_style,
        show_behind_pace=show_behind_pace,
        show_milestones=show_milestones,
        compact=True,
        milestone_override=milestones,
    )
    return f"""
    <div class="gpb-brief-row{milestone_class}">
        <div class="gpb-brief-top">
            <div class="gpb-brief-title">{escape(goal.label)}</div>
            <div class="gpb-brief-summary">{escape(summary)}</div>
        </div>
        {meter_html}
    </div>
    """


def _render_goal_meter(
    goal: GoalProgress,
    *,
    visual_style: str,
    show_behind_pace: bool,
    show_milestones: bool,
    compact: bool,
    milestone_override: tuple[GoalMilestone, ...] | None = None,
) -> str:
    milestones = milestone_override if milestone_override is not None else goal.milestones
    if visual_style == "heatmap":
        return _render_heatmap_meter(goal, show_behind_pace, milestones, compact)

    width = round(goal.ratio * 100, 1)
    expected_width = round(goal.expected_ratio * 100, 1)
    classes = "gpb-meter gpb-meter-brief" if compact else "gpb-meter"
    behind_fill = ""
    if show_behind_pace and goal.behind_amount > 0:
        behind_fill = (
            f'<div class="gpb-behind-fill" style="left: {width}%; width: {max(0.0, expected_width - width)}%"></div>'
        )
    milestone_strip = ""
    if show_milestones and milestones:
        milestone_strip = _render_milestones(milestones, compact=compact)
    summary = f"{goal.current:,}/{goal.target:,} {goal.metric_label}"
    return f"""
    <div class="{classes}" aria-label="{escape(summary)}">
        {behind_fill}
        <div class="gpb-fill" style="width: {width}%"></div>
        {milestone_strip}
    </div>
    """


def _render_heatmap_meter(
    goal: GoalProgress,
    show_behind_pace: bool,
    milestones: tuple[GoalMilestone, ...],
    compact: bool,
) -> str:
    summary = f"{goal.current:,}/{goal.target:,} {goal.metric_label}"
    cell_count = _HEATMAP_CELL_COUNT_COMPACT if compact else _HEATMAP_CELL_COUNT
    cells: list[str] = []
    for index in range(cell_count):
        start_ratio = index / cell_count
        milestone_hint = next(
            (milestone.label for milestone in milestones if start_ratio <= milestone.ratio < (index + 1) / cell_count),
            "",
        )
        classes = ["gpb-hm-cell"]
        if goal.ratio > start_ratio:
            level = min(
                _HEATMAP_COLOR_LEVELS,
                max(1, int(((index + 1) / cell_count) * _HEATMAP_COLOR_LEVELS)),
            )
            classes.append(f"gpb-hm-cell-level-{level}")
        elif show_behind_pace and goal.expected_ratio > start_ratio:
            classes.append("gpb-hm-cell-forecast")
        else:
            classes.append("gpb-hm-cell-empty")
        if milestone_hint:
            classes.append("gpb-hm-cell-milestone")
        title = milestone_hint or ""
        title_attr = f' title="{escape(title)}" aria-label="{escape(title)}"' if title else ""
        cells.append(
            f'<span class="{" ".join(classes)}"{title_attr}></span>'
        )

    milestone_strip = ""
    if milestones:
        markers = []
        for milestone in milestones:
            position = round(milestone.ratio * 100, 1)
            title = escape(f"{milestone.label}: {milestone.full_date_label}")
            badge_class = "gpb-hm-marker-badge gpb-hm-marker-badge-compact" if compact else "gpb-hm-marker-badge"
            markers.append(
                f"""
                <div class="gpb-hm-marker" style="left: {position}%;" title="{title}" aria-label="{title}">
                    <span class="gpb-hm-marker-line" aria-hidden="true"></span>
                    <span class="{badge_class}">{escape(milestone.label)}</span>
                </div>
                """
            )
        milestone_strip = f'<div class="gpb-hm-markers">{"".join(markers)}</div>'

    meter_classes = "gpb-meter gpb-meter-brief gpb-meter-heatmap" if compact else "gpb-meter gpb-meter-heatmap"
    grid_class = "gpb-hm-grid gpb-hm-grid-compact" if compact else "gpb-hm-grid"
    return f"""
    <div class="{meter_classes}" aria-label="{escape(summary)}">
        <div class="{grid_class}" style="--gpb-hm-cell-count: {cell_count};">{"".join(cells)}</div>
        {milestone_strip}
    </div>
    """


def _brief_milestones(
    milestones: tuple[GoalMilestone, ...],
    milestone_display_mode: str,
) -> tuple[GoalMilestone, ...]:
    if not milestones:
        return ()
    if milestone_display_mode == "next":
        return (milestones[0],)
    half = next((milestone for milestone in milestones if milestone.key == "half"), None)
    if half is not None:
        return (half,)
    return (milestones[0],)


def _render_milestones(milestones: tuple[GoalMilestone, ...], compact: bool = False) -> str:
    markers = []
    for milestone in milestones:
        position = round(milestone.ratio * 100, 1)
        label = escape(milestone.label)
        short_date = escape(milestone.short_date_label)
        full_date = escape(milestone.full_date_label)
        title = escape(f"{milestone.label}: {milestone.full_date_label}")
        badge_class = "gpb-milestone-badge gpb-milestone-badge-compact" if compact else "gpb-milestone-badge"
        markers.append(
            f"""
            <div class="gpb-milestone" style="left: {position}%;" title="{title}" aria-label="{title}">
                <span class="gpb-milestone-line" aria-hidden="true"></span>
                <span class="{badge_class}">
                    <span class="gpb-milestone-label">{label}</span>
                    <span class="gpb-milestone-date gpb-milestone-date-full">{full_date}</span>
                    <span class="gpb-milestone-date gpb-milestone-date-short">{short_date}</span>
                </span>
            </div>
            """
        )
    return f'<div class="gpb-milestones">{"".join(markers)}</div>'


def _render_streaks(badges: tuple[StreakBadge, ...], display_mode: str) -> str:
    if display_mode == "last" and len(badges) > 1:
        latest = badges[0]
        all_badges = "".join(_render_streak_badge(badge) for badge in badges)
        extra_count = len(badges) - 1
        return f"""
        <div class="gpb-streaks gpb-streaks-compact" tabindex="0" title="{escape(latest.tooltip)}" aria-label="{escape(latest.tooltip)}">
            <div class="gpb-streak-summary">
                {_render_streak_badge(latest)}
                <span class="gpb-streak-more">+{extra_count}</span>
            </div>
            <div class="gpb-streak-popover">{all_badges}</div>
        </div>
        """

    badges_html = "".join(_render_streak_badge(badge) for badge in badges)
    return f'<div class="gpb-streaks">{badges_html}</div>'


def _render_streak_badge(badge: StreakBadge) -> str:
    return (
        f'<span class="gpb-streak-badge" title="{escape(badge.tooltip)}" '
        f'aria-label="{escape(badge.tooltip)}" tabindex="0">{escape(badge.emoji)}</span>'
    )


def _render_header(
    layout_mode: LayoutMode,
    visual_style: str,
    deck_count: int,
    show_motivation: bool,
    motivation: str,
) -> str:
    count = f"<div class=\"gpb-count\">{deck_count} deck{'s' if deck_count != 1 else ''}</div>"
    heading = "Goal progress"
    if visual_style == "heatmap":
        heading = "Goal heatmap"
    motivation_copy = _render_motivation_markup(
        motivation.strip() or "Add your personal motivation in settings."
    )
    motivation_controls = ""
    if show_motivation:
        motivation_controls = f"""
            <button
                class="gpb-motivation-button"
                type="button"
                title="my Motivation"
                aria-label="my Motivation"
                aria-haspopup="dialog"
                aria-expanded="false"
                data-gpb-motivation-trigger
            >📜</button>
        """
    motivation_popup = ""
    if show_motivation:
        motivation_popup = f"""
    <div class="gpb-motivation-popup" hidden data-gpb-motivation-popup>
        <div class="gpb-motivation-backdrop" data-gpb-motivation-close></div>
        <div class="gpb-motivation-card" role="dialog" aria-modal="true" aria-label="my Motivation">
            <button class="gpb-motivation-close" type="button" aria-label="Close motivation" data-gpb-motivation-close>×</button>
            <div class="gpb-motivation-popup-title">my Motivation</div>
            <div class="gpb-motivation-popup-body">{motivation_copy}</div>
        </div>
    </div>
    """
    return f"""
    <div class="gpb-toolbar">
        <div class="gpb-heading-wrap">
            <div class="gpb-heading">{heading}</div>
            {count}
        </div>
        <div class="gpb-controls">
            {motivation_controls}
            <button class="gpb-config hm-btn-like" onclick="pycmd('gpb_config'); return false;" title="Configure goals" aria-label="Configure goals">
                <svg class="gpb-config-icon" viewBox="0 0 44 46" aria-hidden="true">
                    <g transform="rotate(90,22,22)">
                        <path d="m 2,8 h 6 v 2 a 2,2 0 0 0 2,2 h 12 a 2,2 0 0 0 2,-2 V 8 H 44 A 2,2 0 0 0 44,4 H 24 V 2 A 2,2 0 0 0 22,0 H 10 A 2,2 0 0 0 8,2 V 4 H 2 A 2,2 0 0 0 2,8 Z M 12,4 h 8 v 4 h -8 z"></path>
                        <path d="M 44,20 H 38 V 18 A 2,2 0 0 0 36,16 H 24 a 2,2 0 0 0 -2,2 v 2 H 2 a 2,2 0 0 0 0,4 h 20 v 2 a 2,2 0 0 0 2,2 h 12 a 2,2 0 0 0 2,-2 v -2 h 6 a 2,2 0 0 0 0,-4 z m -10,4 h -8 v -4 h 8 z"></path>
                        <path d="M 44,36 H 24 V 34 A 2,2 0 0 0 22,32 H 10 a 2,2 0 0 0 -2,2 v 2 H 2 a 2,2 0 0 0 0,4 h 6 v 2 a 2,2 0 0 0 2,2 h 12 a 2,2 0 0 0 2,-2 v -2 h 20 a 2,2 0 0 0 0,-4 z m -24,4 h -8 v -4 h 8 z"></path>
                    </g>
                </svg>
            </button>
        </div>
    </div>
    {motivation_popup}
    """


_STYLE_BLOCK = """
<style>
.gpb-wrap {
    margin: 12px auto 0;
    max-width: 520px;
}
.gpb-wrap-carousel .gpb-decks {
    position: relative;
}
.gpb-widget {
    --gpb-border: rgba(0, 0, 0, 0.12);
    --gpb-text: var(--fg, #2f3742);
    --gpb-muted: rgba(47, 55, 66, 0.72);
    --gpb-bg: rgba(127, 140, 153, 0.12);
    --gpb-fill-start: #70b77e;
    --gpb-fill-end: #4f9d69;
    padding: 10px 12px;
    border: 1px solid var(--gpb-border);
    border-radius: 10px;
    background: var(--canvas, rgba(255, 255, 255, 0.78));
    text-align: left;
    box-sizing: border-box;
}
.gpb-widget + .gpb-widget {
    margin-top: 10px;
}
.gpb-deck-top {
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 8px;
    margin-bottom: 8px;
}
.gpb-toolbar {
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 12px;
    margin: 0 2px 6px;
}
.gpb-heading-wrap {
    display: flex;
    align-items: baseline;
    gap: 8px;
}
.gpb-heading {
    color: var(--gpb-text);
    font-size: 13px;
    font-weight: 700;
    letter-spacing: 0.01em;
}
.gpb-count {
    color: var(--gpb-muted);
    font-size: 11px;
}
.gpb-deck-controls,
.gpb-controls {
    display: flex;
    align-items: center;
    gap: 4px;
}
.gpb-controls {
    overflow: visible;
}
.hm-btn-like {
    display: inline-flex;
    align-items: center;
    justify-content: center;
    padding: 2px 4px;
    border: 0;
    border-radius: 3px;
    background: #e6e6e6;
    color: #9e9e9e;
    cursor: pointer;
}
.hm-btn-like:hover {
    background: #bfbfbf;
}
.hm-btn-like:active {
    background: #000;
}
.gpb-cycle,
.gpb-config {
    width: 24px;
    height: 24px;
    flex: 0 0 auto;
}
.gpb-motivation-button {
    width: 24px;
    height: 24px;
    padding: 0;
    border: 0;
    background: transparent;
    font-size: 18px;
    line-height: 1;
    cursor: pointer;
    transition: transform 160ms ease, filter 160ms ease;
}
.gpb-motivation-button:hover,
.gpb-motivation-button:focus-visible {
    transform: scale(1.18);
    filter: saturate(1.08);
}
.gpb-motivation-popup[hidden] {
    display: none;
}
.gpb-motivation-popup {
    position: fixed;
    inset: 0;
    z-index: 9999;
    display: flex;
    align-items: center;
    justify-content: center;
    padding: 52px 28px;
    box-sizing: border-box;
}
.gpb-motivation-backdrop {
    position: absolute;
    inset: 0;
    background: rgba(24, 18, 11, 0.28);
}
.gpb-motivation-card {
    position: relative;
    z-index: 1;
    width: min(420px, calc(100vw - 56px));
    max-height: calc(100vh - 104px);
    padding: 16px 16px 14px;
    border: 1px solid rgba(170, 130, 68, 0.4);
    border-radius: 16px;
    background: linear-gradient(180deg, rgba(250, 241, 213, 0.99), rgba(229, 206, 156, 0.99));
    color: #4f3920;
    box-shadow: 0 16px 34px rgba(24, 18, 11, 0.24);
    box-sizing: border-box;
    overflow: hidden;
}
.gpb-motivation-popup-title {
    padding-right: 24px;
    font-size: 13px;
    font-weight: 700;
    letter-spacing: 0.01em;
}
.gpb-motivation-popup-body {
    margin-top: 8px;
    max-height: calc(100vh - 220px);
    overflow-y: auto;
    font-size: 13px;
    line-height: 1.5;
    white-space: pre-wrap;
    text-align: left;
}
.gpb-motivation-popup-body > :first-child {
    margin-top: 0;
}
.gpb-motivation-popup-body > :last-child {
    margin-bottom: 0;
}
.gpb-motivation-popup-body p,
.gpb-motivation-popup-body ul,
.gpb-motivation-popup-body ol,
.gpb-motivation-popup-body blockquote,
.gpb-motivation-popup-body pre {
    margin: 0.7em 0;
}
.gpb-motivation-popup-body ul,
.gpb-motivation-popup-body ol {
    padding-left: 1.4em;
}
.gpb-motivation-popup-body a {
    color: inherit;
    text-decoration: underline;
}
.gpb-motivation-popup-body code {
    padding: 0.05em 0.35em;
    border-radius: 6px;
    background: rgba(95, 70, 36, 0.12);
    font-size: 0.95em;
}
.gpb-motivation-popup-body pre {
    padding: 10px 12px;
    border-radius: 10px;
    background: rgba(95, 70, 36, 0.1);
    overflow-x: auto;
    white-space: pre-wrap;
}
.gpb-motivation-popup-body pre code {
    padding: 0;
    background: transparent;
}
.gpb-motivation-close {
    position: absolute;
    top: 8px;
    right: 8px;
    width: 24px;
    height: 24px;
    padding: 0;
    border: 0;
    border-radius: 999px;
    background: rgba(95, 70, 36, 0.12);
    color: inherit;
    font-size: 18px;
    line-height: 1;
    cursor: pointer;
}
.gpb-motivation-close:hover,
.gpb-motivation-close:focus-visible {
    background: rgba(95, 70, 36, 0.2);
}
.gpb-cycle {
    font-size: 15px;
    line-height: 1;
}
.gpb-config-icon {
    width: 10px;
    height: 10px;
    display: block;
    fill: currentColor;
}
.gpb-goal-hidden {
    display: none;
}
.gpb-deck-title {
    color: var(--gpb-text);
    font-size: 14px;
    font-weight: 700;
}
.gpb-goal + .gpb-goal {
    margin-top: 10px;
    padding-top: 10px;
    border-top: 1px solid var(--gpb-border);
}
.gpb-wrap-carousel .gpb-goal {
    padding-top: 10px;
    border-top: 1px solid var(--gpb-border);
}
.gpb-goal-brief {
    padding-bottom: 0;
}
.gpb-brief-list {
    display: flex;
    flex-direction: column;
    gap: 8px;
}
.gpb-brief-list-horizontal {
    flex-direction: row;
    gap: 10px;
}
.gpb-brief-row {
    position: relative;
}
.gpb-brief-list-horizontal .gpb-brief-row {
    flex: 1 1 0;
    min-width: 0;
}
.gpb-brief-row + .gpb-brief-row {
    padding-top: 8px;
    border-top: 1px solid rgba(0, 0, 0, 0.06);
}
.gpb-brief-list-horizontal .gpb-brief-row + .gpb-brief-row {
    padding-top: 0;
    padding-left: 10px;
    border-top: 0;
    border-left: 1px solid rgba(0, 0, 0, 0.06);
}
.gpb-brief-row-with-milestones {
    padding-bottom: 18px;
}
.gpb-brief-top {
    display: flex;
    align-items: baseline;
    justify-content: space-between;
    gap: 10px;
}
.gpb-brief-title {
    color: var(--gpb-text);
    font-size: 12px;
    font-weight: 700;
}
.gpb-brief-summary {
    color: var(--gpb-muted);
    font-size: 11px;
    white-space: nowrap;
}
.gpb-brief-list-horizontal .gpb-brief-top {
    flex-direction: column;
    align-items: flex-start;
    gap: 2px;
}
.gpb-brief-list-horizontal .gpb-brief-summary {
    font-size: 10px;
}
.gpb-meter-brief {
    margin-top: 4px;
}
.gpb-header {
    display: flex;
    align-items: baseline;
    justify-content: space-between;
    gap: 12px;
}
.gpb-title {
    color: var(--gpb-text);
    font-size: 14px;
    font-weight: 600;
}
.gpb-percent {
    color: var(--gpb-muted);
    font-size: 12px;
    font-weight: 600;
}
.gpb-summary {
    margin-top: 3px;
    color: var(--gpb-muted);
    font-size: 12px;
    line-height: 1.35;
}
.gpb-streaks {
    display: flex;
    align-items: center;
    gap: 4px;
    margin-top: 6px;
    flex-wrap: wrap;
}
.gpb-streak-badge {
    display: inline-flex;
    align-items: center;
    justify-content: center;
    width: 24px;
    height: 24px;
    border-radius: 999px;
    background: rgba(242, 179, 63, 0.16);
    border: 1px solid rgba(205, 144, 29, 0.24);
    font-size: 14px;
    line-height: 1;
}
.gpb-streaks-compact {
    position: relative;
    display: inline-flex;
    cursor: default;
}
.gpb-streak-summary {
    display: inline-flex;
    align-items: center;
    gap: 4px;
}
.gpb-streak-more {
    color: var(--gpb-muted);
    font-size: 11px;
    font-weight: 700;
}
.gpb-streak-popover {
    position: absolute;
    top: calc(100% + 8px);
    left: 0;
    display: none;
    align-items: center;
    gap: 4px;
    flex-wrap: wrap;
    min-width: 120px;
    max-width: 220px;
    padding: 8px;
    border: 1px solid var(--gpb-border);
    border-radius: 12px;
    background: var(--canvas, rgba(255, 255, 255, 0.98));
    box-shadow: 0 10px 22px rgba(0, 0, 0, 0.12);
    z-index: 4;
}
.gpb-streaks-compact:hover .gpb-streak-popover,
.gpb-streaks-compact:focus-visible .gpb-streak-popover,
.gpb-streaks-compact:focus-within .gpb-streak-popover {
    display: flex;
}
.gpb-reward-badge {
    display: inline-flex;
    align-items: center;
    gap: 5px;
    max-width: 72px;
    margin-top: 6px;
    padding: 3px 8px;
    border: 1px solid rgba(79, 157, 105, 0.2);
    border-radius: 999px;
    background: rgba(112, 183, 126, 0.12);
    color: var(--gpb-text);
    font-size: 11px;
    font-weight: 600;
    line-height: 1.35;
    box-sizing: border-box;
    overflow: hidden;
    white-space: nowrap;
    vertical-align: top;
    transition: max-width 180ms ease, background 180ms ease, border-color 180ms ease;
}
.gpb-reward-badge:hover,
.gpb-reward-badge:focus-visible {
    max-width: min(320px, 100%);
    align-items: flex-start;
}
.gpb-reward-emoji {
    flex: 0 0 auto;
}
.gpb-reward-level {
    flex: 0 0 auto;
}
.gpb-reward-detail {
    display: inline-block;
    max-width: 0;
    max-height: 1.4em;
    overflow: hidden;
    opacity: 0;
    white-space: nowrap;
    line-height: 1.4;
    transition: max-width 180ms ease, max-height 180ms ease, opacity 180ms ease;
}
.gpb-reward-badge:hover .gpb-reward-detail,
.gpb-reward-badge:focus-visible .gpb-reward-detail {
    max-width: 240px;
    max-height: 12em;
    opacity: 1;
    white-space: normal;
    overflow-wrap: anywhere;
}
.gpb-meter {
    margin-top: 7px;
    height: 8px;
    border-radius: 999px;
    overflow: visible;
    position: relative;
    background: var(--gpb-bg);
}
.gpb-behind {
    margin-top: 4px;
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 8px;
    color: rgba(183, 76, 76, 0.82);
    font-size: 11px;
    line-height: 1.3;
}
.gpb-catchup {
    flex: 0 0 auto;
    padding: 1px 8px;
    border: 1px solid rgba(183, 76, 76, 0.24);
    border-radius: 999px;
    background: rgba(183, 76, 76, 0.1);
    color: inherit;
    font-size: 11px;
    font-weight: 600;
    cursor: pointer;
}
.gpb-catchup:hover,
.gpb-catchup:focus-visible {
    background: rgba(183, 76, 76, 0.18);
}
.gpb-behind-fill {
    position: absolute;
    top: 0;
    bottom: 0;
    border-radius: 999px;
    background: rgba(198, 70, 70, 0.28);
}
.gpb-fill {
    position: relative;
    z-index: 1;
    height: 100%;
    min-width: 0;
    border-radius: 999px;
    background: linear-gradient(90deg, var(--gpb-fill-start), var(--gpb-fill-end));
}
.gpb-milestones {
    position: absolute;
    inset: 0;
    overflow: visible;
    z-index: 2;
    pointer-events: none;
}
.gpb-milestone {
    position: absolute;
    top: 0;
    transform: translateX(-50%);
    display: flex;
    flex-direction: column;
    align-items: center;
    pointer-events: auto;
}
.gpb-milestone-line {
    width: 1px;
    height: 8px;
    background: rgba(47, 55, 66, 0.52);
}
.gpb-milestone-badge {
    display: inline-flex;
    align-items: center;
    gap: 4px;
    margin-top: 5px;
    padding: 1px 5px;
    border-radius: 999px;
    background: rgba(255, 255, 255, 0.92);
    color: var(--gpb-text);
    font-size: 10px;
    line-height: 1.25;
    white-space: nowrap;
    box-shadow: 0 1px 2px rgba(0, 0, 0, 0.08);
}
.gpb-milestone-badge-compact {
    gap: 3px;
    margin-top: 4px;
    padding: 1px 4px;
    font-size: 9px;
}
.gpb-milestone-label {
    font-weight: 700;
}
.gpb-milestone-date-short {
    display: none;
}
.gpb-goal-with-milestones {
    padding-bottom: 24px;
}
.gpb-empty-title {
    color: var(--gpb-text);
    font-size: 13px;
    font-weight: 600;
}
.gpb-empty-copy {
    margin-top: 3px;
    color: var(--gpb-muted);
    font-size: 12px;
    line-height: 1.4;
}
.gpb-style-heatmap {
    margin-top: 1em;
}
.gpb-style-heatmap .gpb-widget {
    --gpb-border: #d4d4d4;
    --gpb-text: #4b4b4b;
    --gpb-muted: #7a7a7a;
    --gpb-bg: transparent;
    padding: 10px 11px;
    border-radius: 6px;
    background: transparent;
    box-shadow: none;
}
.gpb-style-heatmap .gpb-heading,
.gpb-style-heatmap .gpb-deck-title,
.gpb-style-heatmap .gpb-title,
.gpb-style-heatmap .gpb-brief-title {
    letter-spacing: 0.03em;
    text-transform: uppercase;
}
.gpb-style-heatmap .gpb-heading {
    font-size: 12px;
}
.gpb-style-heatmap .gpb-count,
.gpb-style-heatmap .gpb-summary,
.gpb-style-heatmap .gpb-brief-summary,
.gpb-style-heatmap .gpb-percent {
    font-family: "SFMono-Regular", "Cascadia Mono", "Liberation Mono", monospace;
}
.gpb-style-heatmap .gpb-goal + .gpb-goal,
.gpb-style-heatmap.gpb-wrap-carousel .gpb-goal {
    border-top-style: dashed;
}
.gpb-style-heatmap .gpb-reward-badge {
    border-radius: 4px;
    background: rgba(120, 168, 81, 0.1);
}
.gpb-style-heatmap .gpb-streak-badge {
    border-radius: 4px;
}
.gpb-style-heatmap .gpb-meter-heatmap {
    margin-top: 8px;
    height: auto;
    background: transparent;
}
.gpb-style-heatmap .gpb-hm-grid {
    display: grid;
    grid-template-columns: repeat(var(--gpb-hm-cell-count, 18), minmax(0, 1fr));
    gap: 3px;
}
.gpb-style-heatmap .gpb-hm-grid-compact {
    gap: 3px;
}
.gpb-style-heatmap .gpb-hm-cell {
    display: block;
    min-width: 0;
    height: 12px;
    border-radius: 2px;
    background: #eaeaea;
    box-shadow: inset 0 0 0 1px rgba(0, 0, 0, 0.04);
}
.gpb-style-heatmap .gpb-hm-grid-compact .gpb-hm-cell {
    height: 11px;
}
.gpb-style-heatmap .gpb-hm-cell-empty {
    background: #eaeaea;
}
.gpb-style-heatmap .gpb-hm-cell-forecast {
    background: #bcbcbc;
}
.gpb-style-heatmap .gpb-hm-cell-milestone {
    box-shadow: inset 0 0 0 1px rgba(59, 100, 39, 0.6);
}
.gpb-style-heatmap .gpb-hm-cell-level-1 { background: #dae289; }
.gpb-style-heatmap .gpb-hm-cell-level-2 { background: #bbd179; }
.gpb-style-heatmap .gpb-hm-cell-level-3 { background: #9cc069; }
.gpb-style-heatmap .gpb-hm-cell-level-4 { background: #8ab45d; }
.gpb-style-heatmap .gpb-hm-cell-level-5 { background: #78a851; }
.gpb-style-heatmap .gpb-hm-cell-level-6 { background: #669d45; }
.gpb-style-heatmap .gpb-hm-cell-level-7 { background: #648b3f; }
.gpb-style-heatmap .gpb-hm-cell-level-8 { background: #637939; }
.gpb-style-heatmap .gpb-hm-cell-level-9 { background: #4f6e30; }
.gpb-style-heatmap .gpb-hm-cell-level-10 { background: #3b6427; }
.gpb-style-heatmap .gpb-hm-markers {
    position: absolute;
    inset: 0;
    overflow: visible;
    pointer-events: none;
}
.gpb-style-heatmap .gpb-hm-marker {
    position: absolute;
    top: 100%;
    transform: translateX(-50%);
    display: flex;
    flex-direction: column;
    align-items: center;
    pointer-events: auto;
}
.gpb-style-heatmap .gpb-hm-marker-line {
    width: 1px;
    height: 6px;
    background: rgba(59, 100, 39, 0.72);
}
.gpb-style-heatmap .gpb-hm-marker-badge {
    margin-top: 4px;
    padding: 1px 4px;
    border-radius: 3px;
    background: rgba(255, 255, 255, 0.94);
    color: #4b4b4b;
    font-size: 9px;
    font-weight: 700;
    line-height: 1.2;
    text-transform: uppercase;
    box-shadow: 0 1px 2px rgba(0, 0, 0, 0.08);
}
.gpb-style-heatmap .gpb-hm-marker-badge-compact {
    margin-top: 3px;
    padding: 1px 3px;
    font-size: 8px;
}
.gpb-style-heatmap .gpb-motivation-card {
    border-radius: 6px;
}
.gpb-style-heatmap.gpb-rh-theme-lime .gpb-hm-cell-level-1 { background: #d6e685; }
.gpb-style-heatmap.gpb-rh-theme-lime .gpb-hm-cell-level-2 { background: #b6d97b; }
.gpb-style-heatmap.gpb-rh-theme-lime .gpb-hm-cell-level-3 { background: #8cc665; }
.gpb-style-heatmap.gpb-rh-theme-lime .gpb-hm-cell-level-4 { background: #70b253; }
.gpb-style-heatmap.gpb-rh-theme-lime .gpb-hm-cell-level-5 { background: #5da14c; }
.gpb-style-heatmap.gpb-rh-theme-lime .gpb-hm-cell-level-6 { background: #4b9146; }
.gpb-style-heatmap.gpb-rh-theme-lime .gpb-hm-cell-level-7 { background: #3f7f3f; }
.gpb-style-heatmap.gpb-rh-theme-lime .gpb-hm-cell-level-8 { background: #356f39; }
.gpb-style-heatmap.gpb-rh-theme-lime .gpb-hm-cell-level-9 { background: #2d6033; }
.gpb-style-heatmap.gpb-rh-theme-lime .gpb-hm-cell-level-10 { background: #254f2c; }
.gpb-style-heatmap.gpb-rh-theme-ice .gpb-hm-cell-level-1 { background: #d5f2ff; }
.gpb-style-heatmap.gpb-rh-theme-ice .gpb-hm-cell-level-2 { background: #b5e8ff; }
.gpb-style-heatmap.gpb-rh-theme-ice .gpb-hm-cell-level-3 { background: #8ad9ff; }
.gpb-style-heatmap.gpb-rh-theme-ice .gpb-hm-cell-level-4 { background: #6fc5ff; }
.gpb-style-heatmap.gpb-rh-theme-ice .gpb-hm-cell-level-5 { background: #54b2ff; }
.gpb-style-heatmap.gpb-rh-theme-ice .gpb-hm-cell-level-6 { background: #439be3; }
.gpb-style-heatmap.gpb-rh-theme-ice .gpb-hm-cell-level-7 { background: #387fb7; }
.gpb-style-heatmap.gpb-rh-theme-ice .gpb-hm-cell-level-8 { background: #2f698f; }
.gpb-style-heatmap.gpb-rh-theme-ice .gpb-hm-cell-level-9 { background: #285970; }
.gpb-style-heatmap.gpb-rh-theme-ice .gpb-hm-cell-level-10 { background: #1f4657; }
.gpb-style-heatmap.gpb-rh-theme-magenta .gpb-hm-cell-level-1 { background: #f4c8d9; }
.gpb-style-heatmap.gpb-rh-theme-magenta .gpb-hm-cell-level-2 { background: #ecacc5; }
.gpb-style-heatmap.gpb-rh-theme-magenta .gpb-hm-cell-level-3 { background: #e487af; }
.gpb-style-heatmap.gpb-rh-theme-magenta .gpb-hm-cell-level-4 { background: #da669d; }
.gpb-style-heatmap.gpb-rh-theme-magenta .gpb-hm-cell-level-5 { background: #cf4d8d; }
.gpb-style-heatmap.gpb-rh-theme-magenta .gpb-hm-cell-level-6 { background: #c03f80; }
.gpb-style-heatmap.gpb-rh-theme-magenta .gpb-hm-cell-level-7 { background: #a5356d; }
.gpb-style-heatmap.gpb-rh-theme-magenta .gpb-hm-cell-level-8 { background: #8c2f5e; }
.gpb-style-heatmap.gpb-rh-theme-magenta .gpb-hm-cell-level-9 { background: #70274c; }
.gpb-style-heatmap.gpb-rh-theme-magenta .gpb-hm-cell-level-10 { background: #551d39; }
.gpb-style-heatmap.gpb-rh-theme-flame .gpb-hm-cell-level-1 { background: #ffd3a2; }
.gpb-style-heatmap.gpb-rh-theme-flame .gpb-hm-cell-level-2 { background: #ffb97b; }
.gpb-style-heatmap.gpb-rh-theme-flame .gpb-hm-cell-level-3 { background: #ff9e58; }
.gpb-style-heatmap.gpb-rh-theme-flame .gpb-hm-cell-level-4 { background: #ff8741; }
.gpb-style-heatmap.gpb-rh-theme-flame .gpb-hm-cell-level-5 { background: #f37034; }
.gpb-style-heatmap.gpb-rh-theme-flame .gpb-hm-cell-level-6 { background: #dc5f2d; }
.gpb-style-heatmap.gpb-rh-theme-flame .gpb-hm-cell-level-7 { background: #bd4f27; }
.gpb-style-heatmap.gpb-rh-theme-flame .gpb-hm-cell-level-8 { background: #9e4222; }
.gpb-style-heatmap.gpb-rh-theme-flame .gpb-hm-cell-level-9 { background: #81361d; }
.gpb-style-heatmap.gpb-rh-theme-flame .gpb-hm-cell-level-10 { background: #652a17; }
.nightMode .gpb-widget,
.night_mode .gpb-widget {
    --gpb-border: rgba(255, 255, 255, 0.1);
    --gpb-text: #e7ebf0;
    --gpb-muted: rgba(231, 235, 240, 0.72);
    --gpb-bg: rgba(255, 255, 255, 0.08);
    background: rgba(255, 255, 255, 0.04);
}
.nightMode .gpb-reward-badge,
.night_mode .gpb-reward-badge {
    border-color: rgba(112, 183, 126, 0.28);
    background: rgba(112, 183, 126, 0.16);
}
.nightMode .gpb-streak-badge,
.night_mode .gpb-streak-badge {
    background: rgba(242, 179, 63, 0.18);
    border-color: rgba(242, 179, 63, 0.24);
}
.nightMode .gpb-streak-popover,
.night_mode .gpb-streak-popover {
    background: rgba(49, 61, 69, 0.98);
    box-shadow: 0 10px 22px rgba(0, 0, 0, 0.28);
}
.nightMode .gpb-milestone-line,
.night_mode .gpb-milestone-line {
    background: rgba(231, 235, 240, 0.6);
}
.nightMode .gpb-milestone-badge,
.night_mode .gpb-milestone-badge {
    background: rgba(49, 61, 69, 0.94);
    box-shadow: 0 1px 2px rgba(0, 0, 0, 0.3);
}
.nightMode .gpb-brief-row + .gpb-brief-row,
.night_mode .gpb-brief-row + .gpb-brief-row {
    border-top-color: rgba(255, 255, 255, 0.08);
}
.nightMode .gpb-brief-list-horizontal .gpb-brief-row + .gpb-brief-row,
.night_mode .gpb-brief-list-horizontal .gpb-brief-row + .gpb-brief-row {
    border-left-color: rgba(255, 255, 255, 0.08);
}
.nightMode .gpb-motivation-card,
.night_mode .gpb-motivation-card {
    border-color: rgba(222, 191, 133, 0.28);
    background: linear-gradient(180deg, rgba(120, 92, 52, 0.98), rgba(88, 64, 33, 0.98));
    color: #f6e8c7;
}
.nightMode .gpb-catchup,
.night_mode .gpb-catchup {
    border-color: rgba(242, 123, 123, 0.24);
    background: rgba(242, 123, 123, 0.12);
}
.nightMode .gpb-catchup:hover,
.night_mode .gpb-catchup:hover,
.nightMode .gpb-catchup:focus-visible,
.night_mode .gpb-catchup:focus-visible {
    background: rgba(242, 123, 123, 0.2);
}
.nightMode .gpb-motivation-close,
.night_mode .gpb-motivation-close {
    background: rgba(246, 232, 199, 0.12);
}
.nightMode .gpb-motivation-popup-body code,
.night_mode .gpb-motivation-popup-body code {
    background: rgba(246, 232, 199, 0.12);
}
.nightMode .gpb-motivation-popup-body pre,
.night_mode .gpb-motivation-popup-body pre {
    background: rgba(246, 232, 199, 0.1);
}
.nightMode .gpb-motivation-close:hover,
.night_mode .gpb-motivation-close:hover,
.nightMode .gpb-motivation-close:focus-visible,
.night_mode .gpb-motivation-close:focus-visible {
    background: rgba(246, 232, 199, 0.22);
}
.nightMode .hm-btn-like,
.night_mode .hm-btn-like {
    background: #313d45;
}
.nightMode .hm-btn-like:hover,
.night_mode .hm-btn-like:hover {
    background: #374f5b;
}
.nightMode .hm-btn-like:active,
.night_mode .hm-btn-like:active {
    background: #433376;
}
.nightMode .gpb-style-heatmap .gpb-widget,
.night_mode .gpb-style-heatmap .gpb-widget {
    --gpb-border: rgba(255, 255, 255, 0.12);
    --gpb-text: #d7dadf;
    --gpb-muted: #9aa7b0;
    background: transparent;
}
.nightMode .gpb-style-heatmap .gpb-hm-cell-empty,
.night_mode .gpb-style-heatmap .gpb-hm-cell-empty {
    background: #222222;
}
.nightMode .gpb-style-heatmap .gpb-hm-cell-forecast,
.night_mode .gpb-style-heatmap .gpb-hm-cell-forecast {
    background: #4e5050;
}
.nightMode .gpb-style-heatmap .gpb-hm-marker-badge,
.night_mode .gpb-style-heatmap .gpb-hm-marker-badge {
    background: rgba(49, 61, 69, 0.96);
    color: #e7ebf0;
}
.nightMode .gpb-style-heatmap .gpb-hm-marker-line,
.night_mode .gpb-style-heatmap .gpb-hm-marker-line {
    background: rgba(231, 235, 240, 0.62);
}
@media (max-width: 480px) {
    .gpb-milestone-date-full {
        display: none;
    }
    .gpb-milestone-date-short {
        display: inline;
    }
    .gpb-style-heatmap .gpb-hm-grid {
        gap: 2px;
    }
    .gpb-style-heatmap .gpb-hm-cell {
        height: 10px;
    }
    .gpb-style-heatmap .gpb-hm-marker-badge {
        font-size: 8px;
    }
}
</style>
"""


def _render_motivation_markup(text: str) -> str:
    if mw is not None and getattr(mw, "col", None) is not None:
        try:
            return mw.col.render_markdown(text, sanitize=False)
        except Exception:
            pass
    return escape(text).replace("\n", "<br>")

_MOTIVATION_SCRIPT = """
<script>
(function() {
    var wraps = document.querySelectorAll('.gpb-wrap');
    if (!wraps.length) {
        return;
    }
    var root = wraps[wraps.length - 1];
    var trigger = root.querySelector('[data-gpb-motivation-trigger]');
    var popup = root.querySelector('[data-gpb-motivation-popup]');
    if (!trigger || !popup) {
        return;
    }
    var closeControls = popup.querySelectorAll('[data-gpb-motivation-close]');

    function openPopup() {
        popup.hidden = false;
        trigger.setAttribute('aria-expanded', 'true');
    }

    function closePopup() {
        popup.hidden = true;
        trigger.setAttribute('aria-expanded', 'false');
        trigger.focus();
    }

    trigger.addEventListener('click', function() {
        if (popup.hidden) {
            openPopup();
        } else {
            closePopup();
        }
    });

    for (var i = 0; i < closeControls.length; i++) {
        closeControls[i].addEventListener('click', function() {
            closePopup();
        });
    }

    popup.addEventListener('click', function(event) {
        if (event.target === popup) {
            closePopup();
        }
    });

    document.addEventListener('keydown', function(event) {
        if (event.key === 'Escape' && !popup.hidden) {
            closePopup();
        }
    });
})();
</script>
"""

_CATCHUP_SCRIPT = """
<script>
(function() {
    var wraps = document.querySelectorAll('.gpb-wrap');
    if (!wraps.length) {
        return;
    }
    var root = wraps[wraps.length - 1];
    root.addEventListener('click', function(event) {
        var button = event.target.closest('[data-gpb-catchup-deck]');
        if (!button) {
            return;
        }
        var deckId = button.getAttribute('data-gpb-catchup-deck');
        var period = button.getAttribute('data-gpb-catchup-period');
        var amount = button.getAttribute('data-gpb-catchup-amount');
        pycmd('gpb_catchup:' + deckId + ':' + period + ':' + amount);
    });
})();
</script>
"""

_HEATMAP_MERGE_SCRIPT = """
<script>
(function() {
    var wraps = document.querySelectorAll('.gpb-wrap[data-visual-style="heatmap"]');
    if (!wraps.length) {
        return;
    }
    var root = wraps[wraps.length - 1];
    if (root._gpbHeatmapMergeInit) {
        return;
    }
    root._gpbHeatmapMergeInit = true;

    function clearSyncedClasses() {
        var classes = Array.prototype.slice.call(root.classList);
        for (var i = 0; i < classes.length; i++) {
            var name = classes[i];
            if (name.indexOf('gpb-rh-theme-') === 0 || name.indexOf('gpb-rh-mode-') === 0) {
                root.classList.remove(name);
            }
        }
    }

    function applyHeatmapClasses(heatmapRoot) {
        if (!heatmapRoot) {
            return false;
        }
        root.classList.add('gpb-rh-merged');
        clearSyncedClasses();
        var classNames = Array.prototype.slice.call(heatmapRoot.classList);
        for (var i = 0; i < classNames.length; i++) {
            var name = classNames[i];
            if (name.indexOf('rh-theme-') === 0 || name.indexOf('rh-mode-') === 0) {
                root.classList.add('gpb-' + name);
            }
        }
        return true;
    }

    function findHeatmapRoot() {
        return document.querySelector('.rh-container');
    }

    function syncFromCurrentHeatmap() {
        return applyHeatmapClasses(findHeatmapRoot());
    }

    syncFromCurrentHeatmap();

    var currentHeatmapRoot = findHeatmapRoot();
    if (currentHeatmapRoot && typeof MutationObserver !== 'undefined') {
        var heatmapClassObserver = new MutationObserver(function() {
            applyHeatmapClasses(currentHeatmapRoot);
        });
        heatmapClassObserver.observe(currentHeatmapRoot, {
            attributes: true,
            attributeFilter: ['class']
        });
    }

    if (typeof MutationObserver !== 'undefined') {
        var documentObserver = new MutationObserver(function() {
            var heatmapRoot = findHeatmapRoot();
            if (!heatmapRoot) {
                return;
            }
            applyHeatmapClasses(heatmapRoot);
            if (heatmapRoot !== currentHeatmapRoot) {
                currentHeatmapRoot = heatmapRoot;
                var observer = new MutationObserver(function() {
                    applyHeatmapClasses(heatmapRoot);
                });
                observer.observe(heatmapRoot, {
                    attributes: true,
                    attributeFilter: ['class']
                });
            }
        });
        documentObserver.observe(document.body, {
            childList: true,
            subtree: true
        });
    } else {
        var attempts = 0;
        var poll = setInterval(function() {
            attempts += 1;
            if (syncFromCurrentHeatmap() || attempts > 20) {
                clearInterval(poll);
            }
        }, 250);
    }
})();
</script>
"""

_CAROUSEL_SCRIPT = """
<script>
(function() {
    var wraps = document.querySelectorAll('.gpb-wrap[data-layout-mode="carousel"]');
    if (!wraps.length) {
        return;
    }
    var root = wraps[wraps.length - 1];
    var decks = root.querySelectorAll('.gpb-deck');
    for (var deckIdx = 0; deckIdx < decks.length; deckIdx++) {
        (function(deck) {
            var goals = deck.querySelectorAll('.gpb-goal');
            if (goals.length < 2) {
                return;
            }
            var deckId = deck.getAttribute('data-deck-id') || String(deckIdx);
            var storageKey = 'gpb-active-goal-index-' + deckId;
            var index = 0;
            try {
                index = parseInt(localStorage.getItem(storageKey) || '0', 10) || 0;
            } catch (err) {
                index = 0;
            }
            function render() {
                index = ((index % goals.length) + goals.length) % goals.length;
                for (var i = 0; i < goals.length; i++) {
                    if (i === index) {
                        goals[i].classList.remove('gpb-goal-hidden');
                    } else {
                        goals[i].classList.add('gpb-goal-hidden');
                    }
                }
                try {
                    localStorage.setItem(storageKey, String(index));
                } catch (err) {
                }
            }
            var prev = deck.querySelector('[data-gpb-prev]');
            var next = deck.querySelector('[data-gpb-next]');
            if (prev) {
                prev.addEventListener('click', function() {
                    index -= 1;
                    render();
                });
            }
            if (next) {
                next.addEventListener('click', function() {
                    index += 1;
                    render();
                });
            }
            render();
        })(decks[deckIdx]);
    }
})();
</script>
"""

def _render_empty_state(visual_style: str) -> str:
    wrap_classes = "gpb-wrap"
    if visual_style == "heatmap":
        wrap_classes += " gpb-style-heatmap"
    return f"""
{_STYLE_BLOCK}
<div class="{wrap_classes}" data-layout-mode="all" data-visual-style="{visual_style}">
    {_render_header("all", visual_style, 0, True, "One more session. Future you will be very impressed.")}
    <div class="gpb-widget">
        <div class="gpb-empty-title">Goal progress bars</div>
        <div class="gpb-empty-copy">
            Add one or more deck goal groups in this add-on&apos;s config to show weekly, monthly, and yearly progress here.
        </div>
    </div>
</div>
"""

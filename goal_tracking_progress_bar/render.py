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


def metric_label(metric: MetricType) -> str:
    return _METRIC_LABELS[metric]


def render_widget(payload: RenderPayload) -> str:
    if not payload.decks:
        return _EMPTY_STATE_HTML

    wrap_classes = "gpb-wrap"
    if payload.layout_mode == "carousel":
        wrap_classes += " gpb-wrap-carousel"

    deck_blocks = "\n".join(
        _render_deck(
            deck,
            payload.layout_mode,
            payload.show_brief_page,
            payload.show_brief_page_horizontal,
            payload.show_behind_pace,
            payload.show_streaks,
            payload.streak_display_mode,
            payload.show_rewards,
            payload.show_milestones,
            payload.milestone_display_mode,
        )
        for deck in payload.decks
    )
    scripts = [_MOTIVATION_SCRIPT]
    if payload.layout_mode == "carousel":
        scripts.append(_CAROUSEL_SCRIPT)
    script = "".join(scripts)

    return (
        f"{_STYLE_BLOCK}"
        f"<div class=\"{wrap_classes}\" data-layout-mode=\"{payload.layout_mode}\">"
        f"{_render_header(payload.layout_mode, len(payload.decks), payload.show_motivation, payload.motivation)}"
        f"<div class=\"gpb-decks\">{deck_blocks}</div>"
        f"</div>"
        f"{script}"
    )


def _render_deck(
    deck: DeckProgress,
    layout_mode: LayoutMode,
    show_brief_page: bool,
    show_brief_page_horizontal: bool,
    show_behind_pace: bool,
    show_streaks: bool,
    streak_display_mode: str,
    show_rewards: bool,
    show_milestones: bool,
    milestone_display_mode: str,
) -> str:
    use_brief_page = layout_mode == "carousel" and show_brief_page and len(deck.goals) > 1
    rows: list[str] = []
    if use_brief_page:
        rows.append(
            _render_brief_goal_page(
                deck.goals,
                show_brief_page_horizontal,
                show_milestones,
                milestone_display_mode,
            )
        )
    rows.extend(
        _render_goal(
            goal,
            layout_mode == "carousel",
            index == 0 and not use_brief_page,
            show_behind_pace,
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
    goal: GoalProgress,
    carousel_mode: bool,
    is_initial: bool,
    show_behind_pace: bool,
    show_streaks: bool,
    streak_display_mode: str,
    show_rewards: bool,
    show_milestones: bool,
) -> str:
    summary = f"{goal.current:,} / {goal.target:,} {goal.metric_label} {goal.label.lower()}"
    width = round(goal.ratio * 100, 1)
    expected_width = round(goal.expected_ratio * 100, 1)
    hidden_class = ""
    if carousel_mode and not is_initial:
        hidden_class = " gpb-goal-hidden"
    if show_milestones and goal.milestones:
        hidden_class += " gpb-goal-with-milestones"
    behind_note = ""
    behind_fill = ""
    if show_behind_pace and goal.behind_amount > 0:
        behind_note = (
            f'<div class="gpb-behind">Behind pace by '
            f'{goal.behind_amount:,} {escape(goal.metric_label)}</div>'
        )
        behind_fill = (
            f'<div class="gpb-behind-fill" style="left: {width}%; width: {max(0.0, expected_width - width)}%"></div>'
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
    milestone_strip = ""
    if show_milestones and goal.milestones:
        milestone_strip = _render_milestones(goal.milestones)

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
        <div class="gpb-meter" aria-label="{escape(summary)}">
            {behind_fill}
            <div class="gpb-fill" style="width: {width}%"></div>
            {milestone_strip}
        </div>
    </div>
    """


def _render_brief_goal_page(
    goals: tuple[GoalProgress, ...],
    horizontal: bool,
    show_milestones: bool,
    milestone_display_mode: str,
) -> str:
    brief_list_class = "gpb-brief-list gpb-brief-list-horizontal" if horizontal else "gpb-brief-list"
    rows = "".join(
        _render_brief_goal_row(goal, show_milestones, milestone_display_mode)
        for goal in goals
    )
    return f"""
    <div class="gpb-goal gpb-goal-brief">
        <div class="{brief_list_class}">{rows}</div>
    </div>
    """


def _render_brief_goal_row(
    goal: GoalProgress,
    show_milestones: bool,
    milestone_display_mode: str,
) -> str:
    summary = f"{goal.current:,}/{goal.target:,} {goal.metric_label}"
    width = round(goal.ratio * 100, 1)
    milestones = _brief_milestones(goal.milestones, milestone_display_mode) if show_milestones else ()
    milestone_strip = ""
    milestone_class = ""
    if milestones:
        milestone_strip = _render_milestones(milestones, compact=True)
        milestone_class = " gpb-brief-row-with-milestones"
    return f"""
    <div class="gpb-brief-row{milestone_class}">
        <div class="gpb-brief-top">
            <div class="gpb-brief-title">{escape(goal.label)}</div>
            <div class="gpb-brief-summary">{escape(summary)}</div>
        </div>
        <div class="gpb-meter gpb-meter-brief" aria-label="{escape(summary)}">
            <div class="gpb-fill" style="width: {width}%"></div>
            {milestone_strip}
        </div>
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


def _render_header(layout_mode: LayoutMode, deck_count: int, show_motivation: bool, motivation: str) -> str:
    count = f"<div class=\"gpb-count\">{deck_count} deck{'s' if deck_count != 1 else ''}</div>"
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
            <div class="gpb-heading">Goal progress</div>
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
    position: relative;
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
    white-space: nowrap;
    vertical-align: top;
    transition: max-width 180ms ease, background 180ms ease, border-color 180ms ease;
}
.gpb-reward-badge:hover,
.gpb-reward-badge:focus-visible {
    max-width: 100%;
}
.gpb-reward-emoji {
    flex: 0 0 auto;
}
.gpb-reward-level {
    flex: 0 0 auto;
}
.gpb-reward-detail {
    position: absolute;
    top: calc(100% + 6px);
    left: 0;
    width: max-content;
    max-width: min(320px, calc(100vw - 48px));
    padding: 7px 9px;
    border: 1px solid var(--gpb-border);
    border-radius: 10px;
    background: var(--canvas, rgba(255, 255, 255, 0.98));
    box-shadow: 0 10px 22px rgba(0, 0, 0, 0.12);
    white-space: normal;
    line-height: 1.4;
    z-index: 5;
    opacity: 0;
    visibility: hidden;
    transform: translateY(-2px);
    pointer-events: none;
    transition: opacity 180ms ease, transform 180ms ease, visibility 180ms ease;
}
.gpb-reward-badge:hover .gpb-reward-detail,
.gpb-reward-badge:focus-visible .gpb-reward-detail {
    opacity: 1;
    visibility: visible;
    transform: translateY(0);
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
    color: rgba(183, 76, 76, 0.82);
    font-size: 11px;
    line-height: 1.3;
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
@media (max-width: 480px) {
    .gpb-milestone-date-full {
        display: none;
    }
    .gpb-milestone-date-short {
        display: inline;
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

_EMPTY_STATE_HTML = f"""
{_STYLE_BLOCK}
<div class="gpb-wrap">
    {_render_header("all", 0, True, "One more session. Future you will be very impressed.")}
    <div class="gpb-widget">
        <div class="gpb-empty-title">Goal progress bars</div>
        <div class="gpb-empty-copy">
            Add one or more deck goal groups in this add-on&apos;s config to show weekly, monthly, and yearly progress here.
        </div>
    </div>
</div>
"""

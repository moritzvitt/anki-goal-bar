from __future__ import annotations

from html import escape

from .config import LayoutMode, MetricType
from .models import DeckProgress, GoalMilestone, GoalProgress, RenderPayload

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
            payload.show_behind_pace,
            payload.show_rewards,
            payload.show_milestones,
        )
        for deck in payload.decks
    )
    script = _CAROUSEL_SCRIPT if payload.layout_mode == "carousel" else ""

    return (
        f"{_STYLE_BLOCK}"
        f"<div class=\"{wrap_classes}\" data-layout-mode=\"{payload.layout_mode}\">"
        f"{_render_header(payload.layout_mode, len(payload.decks))}"
        f"<div class=\"gpb-decks\">{deck_blocks}</div>"
        f"</div>"
        f"{script}"
    )


def _render_deck(
    deck: DeckProgress,
    layout_mode: LayoutMode,
    show_behind_pace: bool,
    show_rewards: bool,
    show_milestones: bool,
) -> str:
    rows = "\n".join(
        _render_goal(
            goal,
            layout_mode == "carousel",
            index == 0,
            show_behind_pace,
            show_rewards,
            show_milestones,
        )
        for index, goal in enumerate(deck.goals)
    )
    controls = ""
    if layout_mode == "carousel" and len(deck.goals) > 1:
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
        {rows}
    </div>
    """


def _render_goal(
    goal: GoalProgress,
    carousel_mode: bool,
    is_initial: bool,
    show_behind_pace: bool,
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
        {reward_badge}
        {behind_note}
        <div class="gpb-meter" aria-label="{escape(summary)}">
            {behind_fill}
            <div class="gpb-fill" style="width: {width}%"></div>
            {milestone_strip}
        </div>
    </div>
    """


def _render_milestones(milestones: tuple[GoalMilestone, ...]) -> str:
    markers = []
    for milestone in milestones:
        position = round(milestone.ratio * 100, 1)
        label = escape(milestone.label)
        short_date = escape(milestone.short_date_label)
        full_date = escape(milestone.full_date_label)
        title = escape(f"{milestone.label}: {milestone.full_date_label}")
        markers.append(
            f"""
            <div class="gpb-milestone" style="left: {position}%;" title="{title}" aria-label="{title}">
                <span class="gpb-milestone-line" aria-hidden="true"></span>
                <span class="gpb-milestone-badge">
                    <span class="gpb-milestone-label">{label}</span>
                    <span class="gpb-milestone-date gpb-milestone-date-full">{full_date}</span>
                    <span class="gpb-milestone-date gpb-milestone-date-short">{short_date}</span>
                </span>
            </div>
            """
        )
    return f'<div class="gpb-milestones">{"".join(markers)}</div>'


def _render_header(layout_mode: LayoutMode, deck_count: int) -> str:
    count = f"<div class=\"gpb-count\">{deck_count} deck{'s' if deck_count != 1 else ''}</div>"
    return f"""
    <div class="gpb-toolbar">
        <div class="gpb-heading-wrap">
            <div class="gpb-heading">Goal progress</div>
            {count}
        </div>
        <div class="gpb-controls">
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
    max-width: 100%;
}
.gpb-reward-emoji {
    flex: 0 0 auto;
}
.gpb-reward-level {
    flex: 0 0 auto;
}
.gpb-reward-detail {
    max-width: 0;
    overflow: hidden;
    opacity: 0;
    transition: max-width 180ms ease, opacity 180ms ease;
}
.gpb-reward-badge:hover .gpb-reward-detail,
.gpb-reward-badge:focus-visible .gpb-reward-detail {
    max-width: 320px;
    opacity: 1;
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
.nightMode .gpb-milestone-line,
.night_mode .gpb-milestone-line {
    background: rgba(231, 235, 240, 0.6);
}
.nightMode .gpb-milestone-badge,
.night_mode .gpb-milestone-badge {
    background: rgba(49, 61, 69, 0.94);
    box-shadow: 0 1px 2px rgba(0, 0, 0, 0.3);
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
    {_render_header("all", 0)}
    <div class="gpb-widget">
        <div class="gpb-empty-title">Goal progress bars</div>
        <div class="gpb-empty-copy">
            Add one or more deck goal groups in this add-on&apos;s config to show weekly, monthly, and yearly progress here.
        </div>
    </div>
</div>
"""

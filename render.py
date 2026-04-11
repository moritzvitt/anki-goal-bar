from __future__ import annotations

from html import escape

from .config import LayoutMode, MetricType
from .models import DeckProgress, GoalProgress, RenderPayload

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
    if payload.layout_mode == "carousel" and len(payload.decks) > 1:
        wrap_classes += " gpb-wrap-carousel"

    deck_blocks = "\n".join(
        _render_deck(deck, payload.layout_mode, index == 0)
        for index, deck in enumerate(payload.decks)
    )
    script = _CAROUSEL_SCRIPT if payload.layout_mode == "carousel" and len(payload.decks) > 1 else ""

    return (
        f"{_STYLE_BLOCK}"
        f"<div class=\"{wrap_classes}\" data-layout-mode=\"{payload.layout_mode}\">"
        f"{_render_header(payload.layout_mode, len(payload.decks))}"
        f"<div class=\"gpb-decks\">{deck_blocks}</div>"
        f"</div>"
        f"{script}"
    )


def _render_deck(deck: DeckProgress, layout_mode: LayoutMode, is_initial: bool) -> str:
    rows = "\n".join(_render_goal(goal) for goal in deck.goals)
    hidden_class = ""
    if layout_mode == "carousel" and not is_initial:
        hidden_class = " gpb-deck-hidden"

    return f"""
    <div class="gpb-widget gpb-deck{hidden_class}" data-deck-index="{deck.deck_id}">
        <div class="gpb-deck-title">{escape(deck.deck_name)}</div>
        {rows}
    </div>
    """


def _render_goal(goal: GoalProgress) -> str:
    summary = f"{goal.current:,} / {goal.target:,} {goal.metric_label} {goal.label.lower()}"
    width = round(goal.ratio * 100, 1)

    return f"""
    <div class="gpb-goal">
        <div class="gpb-header">
            <div class="gpb-title">{escape(goal.label)}</div>
            <div class="gpb-percent">{goal.percent}%</div>
        </div>
        <div class="gpb-summary">{escape(summary)}</div>
        <div class="gpb-meter" aria-label="{escape(summary)}">
            <div class="gpb-fill" style="width: {width}%"></div>
        </div>
    </div>
    """


def _render_header(layout_mode: LayoutMode, deck_count: int) -> str:
    count = f"<div class=\"gpb-count\">{deck_count} deck{'s' if deck_count != 1 else ''}</div>"
    cycle = ""
    if layout_mode == "carousel" and deck_count > 1:
        cycle = """
        <button class="gpb-cycle hm-btn-like" data-gpb-prev title="Previous deck" aria-label="Previous deck">‹</button>
        <button class="gpb-cycle hm-btn-like" data-gpb-next title="Next deck" aria-label="Next deck">›</button>
        """

    return f"""
    <div class="gpb-toolbar">
        <div class="gpb-heading-wrap">
            <div class="gpb-heading">Goal progress</div>
            {count}
        </div>
        <div class="gpb-controls">
            {cycle}
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
.gpb-deck-hidden {
    display: none;
}
.gpb-deck-title {
    color: var(--gpb-text);
    font-size: 14px;
    font-weight: 700;
    margin-bottom: 8px;
}
.gpb-goal + .gpb-goal {
    margin-top: 10px;
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
.gpb-meter {
    margin-top: 7px;
    height: 8px;
    border-radius: 999px;
    overflow: hidden;
    background: var(--gpb-bg);
}
.gpb-fill {
    height: 100%;
    min-width: 0;
    border-radius: 999px;
    background: linear-gradient(90deg, var(--gpb-fill-start), var(--gpb-fill-end));
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
    if (decks.length < 2) {
        return;
    }
    var storageKey = 'gpb-active-deck-index';
    var index = 0;
    try {
        index = parseInt(localStorage.getItem(storageKey) || '0', 10) || 0;
    } catch (err) {
        index = 0;
    }
    function render() {
        index = ((index % decks.length) + decks.length) % decks.length;
        for (var i = 0; i < decks.length; i++) {
            decks[i].style.display = i === index ? '' : 'none';
        }
        try {
            localStorage.setItem(storageKey, String(index));
        } catch (err) {
        }
    }
    var prev = root.querySelector('[data-gpb-prev]');
    var next = root.querySelector('[data-gpb-next]');
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

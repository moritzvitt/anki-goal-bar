from __future__ import annotations

from html import escape

from .config import MetricType
from .models import GoalProgress

_METRIC_LABELS: dict[MetricType, str] = {
    "reviews": "reviews",
    "new_cards": "new cards",
    "study_minutes": "minutes",
}


def metric_label(metric: MetricType) -> str:
    return _METRIC_LABELS[metric]


def render_widget(goals: list[GoalProgress]) -> str:
    if not goals:
        return _EMPTY_STATE_HTML

    rows = "\n".join(_render_goal(goal) for goal in goals)
    return f"{_STYLE_BLOCK}<div class=\"gpb-widget\">{_render_header()}{rows}</div>"


def _render_goal(goal: GoalProgress) -> str:
    summary = (
        f"{goal.current:,} / {goal.target:,} {goal.metric_label} {goal.label.lower()}"
    )
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


def _render_header() -> str:
    return """
    <div class="gpb-toolbar">
        <div class="gpb-heading">Goal progress</div>
        <button class="gpb-config" onclick="pycmd('gpb_config'); return false;" title="Configure goals">
            Config
        </button>
    </div>
    """


_STYLE_BLOCK = """
<style>
.gpb-widget {
    --gpb-border: rgba(0, 0, 0, 0.12);
    --gpb-text: var(--fg, #2f3742);
    --gpb-muted: rgba(47, 55, 66, 0.72);
    --gpb-bg: rgba(127, 140, 153, 0.12);
    --gpb-fill-start: #70b77e;
    --gpb-fill-end: #4f9d69;
    margin: 14px auto 0;
    max-width: 520px;
    padding: 10px 12px;
    border: 1px solid var(--gpb-border);
    border-radius: 10px;
    background: var(--canvas, rgba(255, 255, 255, 0.78));
    text-align: left;
    box-sizing: border-box;
}
.gpb-toolbar {
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 12px;
    margin-bottom: 4px;
}
.gpb-heading {
    color: var(--gpb-text);
    font-size: 13px;
    font-weight: 700;
    letter-spacing: 0.01em;
}
.gpb-config {
    border: 1px solid var(--gpb-border);
    border-radius: 999px;
    background: transparent;
    color: var(--gpb-muted);
    font-size: 11px;
    font-weight: 600;
    padding: 2px 8px;
    cursor: pointer;
}
.gpb-config:hover {
    color: var(--gpb-text);
}
.nightMode .gpb-widget {
    --gpb-border: rgba(255, 255, 255, 0.1);
    --gpb-text: #e7ebf0;
    --gpb-muted: rgba(231, 235, 240, 0.72);
    --gpb-bg: rgba(255, 255, 255, 0.08);
    background: rgba(255, 255, 255, 0.04);
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
</style>
"""

_EMPTY_STATE_HTML = f"""
{_STYLE_BLOCK}
<div class="gpb-widget">
    {_render_header()}
    <div class="gpb-empty-title">Goal progress bars</div>
    <div class="gpb-empty-copy">
        Enable a weekly, monthly, or yearly goal in this add-on&apos;s config to show progress here.
    </div>
</div>
"""

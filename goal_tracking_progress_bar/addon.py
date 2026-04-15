from __future__ import annotations

from dataclasses import replace
from datetime import datetime

from aqt import gui_hooks, mw
from aqt.qt import QTimer
from aqt.utils import showInfo

from .config import (
    export_config,
    is_review_heatmap_available,
    load_config,
    monthly_goal_celebration_token,
)
from .config_dialog import open_config_dialog, try_handle_js_message
from .. import shared_menu
from .service import GoalProgressService


_service: GoalProgressService | None = None
_announcement_scheduled = False
_monthly_goal_celebration_scheduled_for: str | None = None
ADDON_MENU_NAME = "Goal Tracking Progress Bar"
HEATMAP_ANNOUNCEMENT_ID = "review-heatmap-design-2026-04"


def _render_home_widget(deck_browser, content) -> None:
    if mw is None or mw.col is None or _service is None:
        return

    result = _service.render_result()
    content.stats += result.html
    _maybe_schedule_heatmap_announcement()
    _maybe_schedule_monthly_goal_celebration(result.monthly_goal_reached_today)


def register() -> None:
    global _service

    if mw is None:
        return

    shared_menu.add_action_to_addon_menu(
        addon_name=ADDON_MENU_NAME,
        action_text="Settings",
        callback=open_config_dialog,
    )
    _service = GoalProgressService(mw, load_config)
    gui_hooks.deck_browser_will_render_content.append(_render_home_widget)
    gui_hooks.webview_did_receive_js_message.append(try_handle_js_message)
    mw.addonManager.setConfigAction(__name__, open_config_dialog)


def _maybe_schedule_heatmap_announcement() -> None:
    global _announcement_scheduled

    if _announcement_scheduled or mw is None or mw.col is None:
        return

    config = load_config()
    if HEATMAP_ANNOUNCEMENT_ID in config.seen_announcements:
        return

    _announcement_scheduled = True
    QTimer.singleShot(0, _show_heatmap_announcement)


def _show_heatmap_announcement() -> None:
    if mw is None:
        return

    config = load_config()
    if HEATMAP_ANNOUNCEMENT_ID in config.seen_announcements:
        return

    addon_name = __name__.split(".", 1)[0]
    message = (
        "Goal Progress Bar has a new Review Heatmap-inspired visual style.\n\n"
        "You can try it in Settings -> General -> Visual style -> Goal bar style."
    )
    if is_review_heatmap_available():
        message += (
            "\n\nReview Heatmap is installed, so this design can also borrow its theme colors "
            "and is used automatically for untouched configs."
        )

    showInfo(message, title="Try The New Heatmap Design", parent=mw)

    updated = replace(
        config,
        seen_announcements=(*config.seen_announcements, HEATMAP_ANNOUNCEMENT_ID),
    )
    mw.addonManager.writeConfig(addon_name, export_config(updated))


def _maybe_schedule_monthly_goal_celebration(reached_today: bool) -> None:
    global _monthly_goal_celebration_scheduled_for

    if not reached_today or mw is None or mw.col is None:
        return

    today = datetime.now().astimezone().date()
    celebration_token = monthly_goal_celebration_token(today)
    config = load_config()
    if celebration_token in config.seen_announcements:
        return
    if _monthly_goal_celebration_scheduled_for == today.isoformat():
        return

    _monthly_goal_celebration_scheduled_for = today.isoformat()
    QTimer.singleShot(0, _show_monthly_goal_celebration)


def _show_monthly_goal_celebration() -> None:
    global _monthly_goal_celebration_scheduled_for

    if mw is None:
        return

    today = datetime.now().astimezone().date()
    celebration_token = monthly_goal_celebration_token(today)
    config = load_config()
    if celebration_token in config.seen_announcements:
        _monthly_goal_celebration_scheduled_for = None
        return

    showInfo(
        "Congrats on reaching your monthly goal! 🦄",
        title="Monthly Goal Complete",
        parent=mw,
    )
    updated = replace(
        config,
        seen_announcements=(*config.seen_announcements, celebration_token),
    )
    mw.addonManager.writeConfig(__name__.split(".", 1)[0], export_config(updated))
    _monthly_goal_celebration_scheduled_for = None

from __future__ import annotations

from dataclasses import replace

from aqt import gui_hooks, mw
from aqt.qt import QTimer
from aqt.utils import showInfo

from .config import export_config, is_review_heatmap_available, load_config
from .config_dialog import open_config_dialog, try_handle_js_message
from .. import shared_menu
from .service import GoalProgressService


_service: GoalProgressService | None = None
_announcement_scheduled = False
ADDON_MENU_NAME = "Goal Tracking Progress Bar"
HEATMAP_ANNOUNCEMENT_ID = "review-heatmap-design-2026-04"


def _render_home_widget(deck_browser, content) -> None:
    if mw is None or mw.col is None or _service is None:
        return

    content.stats += _service.render_widget()
    _maybe_schedule_heatmap_announcement()


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

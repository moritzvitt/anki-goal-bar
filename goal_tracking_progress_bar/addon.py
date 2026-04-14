from __future__ import annotations

from aqt import gui_hooks, mw

from .config import load_config
from .config_dialog import open_config_dialog, try_handle_js_message
from .. import shared_menu
from .service import GoalProgressService


_service: GoalProgressService | None = None
ADDON_MENU_NAME = "Goal Progress Bar"


def _render_home_widget(deck_browser, content) -> None:
    if mw is None or mw.col is None or _service is None:
        return

    content.stats += _service.render_widget()


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

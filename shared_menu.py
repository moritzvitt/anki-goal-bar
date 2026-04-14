from __future__ import annotations

"""
Shared menu utility for Moritz add-ons.

Copy this file into each add-on that should contribute entries to the shared
"Moritz Add-ons" top-level menu. The menu is discovered and cached on `mw`,
so separate installed add-ons can cooperate without importing one another.
"""

from typing import Callable

from aqt import mw
from aqt.qt import QAction, QMenu

SHARED_MENU_ATTR = "_moritz_addons_menu"
SHARED_SUBMENUS_ATTR = "_moritz_addons_submenus"
SHARED_MENU_OBJECT_NAME = "moritz_addons_menu"
SHARED_MENU_TITLE = "Moritz Add-ons"


def _require_main_window():
    if mw is None:
        raise RuntimeError("Anki main window is not available yet.")
    return mw


def _normalize_menu_text(text: str) -> str:
    return text.replace("&", "").strip()


def _menu_bar():
    main_window = _require_main_window()

    if hasattr(main_window, "menuBar"):
        menu_bar = main_window.menuBar()
        if menu_bar is not None:
            return menu_bar

    menu_bar = getattr(getattr(main_window, "form", None), "menubar", None)
    if menu_bar is not None:
        return menu_bar

    menu_tools = getattr(getattr(main_window, "form", None), "menuTools", None)
    if menu_tools is not None and hasattr(menu_tools, "parentWidget"):
        parent = menu_tools.parentWidget()
        if parent is not None:
            return parent

    raise RuntimeError("Could not find Anki's main menu bar.")


def _find_menu_by_title(menu_bar, title: str) -> QMenu | None:
    normalized_title = _normalize_menu_text(title)
    for action in menu_bar.actions():
        menu = action.menu()
        if menu is None:
            continue
        if _normalize_menu_text(menu.title()) == normalized_title:
            return menu
    return None


def _find_tools_action(menu_bar):
    for action in menu_bar.actions():
        menu = action.menu()
        label = menu.title() if menu is not None else action.text()
        if _normalize_menu_text(label) == "Tools":
            return action
    return None


def _cache_shared_menu(shared_menu: QMenu) -> QMenu:
    main_window = _require_main_window()
    setattr(main_window, SHARED_MENU_ATTR, shared_menu)
    return shared_menu


def _insert_shared_menu(menu_bar, shared_menu: QMenu) -> None:
    tools_action = _find_tools_action(menu_bar)
    if tools_action is None:
        menu_bar.addMenu(shared_menu)
        return

    actions = menu_bar.actions()
    try:
        tools_index = actions.index(tools_action)
    except ValueError:
        menu_bar.addMenu(shared_menu)
        return

    insert_before = actions[tools_index + 1] if tools_index + 1 < len(actions) else None
    if insert_before is None:
        menu_bar.addMenu(shared_menu)
    else:
        menu_bar.insertMenu(insert_before, shared_menu)


def get_shared_menu() -> QMenu:
    """
    Return the shared top-level "Moritz Add-ons" menu.

    Reuses, in order:
    1. `mw._moritz_addons_menu` if already cached
    2. an existing menu bar entry titled "Moritz Add-ons"
    3. a newly created top-level menu inserted next to Tools
    """
    main_window = _require_main_window()

    existing = getattr(main_window, SHARED_MENU_ATTR, None)
    if isinstance(existing, QMenu):
        return existing

    menu_bar = _menu_bar()
    existing = _find_menu_by_title(menu_bar, SHARED_MENU_TITLE)
    if existing is not None:
        return _cache_shared_menu(existing)

    shared_menu = QMenu(SHARED_MENU_TITLE, main_window)
    shared_menu.setObjectName(SHARED_MENU_OBJECT_NAME)
    _insert_shared_menu(menu_bar, shared_menu)
    return _cache_shared_menu(shared_menu)


def _submenu_cache() -> dict[str, QMenu]:
    main_window = _require_main_window()
    cache = getattr(main_window, SHARED_SUBMENUS_ATTR, None)
    if isinstance(cache, dict):
        return cache
    cache = {}
    setattr(main_window, SHARED_SUBMENUS_ATTR, cache)
    return cache


def get_addon_submenu(addon_name: str) -> QMenu:
    """
    Return the submenu for one add-on under the shared top-level menu.
    """
    cache = _submenu_cache()
    cached = cache.get(addon_name)
    if isinstance(cached, QMenu):
        return cached

    parent_menu = get_shared_menu()
    normalized_name = _normalize_menu_text(addon_name)

    for action in parent_menu.actions():
        submenu = action.menu()
        if submenu is None:
            continue
        if _normalize_menu_text(submenu.title()) == normalized_name:
            cache[addon_name] = submenu
            return submenu

    submenu = parent_menu.addMenu(addon_name)
    cache[addon_name] = submenu
    return submenu


def add_action_to_addon_menu(
    addon_name: str,
    action_text: str,
    callback: Callable[[], None],
    icon=None,
) -> QAction:
    """
    Create and add one action under an add-on submenu.
    """
    submenu = get_addon_submenu(addon_name)
    action = QAction(action_text, submenu)
    if icon is not None:
        action.setIcon(icon)
    action.triggered.connect(callback)
    submenu.addAction(action)
    return action


def add_separator_to_addon_menu(addon_name: str) -> None:
    """
    Add a separator inside an add-on submenu.
    """
    get_addon_submenu(addon_name).addSeparator()

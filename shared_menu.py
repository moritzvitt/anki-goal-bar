from __future__ import annotations

"""
Shared menu utility for Moritz add-ons.

Copy this file into each add-on that should contribute entries to the shared
"Moritz Add-ons" top-level menu. The menu is discovered and cached on `mw`,
so separate installed add-ons can cooperate without importing one another.
"""

import json
from pathlib import Path
from typing import Callable

from aqt import mw
from aqt.qt import (
    QAbstractItemView,
    QAction,
    QDesktopServices,
    QDialog,
    QDialogButtonBox,
    QMenu,
    Qt,
    QTreeWidget,
    QTreeWidgetItem,
    QUrl,
    QVBoxLayout,
)
from aqt.utils import showInfo

SHARED_MENU_ATTR = "_moritz_addons_menu"
SHARED_SUBMENUS_ATTR = "_moritz_addons_submenus"
SHARED_MENU_OBJECT_NAME = "moritz_addons_menu"
SHARED_BROWSER_MENU_ATTR = "_moritz_addons_browser_menu"
SHARED_BROWSER_SUBMENUS_ATTR = "_moritz_addons_browser_submenus"
SHARED_BROWSER_MENU_OBJECT_NAME = "moritz_addons_browser_menu"
SHARED_MENU_TITLE = "Moritz Add-ons"
SHARED_RATE_ACTION_ATTR = "_moritz_addons_rate_action"
SHARED_RATING_TARGETS_ATTR = "_moritz_addons_rating_targets"
RATE_ME_LABEL = "Rate me"


def _require_main_window():
    if mw is None:
        raise RuntimeError("Anki main window is not available yet.")
    return mw


def _normalize_menu_text(text: str) -> str:
    return text.replace("&", "").strip()


def _window_menu_bar(window):
    if hasattr(window, "menuBar"):
        menu_bar = window.menuBar()
        if menu_bar is not None:
            return menu_bar

    menu_bar = getattr(getattr(window, "form", None), "menubar", None)
    if menu_bar is not None:
        return menu_bar

    menu_tools = getattr(getattr(window, "form", None), "menuTools", None)
    if menu_tools is not None and hasattr(menu_tools, "parentWidget"):
        parent = menu_tools.parentWidget()
        if parent is not None:
            return parent

    raise RuntimeError("Could not find a menu bar for this Anki window.")


def _menu_bar():
    return _window_menu_bar(_require_main_window())


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


def _cache_browser_shared_menu(browser, shared_menu: QMenu) -> QMenu:
    setattr(browser, SHARED_BROWSER_MENU_ATTR, shared_menu)
    return shared_menu


def _rating_registry() -> dict[str, str | None]:
    main_window = _require_main_window()
    registry = getattr(main_window, SHARED_RATING_TARGETS_ATTR, None)
    if isinstance(registry, dict):
        return registry
    registry = {}
    setattr(main_window, SHARED_RATING_TARGETS_ATTR, registry)
    return registry


def _read_local_ankiweb_target() -> tuple[str, str | None] | None:
    path = Path(__file__).resolve().with_name("ankiweb.json")
    if not path.exists():
        return None
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return None
    addon_id = str(raw.get("ankiweb_id") or "").strip()
    title = str(raw.get("title") or "").strip()
    if not title:
        return None
    url = f"https://ankiweb.net/shared/info/{addon_id}" if addon_id else None
    return title, url


def _register_local_rating_target() -> None:
    target = _read_local_ankiweb_target()
    if target is None:
        return
    title, url = target
    _rating_registry()[title] = url


def _rating_targets() -> list[tuple[str, str | None]]:
    _register_local_rating_target()
    registry = _rating_registry()
    return sorted((title, url) for title, url in registry.items())


def _open_rating_url(url: str) -> None:
    QDesktopServices.openUrl(QUrl(url))


def _open_rate_me_dialog() -> None:
    targets = _rating_targets()
    if not targets:
        showInfo(
            "No Moritz add-on is currently registered in this session.",
            parent=_require_main_window(),
        )
        return
    dialog = _RateMeDialog(targets, _require_main_window())
    if dialog.exec() != int(QDialog.DialogCode.Accepted):
        return
    selected_url = dialog.selected_url()
    if not selected_url:
        return
    _open_rating_url(selected_url)


class _RateMeDialog(QDialog):
    def __init__(self, targets: list[tuple[str, str | None]], parent) -> None:
        super().__init__(parent)
        self.setWindowTitle(RATE_ME_LABEL)
        self.setModal(True)
        self.resize(440, 360)

        layout = QVBoxLayout(self)
        self._tree = QTreeWidget(self)
        self._tree.setHeaderHidden(True)
        self._tree.setRootIsDecorated(True)
        self._tree.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self._tree.itemDoubleClicked.connect(self._accept_if_rateable)
        layout.addWidget(self._tree)

        available_root = QTreeWidgetItem(["Available on AnkiWeb"])
        unavailable_root = QTreeWidgetItem(["Installed, but not on AnkiWeb yet"])
        available_root.setFlags(available_root.flags() & ~Qt.ItemFlag.ItemIsSelectable)
        unavailable_root.setFlags(unavailable_root.flags() & ~Qt.ItemFlag.ItemIsSelectable)

        first_selectable: QTreeWidgetItem | None = None
        for title, url in targets:
            item = QTreeWidgetItem([title])
            if url:
                item.setData(0, Qt.ItemDataRole.UserRole, url)
                item.setToolTip(0, f"Open {title} on AnkiWeb")
                available_root.addChild(item)
                if first_selectable is None:
                    first_selectable = item
            else:
                item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsSelectable)
                item.setToolTip(0, f"{title} does not have an AnkiWeb page configured yet.")
                unavailable_root.addChild(item)

        if available_root.childCount():
            self._tree.addTopLevelItem(available_root)
            available_root.setExpanded(True)
        if unavailable_root.childCount():
            self._tree.addTopLevelItem(unavailable_root)
            unavailable_root.setExpanded(True)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Cancel | QDialogButtonBox.StandardButton.Ok,
            parent=self,
        )
        self._ok_button = buttons.button(QDialogButtonBox.StandardButton.Ok)
        self._ok_button.setText("Open AnkiWeb Page")
        self._ok_button.clicked.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

        self._tree.currentItemChanged.connect(self._sync_ok_state)
        if first_selectable is not None:
            self._tree.setCurrentItem(first_selectable)
        self._sync_ok_state()

    def selected_url(self) -> str | None:
        item = self._tree.currentItem()
        if item is None:
            return None
        data = item.data(0, Qt.ItemDataRole.UserRole)
        return str(data) if data else None

    def accept(self) -> None:
        if not self.selected_url():
            return
        super().accept()

    def _sync_ok_state(self, *_args) -> None:
        self._ok_button.setEnabled(bool(self.selected_url()))

    def _accept_if_rateable(self, item: QTreeWidgetItem) -> None:
        if item.data(0, Qt.ItemDataRole.UserRole):
            self.accept()


def _ensure_rate_me_action(menu: QMenu) -> None:
    main_window = _require_main_window()
    existing = getattr(main_window, SHARED_RATE_ACTION_ATTR, None)
    if isinstance(existing, QAction):
        return
    for action in menu.actions():
        if action.menu() is None and _normalize_menu_text(action.text()) == RATE_ME_LABEL:
            setattr(main_window, SHARED_RATE_ACTION_ATTR, action)
            return
    action = QAction(RATE_ME_LABEL, menu)
    action.triggered.connect(_open_rate_me_dialog)
    menu.addAction(action)
    menu.addSeparator()
    setattr(main_window, SHARED_RATE_ACTION_ATTR, action)


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


def _insert_shared_browser_menu(menu_bar, shared_menu: QMenu) -> None:
    _insert_shared_menu(menu_bar, shared_menu)


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
        _ensure_rate_me_action(existing)
        return existing

    menu_bar = _menu_bar()
    existing = _find_menu_by_title(menu_bar, SHARED_MENU_TITLE)
    if existing is not None:
        _ensure_rate_me_action(existing)
        return _cache_shared_menu(existing)

    shared_menu = QMenu(SHARED_MENU_TITLE, main_window)
    shared_menu.setObjectName(SHARED_MENU_OBJECT_NAME)
    _ensure_rate_me_action(shared_menu)
    _insert_shared_menu(menu_bar, shared_menu)
    return _cache_shared_menu(shared_menu)


def get_browser_shared_menu(browser) -> QMenu:
    """
    Return the shared top-level "Moritz Add-ons" menu for one Browser window.
    """
    existing = getattr(browser, SHARED_BROWSER_MENU_ATTR, None)
    if isinstance(existing, QMenu):
        return existing

    menu_bar = _window_menu_bar(browser)
    existing = _find_menu_by_title(menu_bar, SHARED_MENU_TITLE)
    if existing is not None:
        return _cache_browser_shared_menu(browser, existing)

    shared_menu = QMenu(SHARED_MENU_TITLE, browser)
    shared_menu.setObjectName(SHARED_BROWSER_MENU_OBJECT_NAME)
    _insert_shared_browser_menu(menu_bar, shared_menu)
    return _cache_browser_shared_menu(browser, shared_menu)


def _submenu_cache() -> dict[str, QMenu]:
    main_window = _require_main_window()
    cache = getattr(main_window, SHARED_SUBMENUS_ATTR, None)
    if isinstance(cache, dict):
        return cache
    cache = {}
    setattr(main_window, SHARED_SUBMENUS_ATTR, cache)
    return cache


def _browser_submenu_cache(browser) -> dict[str, QMenu]:
    cache = getattr(browser, SHARED_BROWSER_SUBMENUS_ATTR, None)
    if isinstance(cache, dict):
        return cache
    cache = {}
    setattr(browser, SHARED_BROWSER_SUBMENUS_ATTR, cache)
    return cache


def get_addon_submenu(addon_name: str) -> QMenu:
    """
    Return the submenu for one add-on under the shared top-level menu.
    """
    _register_local_rating_target()
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


def get_browser_addon_submenu(browser, addon_name: str) -> QMenu:
    """
    Return the submenu for one add-on under the Browser shared top-level menu.
    """
    _register_local_rating_target()
    cache = _browser_submenu_cache(browser)
    cached = cache.get(addon_name)
    if isinstance(cached, QMenu):
        return cached

    parent_menu = get_browser_shared_menu(browser)
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


def add_action_to_browser_addon_menu(
    browser,
    addon_name: str,
    action_text: str,
    callback: Callable[[], None],
    icon=None,
) -> QAction:
    """
    Create and add one action under an add-on submenu in the Browser shared menu.
    """
    submenu = get_browser_addon_submenu(browser, addon_name)
    action = QAction(action_text, submenu)
    if icon is not None:
        action.setIcon(icon)
    action.triggered.connect(callback)
    submenu.addAction(action)
    return action


def add_separator_to_browser_addon_menu(browser, addon_name: str) -> None:
    """
    Add a separator inside an add-on submenu in the Browser shared menu.
    """
    get_browser_addon_submenu(browser, addon_name).addSeparator()

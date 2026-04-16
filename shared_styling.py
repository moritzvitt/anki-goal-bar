from __future__ import annotations

from aqt import mw
from aqt.qt import (
    QColor,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QPalette,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

GLOBAL_STYLING_THEME_CHOICE_ATTR = "_moritz_global_styling_theme_choice"
GLOBAL_GAMIFICATION_CHOICE_ATTR = "_moritz_global_gamification_choice"
GLOBAL_STYLING_OPEN_SETTINGS_ATTR = "_moritz_global_styling_open_settings"

GAMIFICATION_LABELS = {
    "zero": "Zero gamification",
    "little_bit": "little bit",
    "half": "gamification 50%",
    "seventy": "70%",
    "all_in": "I am only here for the fun so might as well go all in",
}


def _hex(color: QColor) -> str:
    return color.name(QColor.NameFormat.HexRgb)


def _alpha(color: QColor, alpha: float) -> str:
    tinted = QColor(color)
    tinted.setAlphaF(max(0.0, min(1.0, alpha)))
    return tinted.name(QColor.NameFormat.HexArgb)


def _blend(first: QColor, second: QColor, ratio: float) -> QColor:
    ratio = max(0.0, min(1.0, ratio))
    inverse = 1.0 - ratio
    return QColor(
        round(first.red() * inverse + second.red() * ratio),
        round(first.green() * inverse + second.green() * ratio),
        round(first.blue() * inverse + second.blue() * ratio),
    )


def _luminance(color: QColor) -> float:
    return (
        0.2126 * color.redF()
        + 0.7152 * color.greenF()
        + 0.0722 * color.blueF()
    )


def _is_dark(color: QColor) -> bool:
    return _luminance(color) < 0.48


def _theme_id() -> str | None:
    if mw is None:
        return None
    value = getattr(mw, GLOBAL_STYLING_THEME_CHOICE_ATTR, None)
    if isinstance(value, str) and value:
        if value == "off":
            return None
        return value
    return None


def gamification_id() -> str | None:
    if mw is None:
        return None
    value = getattr(mw, GLOBAL_GAMIFICATION_CHOICE_ATTR, None)
    if isinstance(value, str) and value:
        return value
    return None


def gamification_label() -> str:
    current = gamification_id()
    if current is None:
        return "Local add-on defaults"
    return GAMIFICATION_LABELS.get(current, current)


def open_global_styling_settings() -> bool:
    if mw is None:
        return False
    callback = getattr(mw, GLOBAL_STYLING_OPEN_SETTINGS_ATTR, None)
    if not callable(callback):
        return False
    callback()
    return True


def build_global_preferences_group(
    parent: QWidget,
    *,
    addon_name: str,
    intro: str | None = None,
) -> QGroupBox:
    group = QGroupBox("Global Styling & Gamification", parent)
    layout = QVBoxLayout(group)
    layout.setContentsMargins(12, 12, 12, 12)
    layout.setSpacing(8)

    theme_text = _theme_id() or "Off"
    summary = QLabel(
        f"Current shared style: <b>{theme_text}</b><br>"
        f"Current gamification preset: <b>{gamification_label()}</b>"
    )
    summary.setWordWrap(True)
    layout.addWidget(summary)

    help_text = QLabel(
        intro
        or (
            f"{addon_name} keeps its own local behavior when Global Styling is missing or turned off. "
            "Use the central settings to adjust the shared theme and gamification level for supported add-ons."
        )
    )
    help_text.setWordWrap(True)
    layout.addWidget(help_text)

    row = QHBoxLayout()
    row.addStretch(1)
    button = QPushButton("Open Global Styling Settings", group)
    button.setEnabled(callable(getattr(mw, GLOBAL_STYLING_OPEN_SETTINGS_ATTR, None)) if mw is not None else False)
    button.clicked.connect(lambda: open_global_styling_settings())
    row.addWidget(button)
    layout.addLayout(row)
    return group


def _clean_tokens(palette: QPalette) -> dict[str, str]:
    window = palette.color(QPalette.ColorRole.Window)
    base = palette.color(QPalette.ColorRole.Base)
    text = palette.color(QPalette.ColorRole.Text)
    button = palette.color(QPalette.ColorRole.Button)
    highlight = palette.color(QPalette.ColorRole.Highlight)
    canvas = _blend(window, base, 0.35)

    return {
        "text": _hex(text),
        "muted_text": _alpha(text, 0.7),
        "canvas": _hex(canvas),
        "surface": _hex(base),
        "surface_alt": _hex(_blend(base, button, 0.22)),
        "input": _hex(_blend(base, window, 0.16)),
        "border": _alpha(text, 0.15),
        "accent": _hex(highlight),
        "accent_hover": _hex(_blend(highlight, text if _is_dark(highlight) else window, 0.16)),
        "accent_soft": _hex(_blend(highlight, base, 0.82)),
        "accent_text": "#ffffff" if _is_dark(highlight) else "#102331",
        "shadow": _alpha(text, 0.09),
        "goal_fill_start": _hex(_blend(highlight, QColor("#78c488"), 0.44)),
        "goal_fill_end": _hex(_blend(highlight, QColor("#4f9d69"), 0.52)),
        "goal_empty": _alpha(text, 0.08),
        "goal_forecast": _alpha(highlight, 0.18),
    }


def _heatmap_tokens(palette: QPalette) -> dict[str, str]:
    dark = _is_dark(palette.color(QPalette.ColorRole.Window))
    if dark:
        return {
            "text": "#edf7ef",
            "muted_text": "#b6d1bd",
            "canvas": "#13231b",
            "surface": "#193126",
            "surface_alt": "#214032",
            "input": "#10271d",
            "border": "#2d5945",
            "accent": "#67b36f",
            "accent_hover": "#7bc884",
            "accent_soft": "#203b2f",
            "accent_text": "#0e1b14",
            "shadow": "#66101b14",
            "goal_fill_start": "#7ac96f",
            "goal_fill_end": "#438b52",
            "goal_empty": "#284234",
            "goal_forecast": "#2f6440",
        }
    return {
        "text": "#244233",
        "muted_text": "#587767",
        "canvas": "#f7f5ed",
        "surface": "#fcfbf4",
        "surface_alt": "#f0ecdd",
        "input": "#f8f5e8",
        "border": "#d7d2bf",
        "accent": "#5aa469",
        "accent_hover": "#6cb67a",
        "accent_soft": "#e7f2e5",
        "accent_text": "#16311d",
        "shadow": "#1f253222",
        "goal_fill_start": "#8bcf75",
        "goal_fill_end": "#4f965d",
        "goal_empty": "#d8e4d2",
        "goal_forecast": "#c0d7bf",
    }


def _modern_tokens(palette: QPalette) -> dict[str, str]:
    dark = _is_dark(palette.color(QPalette.ColorRole.Window))
    if dark:
        return {
            "text": "#eef4ff",
            "muted_text": "#a7b7d6",
            "canvas": "#0f1728",
            "surface": "#152039",
            "surface_alt": "#1d2a4a",
            "input": "#0f1c34",
            "border": "#2a3b67",
            "accent": "#63b3ff",
            "accent_hover": "#84c5ff",
            "accent_soft": "#1a2d4e",
            "accent_text": "#08111f",
            "shadow": "#7f040814",
            "goal_fill_start": "#70c0ff",
            "goal_fill_end": "#3f88ff",
            "goal_empty": "#223557",
            "goal_forecast": "#274572",
        }
    return {
        "text": "#1f2a44",
        "muted_text": "#64728d",
        "canvas": "#eef4ff",
        "surface": "#ffffff",
        "surface_alt": "#f3f7ff",
        "input": "#f8fbff",
        "border": "#d9e4fb",
        "accent": "#4d8dff",
        "accent_hover": "#6ba2ff",
        "accent_soft": "#e8f0ff",
        "accent_text": "#ffffff",
        "shadow": "#242f4a18",
        "goal_fill_start": "#69b4ff",
        "goal_fill_end": "#4d8dff",
        "goal_empty": "#dfe8fb",
        "goal_forecast": "#bed1f5",
    }


def _theme_tokens(theme_id: str, palette: QPalette) -> dict[str, str]:
    if theme_id == "heatmap":
        return _heatmap_tokens(palette)
    if theme_id == "modern":
        return _modern_tokens(palette)
    return _clean_tokens(palette)


def apply_dialog_theme(widget: QWidget) -> bool:
    theme_id = _theme_id()
    if theme_id is None:
        return False
    colors = _theme_tokens(theme_id, widget.palette())
    widget.setStyleSheet(
        f"""
QDialog {{
    background: {colors["canvas"]};
    color: {colors["text"]};
}}
QLabel {{
    color: {colors["text"]};
}}
QGroupBox {{
    margin-top: 14px;
    padding: 14px 12px 12px 12px;
    border: 1px solid {colors["border"]};
    border-radius: 14px;
    background: {colors["surface"]};
    font-weight: 600;
}}
QGroupBox::title {{
    subcontrol-origin: margin;
    left: 10px;
    padding: 0 6px;
    color: {colors["muted_text"]};
    background: {colors["canvas"]};
}}
QLineEdit,
QPlainTextEdit,
QTextEdit,
QListWidget,
QComboBox,
QSpinBox,
QDoubleSpinBox,
QDateEdit,
QTimeEdit,
QTableWidget,
QTreeWidget,
QListView,
QTextBrowser {{
    background: {colors["input"]};
    color: {colors["text"]};
    border: 1px solid {colors["border"]};
    border-radius: 10px;
    padding: 6px 8px;
    selection-background-color: {colors["accent"]};
    selection-color: {colors["accent_text"]};
}}
QComboBox::drop-down {{
    border: 0;
    width: 24px;
}}
QPushButton,
QToolButton {{
    background: {colors["accent_soft"]};
    color: {colors["text"]};
    border: 1px solid {colors["border"]};
    border-radius: 10px;
    padding: 7px 12px;
}}
QPushButton:hover,
QToolButton:hover {{
    background: {colors["surface_alt"]};
    border-color: {colors["accent_hover"]};
}}
QPushButton:pressed,
QToolButton:pressed {{
    background: {colors["accent"]};
    color: {colors["accent_text"]};
}}
QDialogButtonBox QPushButton {{
    min-width: 96px;
}}
QCheckBox,
QRadioButton {{
    color: {colors["text"]};
    spacing: 8px;
}}
QScrollArea,
QStackedWidget,
QTabWidget::pane {{
    background: transparent;
    border: 0;
}}
QTabBar::tab {{
    background: {colors["surface_alt"]};
    color: {colors["muted_text"]};
    border: 1px solid {colors["border"]};
    border-bottom: 0;
    padding: 8px 12px;
    margin-right: 4px;
    border-top-left-radius: 10px;
    border-top-right-radius: 10px;
}}
QTabBar::tab:selected {{
    background: {colors["surface"]};
    color: {colors["text"]};
}}
"""
    )
    return True


def build_webview_theme_css(widget: QWidget, selector: str) -> str:
    theme_id = _theme_id()
    if theme_id is None:
        return ""
    colors = _theme_tokens(theme_id, widget.palette())
    return f"""
<style>
{selector} {{
    --moritz-theme-text: {colors["text"]};
    --moritz-theme-muted-text: {colors["muted_text"]};
    --moritz-theme-canvas: {colors["canvas"]};
    --moritz-theme-surface: {colors["surface"]};
    --moritz-theme-surface-alt: {colors["surface_alt"]};
    --moritz-theme-input: {colors["input"]};
    --moritz-theme-border: {colors["border"]};
    --moritz-theme-accent: {colors["accent"]};
    --moritz-theme-accent-hover: {colors["accent_hover"]};
    --moritz-theme-accent-soft: {colors["accent_soft"]};
    --moritz-theme-accent-text: {colors["accent_text"]};
    --moritz-theme-shadow: {colors["shadow"]};
    --moritz-theme-goal-fill-start: {colors["goal_fill_start"]};
    --moritz-theme-goal-fill-end: {colors["goal_fill_end"]};
    --moritz-theme-goal-empty: {colors["goal_empty"]};
    --moritz-theme-goal-forecast: {colors["goal_forecast"]};
}}
</style>
"""

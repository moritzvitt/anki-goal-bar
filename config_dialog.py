from __future__ import annotations

from aqt import mw
from aqt.deckbrowser import DeckBrowser
from aqt.main import AnkiQt
from aqt.overview import Overview
from aqt.qt import (
    QCheckBox,
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)
from aqt.stats import DeckStats

from .config import DEFAULT_CONFIG, PERIODS, MetricType

_BRIDGE_CMD = "gpb_config"
_METRIC_OPTIONS: tuple[tuple[str, MetricType], ...] = (
    ("Reviews completed", "reviews"),
    ("New cards learned", "new_cards"),
    ("Study time (minutes)", "study_minutes"),
)


class GoalConfigDialog(QDialog):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent or mw)
        self._addon_name = __name__.split(".", 1)[0]
        self._rows: dict[str, _GoalRow] = {}

        self.setWindowTitle("Goal Progress Bar")
        self.setMinimumWidth(420)

        root = QVBoxLayout(self)
        intro = QLabel(
            "Configure weekly, monthly, and yearly goals for the home-screen progress widget."
        )
        intro.setWordWrap(True)
        root.addWidget(intro)

        current = mw.addonManager.getConfig(self._addon_name) or {}
        for period in PERIODS:
            row = _GoalRow(period, current.get(period, DEFAULT_CONFIG[period]), self)
            self._rows[period] = row
            root.addWidget(row.group)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok
            | QDialogButtonBox.StandardButton.Cancel
            | QDialogButtonBox.StandardButton.RestoreDefaults
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        buttons.button(QDialogButtonBox.StandardButton.RestoreDefaults).clicked.connect(
            self._restore_defaults
        )
        root.addWidget(buttons)

    def accept(self) -> None:
        payload = {period: row.to_config() for period, row in self._rows.items()}
        mw.addonManager.writeConfig(self._addon_name, payload)
        mw.reset()
        super().accept()

    def _restore_defaults(self) -> None:
        for period, row in self._rows.items():
            row.apply_config(DEFAULT_CONFIG[period])


class _GoalRow:
    def __init__(self, period: str, config: dict, parent: QWidget) -> None:
        self.group = QGroupBox(period.capitalize(), parent)
        layout = QFormLayout(self.group)
        layout.setContentsMargins(12, 10, 12, 10)
        layout.setSpacing(8)

        self.enabled = QCheckBox("Enable this goal", self.group)
        layout.addRow(self.enabled)

        self.metric = QComboBox(self.group)
        for label, key in _METRIC_OPTIONS:
            self.metric.addItem(label, key)
        layout.addRow("Metric", self.metric)

        self.target = QSpinBox(self.group)
        self.target.setRange(0, 1_000_000)
        self.target.setSingleStep(10)
        layout.addRow("Target", self.target)

        self.apply_config(config)

    def apply_config(self, config: dict) -> None:
        self.enabled.setChecked(bool(config.get("enabled", False)))
        metric = config.get("metric", "reviews")
        index = self.metric.findData(metric)
        self.metric.setCurrentIndex(max(0, index))
        self.target.setValue(max(0, int(config.get("target", 0))))

    def to_config(self) -> dict:
        return {
            "enabled": self.enabled.isChecked(),
            "metric": self.metric.currentData(),
            "target": self.target.value(),
        }


def open_config_dialog() -> bool:
    dialog = GoalConfigDialog(mw)
    dialog.exec()
    return True


def try_handle_js_message(
    handled: tuple[bool, object],
    message: str,
    context: object,
) -> tuple[bool, object]:
    if handled[0]:
        return handled

    if message != _BRIDGE_CMD:
        return handled

    if not isinstance(context, (DeckBrowser, Overview, DeckStats)):
        return handled

    open_config_dialog()
    return (True, None)

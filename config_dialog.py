from __future__ import annotations

from aqt import mw
from aqt.deckbrowser import DeckBrowser
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
    QPushButton,
    QScrollArea,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)
from aqt.stats import DeckStats

from .config import (
    DEFAULT_DECK_ENTRY,
    LayoutMode,
    PERIODS,
    AddonConfig,
    DeckGoalDefinition,
    GoalDefinition,
    clamp_month_day,
    export_config,
    load_config,
)

_BRIDGE_CMD = "gpb_config"
_METRIC_OPTIONS = (
    ("Reviews completed", "reviews"),
    ("New cards learned", "new_cards"),
    ("Study time (minutes)", "study_minutes"),
)
_LAYOUT_OPTIONS: tuple[tuple[str, LayoutMode], ...] = (
    ("Show all configured decks", "all"),
    ("Show one goal bar at a time", "carousel"),
)


class GoalConfigDialog(QDialog):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent or mw)
        self._addon_name = __name__.split(".", 1)[0]
        self._deck_editors: list[_DeckConfigEditor] = []
        self._available_decks = [(deck.name, int(deck.id)) for deck in mw.col.decks.all_names_and_ids()]

        self.setWindowTitle("Goal Progress Bar")
        self.setMinimumWidth(640)
        self.setMinimumHeight(560)

        root = QVBoxLayout(self)
        intro = QLabel(
            "Configure deck-specific weekly, monthly, and yearly goals. "
            "Yearly goals can start on a custom month/day. Weekly starts on Monday and monthly starts on the 1st."
        )
        intro.setWordWrap(True)
        root.addWidget(intro)

        general_group = QGroupBox("General", self)
        general_layout = QFormLayout(general_group)
        self._layout_mode = QComboBox(general_group)
        for label, mode in _LAYOUT_OPTIONS:
            self._layout_mode.addItem(label, mode)
        general_layout.addRow("Home screen layout", self._layout_mode)
        self._show_behind_pace = QCheckBox("Show how far behind pace you are", general_group)
        general_layout.addRow(self._show_behind_pace)
        root.addWidget(general_group)

        decks_header = QHBoxLayout()
        decks_label = QLabel("Deck goal groups", self)
        decks_header.addWidget(decks_label)
        decks_header.addStretch(1)
        add_button = QPushButton("Add deck", self)
        add_button.clicked.connect(lambda: self._add_deck_editor())
        decks_header.addWidget(add_button)
        root.addLayout(decks_header)

        self._scroll = QScrollArea(self)
        self._scroll.setWidgetResizable(True)
        self._container = QWidget(self._scroll)
        self._container_layout = QVBoxLayout(self._container)
        self._container_layout.setContentsMargins(0, 0, 0, 0)
        self._container_layout.setSpacing(10)
        self._container_layout.addStretch(1)
        self._scroll.setWidget(self._container)
        root.addWidget(self._scroll, 1)

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

        self._apply_config(load_config())

    def accept(self) -> None:
        config = AddonConfig(
            layout_mode=self._layout_mode.currentData(),
            show_behind_pace=self._show_behind_pace.isChecked(),
            decks=tuple(editor.to_definition() for editor in self._deck_editors),
        )
        mw.addonManager.writeConfig(self._addon_name, export_config(config))
        mw.reset()
        super().accept()

    def _apply_config(self, config: AddonConfig) -> None:
        self._layout_mode.setCurrentIndex(max(0, self._layout_mode.findData(config.layout_mode)))
        self._show_behind_pace.setChecked(config.show_behind_pace)
        for editor in list(self._deck_editors):
            self._remove_editor(editor)

        deck_definitions = list(config.decks)
        if not deck_definitions:
            deck_definitions = [
                DeckGoalDefinition(
                    deck_id=None,
                    deck_name="",
                    goals=tuple(
                        GoalDefinition(
                            period=period,
                            enabled=DEFAULT_DECK_ENTRY[period]["enabled"],
                            metric=DEFAULT_DECK_ENTRY[period]["metric"],
                            target=DEFAULT_DECK_ENTRY[period]["target"],
                            start_month=DEFAULT_DECK_ENTRY[period].get("start_month", 1),
                            start_day=DEFAULT_DECK_ENTRY[period].get("start_day", 1),
                        )
                        for period in PERIODS
                    ),
                )
            ]

        for deck in deck_definitions:
            self._add_deck_editor(deck)

    def _restore_defaults(self) -> None:
        self._apply_config(AddonConfig(layout_mode="all", show_behind_pace=False, decks=tuple()))

    def _add_deck_editor(self, definition: DeckGoalDefinition | None = None) -> None:
        editor = _DeckConfigEditor(
            available_decks=self._available_decks,
            definition=definition,
            on_remove=self._remove_editor,
            parent=self._container,
        )
        self._deck_editors.append(editor)
        self._container_layout.insertWidget(self._container_layout.count() - 1, editor.group)

    def _remove_editor(self, editor: "_DeckConfigEditor") -> None:
        if editor in self._deck_editors:
            self._deck_editors.remove(editor)
            editor.group.deleteLater()


class _DeckConfigEditor:
    def __init__(
        self,
        available_decks: list[tuple[str, int]],
        definition: DeckGoalDefinition | None,
        on_remove,
        parent: QWidget,
    ) -> None:
        self.group = QGroupBox("Deck goal group", parent)
        self._on_remove = on_remove
        self._goal_rows: dict[str, _GoalRow] = {}

        layout = QVBoxLayout(self.group)
        top = QHBoxLayout()
        top.addWidget(QLabel("Deck", self.group))
        self.deck = QComboBox(self.group)
        self.deck.addItem("Select a deck...", None)
        for deck_name, deck_id in available_decks:
            self.deck.addItem(deck_name, deck_id)
        top.addWidget(self.deck, 1)
        remove_button = QPushButton("Remove", self.group)
        remove_button.clicked.connect(lambda: self._on_remove(self))
        top.addWidget(remove_button)
        layout.addLayout(top)

        for period in PERIODS:
            row = _GoalRow(period, self.group)
            self._goal_rows[period] = row
            layout.addWidget(row.group)

        if definition is not None:
            self.apply_definition(definition)

    def apply_definition(self, definition: DeckGoalDefinition) -> None:
        index = self.deck.findData(definition.deck_id)
        self.deck.setCurrentIndex(max(0, index))
        if index < 0 and definition.deck_name:
            self.deck.setCurrentIndex(0)
        for goal in definition.goals:
            self._goal_rows[goal.period].apply_definition(goal)

    def to_definition(self) -> DeckGoalDefinition:
        deck_id = self.deck.currentData()
        deck_name = self.deck.currentText() if deck_id is not None else ""
        return DeckGoalDefinition(
            deck_id=deck_id,
            deck_name=deck_name,
            goals=tuple(row.to_definition() for row in self._goal_rows.values()),
        )


class _GoalRow:
    def __init__(self, period: str, parent: QWidget) -> None:
        self._period = period
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

        self.year_start_month = QSpinBox(self.group)
        self.year_start_month.setRange(1, 12)
        self.year_start_day = QSpinBox(self.group)
        self.year_start_day.setRange(1, 31)
        self.year_start = QWidget(self.group)
        year_start_layout = QHBoxLayout(self.year_start)
        year_start_layout.setContentsMargins(0, 0, 0, 0)
        year_start_layout.addWidget(QLabel("Month", self.year_start))
        year_start_layout.addWidget(self.year_start_month)
        year_start_layout.addSpacing(8)
        year_start_layout.addWidget(QLabel("Day", self.year_start))
        year_start_layout.addWidget(self.year_start_day)
        year_start_layout.addStretch(1)
        layout.addRow("Year starts on", self.year_start)
        self._year_start_label = layout.labelForField(self.year_start)
        self._set_year_start_visible(period == "yearly")

    def apply_definition(self, definition: GoalDefinition) -> None:
        self.enabled.setChecked(definition.enabled)
        self.metric.setCurrentIndex(max(0, self.metric.findData(definition.metric)))
        self.target.setValue(definition.target)
        self.year_start_month.setValue(definition.start_month)
        self.year_start_day.setValue(definition.start_day)

    def to_definition(self) -> GoalDefinition:
        month, day = clamp_month_day(self.year_start_month.value(), self.year_start_day.value())
        return GoalDefinition(
            period=self._period,  # type: ignore[arg-type]
            enabled=self.enabled.isChecked(),
            metric=self.metric.currentData(),
            target=self.target.value(),
            start_month=month,
            start_day=day,
        )

    def _set_year_start_visible(self, visible: bool) -> None:
        self.year_start.setVisible(visible)
        if self._year_start_label is not None:
            self._year_start_label.setVisible(visible)


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

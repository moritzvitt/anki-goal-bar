from __future__ import annotations

from aqt import mw
from aqt.deckbrowser import DeckBrowser
from aqt.overview import Overview
from aqt.qt import (
    QCheckBox,
    QComboBox,
    QDate,
    QDateEdit,
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QPlainTextEdit,
    QPushButton,
    QScrollArea,
    QSpinBox,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)
from aqt.stats import DeckStats

from .config import (
    DEFAULT_REWARDS,
    LayoutMode,
    MILESTONE_KEYS,
    MilestoneDisplayMode,
    PERIODS,
    AddonConfig,
    CustomGoalDefinition,
    DeckGoalDefinition,
    GoalDefinition,
    clamp_month_day,
    default_custom_goal_definition,
    default_config,
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
_MILESTONE_OPTIONS: tuple[tuple[str, str], ...] = (
    ("Show 1/4 milestone", "quarter"),
    ("Show 1/2 milestone", "half"),
    ("Show 3/4 milestone", "three_quarter"),
)
_MILESTONE_DISPLAY_OPTIONS: tuple[tuple[str, MilestoneDisplayMode], ...] = (
    ("Show all enabled milestones", "all"),
    ("Show only the next milestone", "next"),
)


class GoalConfigDialog(QDialog):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent or mw)
        self._addon_name = __name__.split(".", 1)[0]
        self._page_editors: list[object] = []
        self._available_decks = [(deck.name, int(deck.id)) for deck in mw.col.decks.all_names_and_ids()]

        self.setWindowTitle("Goal Progress Bar")
        self.setMinimumWidth(980)
        self.setMinimumHeight(680)

        root = QVBoxLayout(self)
        intro = QLabel(
            "Configure your home-screen goals, personal motivation, and deck-specific weekly, "
            "monthly, and yearly targets. Each deck goal group now has its own page in this window."
        )
        intro.setWordWrap(True)
        root.addWidget(intro)

        content = QHBoxLayout()
        content.setSpacing(14)
        root.addLayout(content, 1)

        nav_panel = QWidget(self)
        nav_layout = QVBoxLayout(nav_panel)
        nav_layout.setContentsMargins(0, 0, 0, 0)
        nav_layout.setSpacing(8)

        nav_header = QHBoxLayout()
        nav_header.addWidget(QLabel("Pages", nav_panel))
        nav_header.addStretch(1)
        add_deck_button = QPushButton("Add deck", nav_panel)
        add_deck_button.clicked.connect(lambda: self._add_deck_editor(select_new=True))
        nav_header.addWidget(add_deck_button)
        add_custom_button = QPushButton("Add custom goal", nav_panel)
        add_custom_button.clicked.connect(lambda: self._add_custom_editor(select_new=True))
        nav_header.addWidget(add_custom_button)
        nav_layout.addLayout(nav_header)

        self._nav = QListWidget(nav_panel)
        self._nav.setMinimumWidth(220)
        self._nav.currentRowChanged.connect(self._set_current_page)
        nav_layout.addWidget(self._nav, 1)
        content.addWidget(nav_panel, 0)

        self._pages = QStackedWidget(self)
        content.addWidget(self._pages, 1)

        self._add_general_page()

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
            show_motivation=self._show_motivation.isChecked(),
            show_rewards=self._show_rewards.isChecked(),
            show_milestones=self._show_milestones.isChecked(),
            milestone_display_mode=self._milestone_display_mode.currentData(),
            motivation=self._motivation_text.toPlainText().strip(),
            milestones={
                key: self._milestone_toggles[key].isChecked()
                for key in MILESTONE_KEYS
            },
            decks=tuple(
                editor.to_definition()
                for editor in self._page_editors
                if isinstance(editor, _DeckConfigEditor)
            ),
            custom_goals=tuple(
                editor.to_definition()
                for editor in self._page_editors
                if isinstance(editor, _CustomGoalEditor)
            ),
        )
        mw.addonManager.writeConfig(self._addon_name, export_config(config))
        mw.reset()
        super().accept()

    def _add_general_page(self) -> None:
        page = QWidget(self)
        layout = QVBoxLayout(page)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(14)

        motivation_group = QGroupBox("Motivation", page)
        motivation_layout = QFormLayout(motivation_group)
        self._motivation_text = QPlainTextEdit(motivation_group)
        self._motivation_text.setPlaceholderText(
            "Write the message you want to see when hovering over the scroll on the home screen."
        )
        self._motivation_text.setMinimumHeight(110)
        motivation_layout.addRow("Personal motivational text", self._motivation_text)
        hint = QLabel(
            "The home screen shows a small ancient scroll next to the settings button. Hover it to "
            "expand your personal message. Its tooltip is always “my Motivation”."
        )
        hint.setWordWrap(True)
        motivation_layout.addRow("", hint)
        layout.addWidget(motivation_group)

        display_group = QGroupBox("Display", page)
        display_layout = QFormLayout(display_group)
        self._layout_mode = QComboBox(display_group)
        for label, mode in _LAYOUT_OPTIONS:
            self._layout_mode.addItem(label, mode)
        display_layout.addRow("Home screen layout", self._layout_mode)

        self._show_behind_pace = QCheckBox("Show how far behind pace you are", display_group)
        display_layout.addRow(self._show_behind_pace)

        self._show_motivation = QCheckBox("Show motivation scroll", display_group)
        display_layout.addRow(self._show_motivation)

        self._show_rewards = QCheckBox("Show reward badges", display_group)
        display_layout.addRow(self._show_rewards)
        self._show_rewards.toggled.connect(self._apply_reward_visibility)

        self._show_milestones = QCheckBox(
            "Show milestone markers for weekly, monthly, and yearly goals",
            display_group,
        )
        display_layout.addRow(self._show_milestones)

        self._milestone_display_mode = QComboBox(display_group)
        for label, mode in _MILESTONE_DISPLAY_OPTIONS:
            self._milestone_display_mode.addItem(label, mode)
        display_layout.addRow("Milestone display", self._milestone_display_mode)
        self._milestone_display_label = display_layout.labelForField(self._milestone_display_mode)

        self._milestone_toggles: dict[str, QCheckBox] = {}
        self._milestones_box = QWidget(display_group)
        milestones_layout = QVBoxLayout(self._milestones_box)
        milestones_layout.setContentsMargins(0, 0, 0, 0)
        milestones_layout.setSpacing(4)
        for label, key in _MILESTONE_OPTIONS:
            checkbox = QCheckBox(label, self._milestones_box)
            self._milestone_toggles[key] = checkbox
            milestones_layout.addWidget(checkbox)
        self._show_milestones.toggled.connect(self._apply_milestone_visibility)
        self._milestone_display_mode.currentIndexChanged.connect(
            lambda _index: self._apply_milestone_visibility(self._show_milestones.isChecked())
        )
        display_layout.addRow("Milestones", self._milestones_box)
        self._milestones_label = display_layout.labelForField(self._milestones_box)
        layout.addWidget(display_group)
        layout.addStretch(1)

        self._pages.addWidget(self._wrap_page(page))
        self._nav.addItem(QListWidgetItem("General"))

    def _apply_config(self, config: AddonConfig) -> None:
        self._layout_mode.setCurrentIndex(max(0, self._layout_mode.findData(config.layout_mode)))
        self._show_behind_pace.setChecked(config.show_behind_pace)
        self._show_motivation.setChecked(config.show_motivation)
        self._show_rewards.setChecked(config.show_rewards)
        self._show_milestones.setChecked(config.show_milestones)
        self._milestone_display_mode.setCurrentIndex(
            max(0, self._milestone_display_mode.findData(config.milestone_display_mode))
        )
        self._motivation_text.setPlainText(config.motivation)
        for key in MILESTONE_KEYS:
            self._milestone_toggles[key].setChecked(bool(config.milestones.get(key, True)))
        for editor in list(self._page_editors):
            self._remove_editor(editor, select_replacement=False)

        for deck in config.decks:
            self._add_deck_editor(deck, select_new=False)
        for custom_goal in config.custom_goals:
            self._add_custom_editor(custom_goal, select_new=False)

        self._apply_reward_visibility(self._show_rewards.isChecked())
        self._apply_milestone_visibility(self._show_milestones.isChecked())
        self._refresh_deck_page_labels()
        self._nav.setCurrentRow(0)

    def _restore_defaults(self) -> None:
        self._apply_config(default_config())

    def _add_deck_editor(
        self,
        definition: DeckGoalDefinition | None = None,
        *,
        select_new: bool,
    ) -> None:
        editor = _DeckConfigEditor(
            available_decks=self._available_decks,
            definition=definition,
            on_remove=self._remove_editor,
            on_title_changed=self._refresh_deck_page_labels,
            parent=self,
        )
        self._page_editors.append(editor)
        editor.page_widget = self._wrap_page(editor.page)
        self._pages.addWidget(editor.page_widget)
        editor.nav_item = QListWidgetItem("")
        self._nav.addItem(editor.nav_item)
        editor.set_rewards_controls_visible(self._show_rewards.isChecked())
        self._refresh_deck_page_labels()
        if select_new:
            self._nav.setCurrentRow(self._nav.count() - 1)

    def _add_custom_editor(
        self,
        definition: CustomGoalDefinition | None = None,
        *,
        select_new: bool,
    ) -> None:
        editor = _CustomGoalEditor(
            available_decks=self._available_decks,
            definition=definition or default_custom_goal_definition(),
            on_remove=self._remove_editor,
            on_title_changed=self._refresh_deck_page_labels,
            parent=self,
        )
        self._page_editors.append(editor)
        editor.page_widget = self._wrap_page(editor.page)
        self._pages.addWidget(editor.page_widget)
        editor.nav_item = QListWidgetItem("")
        self._nav.addItem(editor.nav_item)
        editor.set_rewards_controls_visible(self._show_rewards.isChecked())
        self._refresh_deck_page_labels()
        if select_new:
            self._nav.setCurrentRow(self._nav.count() - 1)

    def _remove_editor(
        self,
        editor: "_DeckConfigEditor",
        *,
        select_replacement: bool = True,
    ) -> None:
        if editor not in self._page_editors:
            return

        current_row = self._nav.currentRow()
        row = self._page_editors.index(editor) + 1
        self._page_editors.remove(editor)

        if editor.page_widget is not None:
            self._pages.removeWidget(editor.page_widget)
            editor.page_widget.deleteLater()
        editor.page.deleteLater()

        item = self._nav.takeItem(row)
        del item

        self._refresh_deck_page_labels()

        if select_replacement:
            if self._nav.count() <= 1:
                self._nav.setCurrentRow(0)
            else:
                self._nav.setCurrentRow(min(current_row, self._nav.count() - 1))

    def _refresh_deck_page_labels(self) -> None:
        for index, editor in enumerate(self._page_editors, start=1):
            title = editor.display_title(index)
            editor.set_page_title(title)
            if editor.nav_item is not None:
                editor.nav_item.setText(title)

    def _apply_reward_visibility(self, visible: bool) -> None:
        for editor in self._page_editors:
            editor.set_rewards_controls_visible(visible)

    def _apply_milestone_visibility(self, visible: bool) -> None:
        show_individual_milestones = (
            visible and self._milestone_display_mode.currentData() != "next"
        )
        self._milestones_box.setVisible(show_individual_milestones)
        if self._milestones_label is not None:
            self._milestones_label.setVisible(show_individual_milestones)
        self._milestone_display_mode.setVisible(visible)
        if self._milestone_display_label is not None:
            self._milestone_display_label.setVisible(visible)

    def _set_current_page(self, row: int) -> None:
        if row < 0 or row >= self._pages.count():
            return
        self._pages.setCurrentIndex(row)

    def _wrap_page(self, page: QWidget) -> QScrollArea:
        scroll = QScrollArea(self)
        scroll.setWidgetResizable(True)
        scroll.setWidget(page)
        return scroll


class _DeckConfigEditor:
    def __init__(
        self,
        available_decks: list[tuple[str, int]],
        definition: DeckGoalDefinition | None,
        on_remove,
        on_title_changed,
        parent: QWidget,
    ) -> None:
        self._on_remove = on_remove
        self._on_title_changed = on_title_changed
        self._goal_rows: dict[str, _GoalRow] = {}
        self.nav_item: QListWidgetItem | None = None
        self.page_widget: QScrollArea | None = None

        self.page = QWidget(parent)
        layout = QVBoxLayout(self.page)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(14)

        header = QHBoxLayout()
        self._title = QLabel("Deck goal group", self.page)
        header.addWidget(self._title)
        header.addStretch(1)
        remove_button = QPushButton("Remove deck group", self.page)
        remove_button.clicked.connect(lambda: self._on_remove(self))
        header.addWidget(remove_button)
        layout.addLayout(header)

        info = QLabel(
            "Pick the deck tree this page should track, then adjust its weekly, monthly, and yearly goals."
        )
        info.setWordWrap(True)
        layout.addWidget(info)

        deck_group = QGroupBox("Deck selection", self.page)
        deck_layout = QFormLayout(deck_group)
        self.deck = QComboBox(deck_group)
        self.deck.addItem("Select a deck...", None)
        for deck_name, deck_id in available_decks:
            self.deck.addItem(deck_name, deck_id)
        self.deck.currentIndexChanged.connect(self._notify_title_changed)
        deck_layout.addRow("Deck", self.deck)
        layout.addWidget(deck_group)

        for period in PERIODS:
            row = _GoalRow(period, self.page)
            self._goal_rows[period] = row
            layout.addWidget(row.group)

        layout.addStretch(1)

        if definition is not None:
            self.apply_definition(definition)
        else:
            self._notify_title_changed()

    def apply_definition(self, definition: DeckGoalDefinition) -> None:
        index = self.deck.findData(definition.deck_id)
        self.deck.setCurrentIndex(max(0, index))
        if index < 0 and definition.deck_name:
            self.deck.setCurrentIndex(0)
        for goal in definition.goals:
            self._goal_rows[goal.period].apply_definition(goal)
        self._notify_title_changed()

    def to_definition(self) -> DeckGoalDefinition:
        deck_id = self.deck.currentData()
        deck_name = self.deck.currentText() if deck_id is not None else ""
        return DeckGoalDefinition(
            deck_id=deck_id,
            deck_name=deck_name,
            goals=tuple(row.to_definition() for row in self._goal_rows.values()),
        )

    def display_title(self, position: int) -> str:
        deck_id = self.deck.currentData()
        if deck_id is not None:
            return str(self.deck.currentText())
        return f"Deck group {position}"

    def set_page_title(self, title: str) -> None:
        self._title.setText(title)

    def set_rewards_controls_visible(self, visible: bool) -> None:
        for row in self._goal_rows.values():
            row.set_rewards_controls_visible(visible)

    def _notify_title_changed(self) -> None:
        self._on_title_changed()


class _CustomGoalEditor:
    def __init__(
        self,
        available_decks: list[tuple[str, int]],
        definition: CustomGoalDefinition,
        on_remove,
        on_title_changed,
        parent: QWidget,
    ) -> None:
        self._on_remove = on_remove
        self._on_title_changed = on_title_changed
        self.nav_item: QListWidgetItem | None = None
        self.page_widget: QScrollArea | None = None
        self._syncing_dates = False

        self.page = QWidget(parent)
        layout = QVBoxLayout(self.page)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(14)

        header = QHBoxLayout()
        self._title = QLabel("Custom goal", self.page)
        header.addWidget(self._title)
        header.addStretch(1)
        remove_button = QPushButton("Remove custom goal", self.page)
        remove_button.clicked.connect(lambda: self._on_remove(self))
        header.addWidget(remove_button)
        layout.addLayout(header)

        info = QLabel(
            "Create a personal goal with its own title, start date, duration, and optional deck scope."
        )
        info.setWordWrap(True)
        layout.addWidget(info)

        basics_group = QGroupBox("Custom period", self.page)
        basics_layout = QFormLayout(basics_group)
        self.title = QLineEdit(basics_group)
        self.title.textChanged.connect(self._notify_title_changed)
        basics_layout.addRow("Title", self.title)

        self.deck = QComboBox(basics_group)
        self.deck.addItem("All decks", None)
        for deck_name, deck_id in available_decks:
            self.deck.addItem(deck_name, deck_id)
        basics_layout.addRow("Scope", self.deck)

        self.start_date = QDateEdit(basics_group)
        self.start_date.setCalendarPopup(True)
        self.start_date.setDisplayFormat("yyyy-MM-dd")
        self.start_date.dateChanged.connect(self._sync_end_date_from_duration)
        basics_layout.addRow("Starts on", self.start_date)

        self.duration_days = QSpinBox(basics_group)
        self.duration_days.setRange(1, 3650)
        self.duration_days.setSuffix(" days")
        self.duration_days.valueChanged.connect(self._sync_end_date_from_duration)
        basics_layout.addRow("Duration", self.duration_days)

        self.end_date = QDateEdit(basics_group)
        self.end_date.setCalendarPopup(True)
        self.end_date.setDisplayFormat("yyyy-MM-dd")
        self.end_date.dateChanged.connect(self._sync_duration_from_end_date)
        basics_layout.addRow("Ends on", self.end_date)
        layout.addWidget(basics_group)

        self.goal_row = _GoalRow("custom", self.page)
        layout.addWidget(self.goal_row.group)
        layout.addStretch(1)

        self.apply_definition(definition)

    def apply_definition(self, definition: CustomGoalDefinition) -> None:
        self.title.setText(definition.title)
        self.deck.setCurrentIndex(max(0, self.deck.findData(definition.deck_id)))
        self.start_date.setDate(
            QDate(
                max(1, definition.goal.start_year),
                definition.goal.start_month,
                definition.goal.start_day,
            )
        )
        self.duration_days.setValue(definition.goal.duration_days)
        self._sync_end_date_from_duration()
        self.goal_row.apply_definition(definition.goal)
        self._notify_title_changed()

    def to_definition(self) -> CustomGoalDefinition:
        qdate = self.start_date.date()
        goal = self.goal_row.to_definition()
        goal = GoalDefinition(
            period="custom",
            enabled=goal.enabled,
            metric=goal.metric,
            target=goal.target,
            start_year=qdate.year(),
            start_month=qdate.month(),
            start_day=qdate.day(),
            duration_days=self.duration_days.value(),
            rewards=goal.rewards,
            show_reward=goal.show_reward,
        )
        deck_id = self.deck.currentData()
        deck_name = self.deck.currentText() if deck_id is not None else ""
        return CustomGoalDefinition(
            title=self.title.text().strip() or "Custom goal",
            deck_id=deck_id,
            deck_name=deck_name,
            goal=goal,
        )

    def display_title(self, position: int) -> str:
        value = self.title.text().strip()
        return value or f"Custom goal {position}"

    def set_page_title(self, title: str) -> None:
        self._title.setText(title)

    def set_rewards_controls_visible(self, visible: bool) -> None:
        self.goal_row.set_rewards_controls_visible(visible)

    def _notify_title_changed(self) -> None:
        self._on_title_changed()

    def _sync_end_date_from_duration(self) -> None:
        if self._syncing_dates:
            return
        self._syncing_dates = True
        self.end_date.setDate(self.start_date.date().addDays(self.duration_days.value() - 1))
        self._syncing_dates = False

    def _sync_duration_from_end_date(self) -> None:
        if self._syncing_dates:
            return
        self._syncing_dates = True
        duration = max(1, self.start_date.date().daysTo(self.end_date.date()) + 1)
        self.duration_days.setValue(duration)
        self._syncing_dates = False


class _GoalRow:
    def __init__(self, period: str, parent: QWidget) -> None:
        self._period = period
        title = "Custom goal settings" if period == "custom" else period.capitalize()
        self.group = QGroupBox(title, parent)
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

        self.rewards = QPlainTextEdit(self.group)
        self.rewards.setPlaceholderText("One reward per line, emojis welcome")
        self.rewards.setMinimumHeight(120)
        layout.addRow("Rewards", self.rewards)
        self._rewards_label = layout.labelForField(self.rewards)

        self.show_reward = QCheckBox("Show reward badge for this goal", self.group)
        self.show_reward.setChecked(True)
        layout.addRow(self.show_reward)

        self._rewards_hint = QLabel(
            "One reward per line. The widget shows a compact emoji-plus-level chip and reveals the full reward on hover."
        )
        self._rewards_hint.setWordWrap(True)
        layout.addRow("", self._rewards_hint)

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
        self.rewards.setPlainText("\n".join(definition.rewards))
        self.show_reward.setChecked(definition.show_reward)

    def to_definition(self) -> GoalDefinition:
        month, day = clamp_month_day(self.year_start_month.value(), self.year_start_day.value())
        rewards = tuple(
            line.strip()
            for line in self.rewards.toPlainText().splitlines()
            if line.strip()
        )
        rewards_default_period = "monthly" if self._period == "custom" else self._period
        return GoalDefinition(
            period=self._period,  # type: ignore[arg-type]
            enabled=self.enabled.isChecked(),
            metric=self.metric.currentData(),
            target=self.target.value(),
            start_month=month,
            start_day=day,
            start_year=0,
            duration_days=30,
            rewards=rewards or DEFAULT_REWARDS[rewards_default_period],  # type: ignore[index]
            show_reward=self.show_reward.isChecked(),
        )

    def _set_year_start_visible(self, visible: bool) -> None:
        self.year_start.setVisible(visible)
        if self._year_start_label is not None:
            self._year_start_label.setVisible(visible)

    def set_rewards_controls_visible(self, visible: bool) -> None:
        self.rewards.setVisible(visible)
        self.show_reward.setVisible(visible)
        self._rewards_hint.setVisible(visible)
        if self._rewards_label is not None:
            self._rewards_label.setVisible(visible)


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

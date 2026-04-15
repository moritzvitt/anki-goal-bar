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
    QInputDialog,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QPlainTextEdit,
    QPushButton,
    QScrollArea,
    QMessageBox,
    QSpinBox,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)
from aqt.stats import DeckStats
from aqt.utils import showInfo, showWarning

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
    StreakDisplayMode,
    VisualStyle,
    clamp_month_day,
    default_custom_goal_definition,
    default_config,
    export_config,
    load_config,
)

_BRIDGE_CMD = "gpb_config"
_CATCHUP_CMD = "gpb_catchup"
_METRIC_OPTIONS = (
    ("Reviews completed", "reviews"),
    ("New cards learned", "new_cards"),
    ("Study time (minutes)", "study_minutes"),
)
_LAYOUT_OPTIONS: tuple[tuple[str, LayoutMode], ...] = (
    ("Show all configured decks", "all"),
    ("Show one goal bar at a time", "carousel"),
)
_VISUAL_STYLE_OPTIONS: tuple[tuple[str, VisualStyle], ...] = (
    ("Standard goal bar", "default"),
    ("Review Heatmap-inspired blocks", "heatmap"),
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
_STREAK_DISPLAY_OPTIONS: tuple[tuple[str, StreakDisplayMode], ...] = (
    ("Show all earned badges", "all"),
    ("Show only the latest badge", "last"),
)


class GoalConfigDialog(QDialog):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent or mw)
        self._addon_name = __name__.split(".", 1)[0]
        self._page_editors: list[object] = []
        self._loaded_visual_style: VisualStyle = "default"
        self._loaded_visual_style_auto = True
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
        add_deck_button.setToolTip("Add a new page for a deck-specific weekly, monthly, and yearly goal group.")
        add_deck_button.clicked.connect(lambda: self._add_deck_editor(select_new=True))
        nav_header.addWidget(add_deck_button)
        add_custom_button = QPushButton("Add custom goal", nav_panel)
        add_custom_button.setToolTip("Add a custom goal with its own title, dates, and optional deck scope.")
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
        selected_visual_style = self._visual_style.currentData()
        visual_style_auto = (
            self._loaded_visual_style_auto
            and selected_visual_style == self._loaded_visual_style
        )
        config = AddonConfig(
            layout_mode=self._layout_mode.currentData(),
            visual_style=selected_visual_style,
            visual_style_auto=visual_style_auto,
            show_brief_page=self._show_brief_page.isChecked(),
            show_brief_page_horizontal=self._show_brief_page_horizontal.isChecked(),
            show_behind_pace=self._show_behind_pace.isChecked(),
            show_catchup_button=self._show_catchup_button.isChecked(),
            show_motivation=self._show_motivation.isChecked(),
            show_streaks=self._show_streaks.isChecked(),
            streak_display_mode=self._streak_display_mode.currentData(),
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

        self._motivation_group = QGroupBox("Motivation", page)
        motivation_layout = QFormLayout(self._motivation_group)
        self._motivation_text = QPlainTextEdit(self._motivation_group)
        self._motivation_text.setPlaceholderText(
            "Write the message you want to see when opening the scroll on the home screen."
        )
        self._motivation_text.setToolTip("Your personal message shown when the home-screen scroll is opened.")
        self._motivation_text.setMinimumHeight(110)
        motivation_layout.addRow("Personal motivational text", self._motivation_text)
        hint = QLabel(
            "The home screen shows a small ancient scroll next to the settings button. Click it to "
            "open your personal message. Its tooltip is always “my Motivation”."
        )
        hint.setWordWrap(True)
        motivation_layout.addRow("", hint)

        visual_style_group = QGroupBox("Visual style", page)
        visual_style_layout = QFormLayout(visual_style_group)
        self._visual_style = QComboBox(visual_style_group)
        for label, style in _VISUAL_STYLE_OPTIONS:
            self._visual_style.addItem(label, style)
        self._visual_style.setToolTip(
            "Switch between the default rounded goal bar and a Review Heatmap-inspired retro block display."
        )
        visual_style_layout.addRow("Goal bar style", self._visual_style)
        visual_style_hint = QLabel(
            "Choose how the home-screen goal widget should look. The heatmap option uses retro block cells "
            "and borrows Review Heatmap theme colors when that add-on is installed."
        )
        visual_style_hint.setWordWrap(True)
        visual_style_layout.addRow("", visual_style_hint)
        minimalist_button = QPushButton("Apply minimalist mode", visual_style_group)
        minimalist_button.setToolTip(
            "Quickly turn off rewards, streaks, the motivation scroll, and the catch-up button."
        )
        minimalist_button.clicked.connect(self._apply_minimalist_mode)
        visual_style_layout.addRow("Quick preset", minimalist_button)
        layout.addWidget(visual_style_group)

        display_group = QGroupBox("Display", page)
        display_layout = QFormLayout(display_group)
        self._layout_mode = QComboBox(display_group)
        for label, mode in _LAYOUT_OPTIONS:
            self._layout_mode.addItem(label, mode)
        self._layout_mode.setToolTip("Choose whether every deck widget is visible at once or shown one goal page at a time.")
        display_layout.addRow("Home screen layout", self._layout_mode)
        self._layout_mode.currentIndexChanged.connect(self._apply_layout_mode_visibility)

        self._show_brief_page = QCheckBox(
            "Show brief summary page first in carousel mode",
            display_group,
        )
        self._show_brief_page.setToolTip("Add a compact first carousel page that shows weekly, monthly, and yearly progress together.")
        display_layout.addRow("", self._show_brief_page)
        self._show_brief_page.toggled.connect(self._apply_layout_mode_visibility)

        self._show_brief_page_horizontal = QCheckBox(
            "Show brief summary bars next to each other",
            display_group,
        )
        self._show_brief_page_horizontal.setToolTip("Show the brief summary page as compressed horizontal mini-bars instead of stacked rows.")
        display_layout.addRow("", self._show_brief_page_horizontal)

        self._show_behind_pace = QCheckBox("Show how far behind pace you are", display_group)
        self._show_behind_pace.setToolTip("Show how far the current goal is behind the expected pace for this point in the period.")
        display_layout.addRow(self._show_behind_pace)
        self._show_behind_pace.toggled.connect(self._apply_behind_pace_visibility)

        self._show_catchup_button = QCheckBox("Show catch-up button", display_group)
        self._show_catchup_button.setToolTip("Show the catch-up shortcut below behind-pace notes for new-card goals.")
        display_layout.addRow("", self._show_catchup_button)

        self._show_motivation = QCheckBox("Show motivation scroll", display_group)
        self._show_motivation.setToolTip("Show the small scroll button next to the settings icon on the home screen.")
        display_layout.addRow(self._show_motivation)
        display_layout.addRow("", self._motivation_group)
        self._show_motivation.toggled.connect(self._apply_motivation_visibility)

        self._show_streaks = QCheckBox("Show streak badges", display_group)
        self._show_streaks.setToolTip("Show earned streak badges for periods where goals were completed consecutively.")
        display_layout.addRow(self._show_streaks)

        self._streak_display_mode = QComboBox(display_group)
        for label, mode in _STREAK_DISPLAY_OPTIONS:
            self._streak_display_mode.addItem(label, mode)
        self._streak_display_mode.setToolTip("Choose whether to show every earned streak badge or only the latest one by default.")
        display_layout.addRow("Streak display", self._streak_display_mode)
        self._streak_display_label = display_layout.labelForField(self._streak_display_mode)
        self._show_streaks.toggled.connect(self._apply_streak_visibility)

        self._show_rewards = QCheckBox("Show reward badges", display_group)
        self._show_rewards.setToolTip("Show or hide reward chips globally across all goals.")
        display_layout.addRow(self._show_rewards)
        self._show_rewards.toggled.connect(self._apply_reward_visibility)

        self._show_milestones = QCheckBox(
            "Show milestone markers for weekly, monthly, and yearly goals",
            display_group,
        )
        self._show_milestones.setToolTip("Show progress checkpoints like 1/4, 1/2, and 3/4 on the bar.")
        display_layout.addRow(self._show_milestones)

        self._milestone_display_mode = QComboBox(display_group)
        for label, mode in _MILESTONE_DISPLAY_OPTIONS:
            self._milestone_display_mode.addItem(label, mode)
        self._milestone_display_mode.setToolTip("Show every enabled milestone or only the next upcoming one.")
        display_layout.addRow("Milestone display", self._milestone_display_mode)
        self._milestone_display_label = display_layout.labelForField(self._milestone_display_mode)

        self._milestone_toggles: dict[str, QCheckBox] = {}
        self._milestones_box = QWidget(display_group)
        milestones_layout = QVBoxLayout(self._milestones_box)
        milestones_layout.setContentsMargins(0, 0, 0, 0)
        milestones_layout.setSpacing(4)
        for label, key in _MILESTONE_OPTIONS:
            checkbox = QCheckBox(label, self._milestones_box)
            checkbox.setToolTip(f"Show the {label.removeprefix('Show ').lower()} marker on supported goal bars.")
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
        self._loaded_visual_style = config.visual_style
        self._loaded_visual_style_auto = config.visual_style_auto
        self._layout_mode.setCurrentIndex(max(0, self._layout_mode.findData(config.layout_mode)))
        self._visual_style.setCurrentIndex(max(0, self._visual_style.findData(config.visual_style)))
        self._show_brief_page.setChecked(config.show_brief_page)
        self._show_brief_page_horizontal.setChecked(config.show_brief_page_horizontal)
        self._show_behind_pace.setChecked(config.show_behind_pace)
        self._show_catchup_button.setChecked(config.show_catchup_button)
        self._show_motivation.setChecked(config.show_motivation)
        self._show_streaks.setChecked(config.show_streaks)
        self._streak_display_mode.setCurrentIndex(
            max(0, self._streak_display_mode.findData(config.streak_display_mode))
        )
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

        self._apply_layout_mode_visibility()
        self._apply_behind_pace_visibility(self._show_behind_pace.isChecked())
        self._apply_motivation_visibility(self._show_motivation.isChecked())
        self._apply_reward_visibility(self._show_rewards.isChecked())
        self._apply_streak_visibility(self._show_streaks.isChecked())
        self._apply_milestone_visibility(self._show_milestones.isChecked())
        self._refresh_deck_page_labels()
        self._nav.setCurrentRow(0)

    def _restore_defaults(self) -> None:
        self._apply_config(default_config())

    def _apply_motivation_visibility(self, visible: bool) -> None:
        self._motivation_group.setVisible(visible)

    def _apply_layout_mode_visibility(self) -> None:
        carousel_mode = self._layout_mode.currentData() == "carousel"
        self._show_brief_page.setVisible(carousel_mode)
        self._show_brief_page_horizontal.setVisible(
            carousel_mode and self._show_brief_page.isChecked()
        )

    def _apply_behind_pace_visibility(self, visible: bool) -> None:
        self._show_catchup_button.setVisible(visible)

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

    def _apply_streak_visibility(self, visible: bool) -> None:
        self._streak_display_mode.setVisible(visible)
        if self._streak_display_label is not None:
            self._streak_display_label.setVisible(visible)

    def _apply_minimalist_mode(self) -> None:
        self._show_motivation.setChecked(False)
        self._show_streaks.setChecked(False)
        self._show_rewards.setChecked(False)
        self._show_catchup_button.setChecked(False)

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
        remove_button.setToolTip("Remove this deck goal page from the settings.")
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
        self.deck.setToolTip("Choose the deck tree this goal page should track, including its subdecks.")
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
        remove_button.setToolTip("Remove this custom goal page from the settings.")
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
        self.title.setToolTip("Name shown for this custom goal on the home screen and in the page list.")
        self.title.textChanged.connect(self._notify_title_changed)
        basics_layout.addRow("Title", self.title)

        self.deck = QComboBox(basics_group)
        self.deck.setToolTip("Choose a single deck tree or track all decks together for this custom goal.")
        self.deck.addItem("All decks", None)
        for deck_name, deck_id in available_decks:
            self.deck.addItem(deck_name, deck_id)
        basics_layout.addRow("Scope", self.deck)

        self.start_date = QDateEdit(basics_group)
        self.start_date.setCalendarPopup(True)
        self.start_date.setDisplayFormat("yyyy-MM-dd")
        self.start_date.setToolTip("The first day included in this custom goal window.")
        self.start_date.dateChanged.connect(self._sync_end_date_from_duration)
        basics_layout.addRow("Starts on", self.start_date)

        self.duration_days = QSpinBox(basics_group)
        self.duration_days.setRange(1, 3650)
        self.duration_days.setSuffix(" days")
        self.duration_days.setToolTip("How many days the custom goal should run for.")
        self.duration_days.valueChanged.connect(self._sync_end_date_from_duration)
        basics_layout.addRow("Duration", self.duration_days)

        self.end_date = QDateEdit(basics_group)
        self.end_date.setCalendarPopup(True)
        self.end_date.setDisplayFormat("yyyy-MM-dd")
        self.end_date.setToolTip("The final day included in this custom goal window.")
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
        self.enabled.setToolTip("Turn this goal on or off without deleting its settings.")
        layout.addRow(self.enabled)

        self.metric = QComboBox(self.group)
        for label, key in _METRIC_OPTIONS:
            self.metric.addItem(label, key)
        self.metric.setToolTip("Choose whether this goal tracks review count, newly learned cards, or study time.")
        layout.addRow("Metric", self.metric)

        self.target = QSpinBox(self.group)
        self.target.setRange(0, 1_000_000)
        self.target.setSingleStep(10)
        self.target.setToolTip("Target amount to reach within this period.")
        layout.addRow("Target", self.target)

        self.rewards = QPlainTextEdit(self.group)
        self.rewards.setPlaceholderText("One reward per line, emojis welcome")
        self.rewards.setToolTip("Write one reward per line. The bar uses these as milestone-style reward messages.")
        self.rewards.setMinimumHeight(120)
        layout.addRow("Rewards", self.rewards)
        self._rewards_label = layout.labelForField(self.rewards)

        self.show_reward = QCheckBox("Show reward badge for this goal", self.group)
        self.show_reward.setChecked(True)
        self.show_reward.setToolTip("Show or hide the reward chip for just this one goal.")
        layout.addRow(self.show_reward)

        self._rewards_hint = QLabel(
            "One reward per line. The widget shows a compact emoji-plus-level chip and reveals the full reward on hover."
        )
        self._rewards_hint.setWordWrap(True)
        layout.addRow("", self._rewards_hint)

        self.year_start_month = QSpinBox(self.group)
        self.year_start_month.setRange(1, 12)
        self.year_start_month.setToolTip("Month when this yearly goal should restart each year.")
        self.year_start_day = QSpinBox(self.group)
        self.year_start_day.setRange(1, 31)
        self.year_start_day.setToolTip("Day when this yearly goal should restart each year.")
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

    if not isinstance(context, (DeckBrowser, Overview, DeckStats)):
        return handled

    if message == _BRIDGE_CMD:
        open_config_dialog()
        return (True, None)

    if not message.startswith(f"{_CATCHUP_CMD}:"):
        return handled

    if _handle_catchup_message(message):
        return (True, None)
    return handled


def _handle_catchup_message(message: str) -> bool:
    try:
        _cmd, raw_deck_id, period, raw_amount = message.split(":", 3)
        deck_id = int(raw_deck_id)
        behind_amount = max(0, int(raw_amount))
    except (TypeError, ValueError):
        return False

    if mw is None or mw.col is None or behind_amount <= 0:
        return True

    deck = mw.col.decks.get(deck_id)
    if not deck:
        showWarning("That deck could not be found anymore.", parent=mw)
        return True

    conf = mw.col.decks.config_dict_for_deck_id(deck_id)
    if not conf:
        showWarning("This deck does not have editable deck options.", parent=mw)
        return True

    current_limit = int(conf["new"]["perDay"])
    deck_name = str(deck["name"])
    title = "Catch Up New Cards"
    prompt = QMessageBox(mw)
    prompt.setWindowTitle(title)
    prompt.setIcon(QMessageBox.Icon.Question)
    prompt.setText(
        f'Your {period} goal for "{deck_name}" is behind by {behind_amount} new cards.\n\n'
        f"Current deck option limit: {current_limit} new cards/day"
    )
    catch_up_now = prompt.addButton("Catch up everything now", QMessageBox.ButtonRole.ActionRole)
    spread_out = prompt.addButton(
        "Catch up over a couple of days/weeks",
        QMessageBox.ButtonRole.ActionRole,
    )
    prompt.addButton(QMessageBox.StandardButton.Cancel)
    prompt.exec()
    clicked = prompt.clickedButton()

    if clicked is catch_up_now:
        _extend_today_new_limit(deck_id, deck_name, behind_amount)
        return True
    if clicked is spread_out:
        _spread_new_limit_increase(deck_id, deck_name, conf, behind_amount)
        return True
    return True


def _extend_today_new_limit(deck_id: int, deck_name: str, amount: int) -> None:
    if mw is None or mw.col is None:
        return
    try:
        mw.col._backend.extend_limits(deck_id=deck_id, new_delta=amount, review_delta=0)
    except Exception as exc:
        showWarning(f"Unable to extend today's new card limit: {exc}", parent=mw)
        return
    mw.reset()
    showInfo(
        f'Increased today\'s new card limit for "{deck_name}" by {amount}.',
        parent=mw,
    )


def _spread_new_limit_increase(deck_id: int, deck_name: str, conf: dict, amount: int) -> None:
    if mw is None or mw.col is None:
        return

    unit_box = QMessageBox(mw)
    unit_box.setWindowTitle("Catch Up Over Time")
    unit_box.setIcon(QMessageBox.Icon.Question)
    unit_box.setText("Spread the catch-up across days or weeks?")
    days_button = unit_box.addButton("Days", QMessageBox.ButtonRole.ActionRole)
    weeks_button = unit_box.addButton("Weeks", QMessageBox.ButtonRole.ActionRole)
    unit_box.addButton(QMessageBox.StandardButton.Cancel)
    unit_box.exec()
    clicked = unit_box.clickedButton()
    if clicked not in (days_button, weeks_button):
        return

    use_weeks = clicked is weeks_button
    count, accepted = QInputDialog.getInt(
        mw,
        "Catch Up Over Time",
        "How many weeks?" if use_weeks else "How many days?",
        2 if use_weeks else 3,
        1,
        52 if use_weeks else 365,
    )
    if not accepted:
        return

    spread_days = count * 7 if use_weeks else count
    extra_per_day = (amount + spread_days - 1) // spread_days
    old_limit = int(conf["new"]["perDay"])
    conf["new"]["perDay"] = old_limit + extra_per_day
    mw.col.decks.save(conf)
    mw.reset()

    affected = len(mw.col.decks.decks_using_config(conf))
    shared_note = (
        f"\n\nThis deck options preset is shared with {affected} decks."
        if affected > 1
        else ""
    )
    showInfo(
        f'Raised the deck option new-card limit for "{deck_name}" from {old_limit} to '
        f'{conf["new"]["perDay"]} per day so you can catch up over the next {spread_days} days.'
        f"{shared_note}",
        parent=mw,
    )

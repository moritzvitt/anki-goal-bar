# Changelog

All notable changes to this project will be documented in this file.

The format is based on Keep a Changelog and this project follows semantic versioning where practical.

## Unreleased

### Added

- Added deck-specific goal groups so weekly, monthly, and yearly progress can be tracked separately for multiple configured decks.
- Added a configurable yearly start month/day while keeping weekly goals anchored to Monday and monthly goals anchored to the first of the month.
- Added an optional one-bar-at-a-time carousel layout with manual cycling controls inside each deck widget for less cluttered home screen widgets.
- Added a richer config dialog for choosing decks, goal metrics, targets, and layout mode.
- Added an optional behind-pace indicator that shows expected progress for the current point in the week, month, or year and highlights the shortfall in subtle red.
- Added reward badges for each goal plus 20 default emoji reward tiers for weekly, monthly, and yearly goals, all editable in the config dialog.
- Added global and per-goal reward visibility toggles, and changed reward badges to compact emoji-plus-level chips that expand on hover.
- Added optional milestone markers for weekly, monthly, and yearly goals, including `1/4`, `1/2`, and `3/4` positions with milestone dates on the bar.
- Added milestone display settings so users can hide milestones globally, toggle specific milestone markers, or show only the next upcoming milestone.
- Added a personal motivation message setting plus an expandable scroll badge next to the home screen settings button.
- Added custom goal pages that can track a personal time window with a custom title, start date, duration, optional end date, and optional deck scope.
- Added streak badges that are earned when goals are completed and reset to zero when the streak breaks.
- Added short and long AnkiWeb product page drafts for publishing and release preparation.
- Added an optional brief carousel page that shows weekly, monthly, and yearly goals together in one compact first view.
- Added an option to show the brief carousel bars side by side horizontally for a more compressed first view.

### Changed

- Updated the home screen config button to use a compact Review Heatmap-style settings icon and button treatment.
- Updated streak badges so they can be hidden entirely or collapsed to the latest badge with the full streak shown on hover, with tooltips that show the exact goal overage reached.
- Updated the default motivation text to the new Japanese learning plan.
- Updated the motivation scroll so it can be hidden from settings, opens as a centered popup on click, and supports Markdown plus inline HTML in the message body.
- Updated the motivation popup styling to look like a larger parchment scroll with better spacing from the dimmed overlay.
- Updated the settings dialog to use a cleaner in-window page layout with a general page and one dedicated page per deck goal group.
- Updated the settings dialog so users can add either deck goal pages or custom goal pages from the same sidebar.
- Updated deck goal group management so users can remove deck pages directly from the settings dialog and keep the config empty if they choose.
- Updated progress calculations to use revlog history scoped to cards in each configured deck tree, including subdecks.
- Updated weekly and monthly behind-pace calculations so new periods start at zero expected progress instead of immediately counting partial-day time.
- Updated weekly milestone labels to use weekday names instead of calendar dates.
- Updated "show only the next milestone" behavior so passed milestone days no longer linger, completed goals fall back to the half milestone, and hidden per-milestone toggles no longer affect next-only mode.
- Updated the milestone settings UI so individual milestone toggles are hidden while "show only the next milestone" is active.
- Updated fresh-install and restore-default behavior to enable weekly, monthly, and yearly goals by default, start in carousel mode, and preselect the most-used deck tree from review history.
- Updated reward chip hover text so the expanded state no longer repeats the reward level label.
- Updated the config dialog so disabling global reward badges also hides the reward editing controls.
- Updated the repository layout to keep runtime Python code under `goal_tracking_progress_bar/` and moved config documentation into `docs/`.
- Updated the README, config docs, architecture notes, and release copy to match the current milestone behavior and smarter default setup.
- Updated root metadata and repo-owned example config files to match the current add-on instead of the original starter template.
- Updated the config docs and AnkiWeb/release copy to describe custom goals, streak badges, and the click-to-open motivation scroll popup.
- Updated the settings dialog so the motivation editor sits directly under the motivation toggle and hides completely when the scroll is disabled.
- Updated reward chips so long reward text opens in a small popover instead of getting cut off.
- Updated all-decks custom goals to use deck IDs correctly and ignore invalid deck IDs instead of crashing rendering.

## 0.1.0 - 2026-03-27

### Added

- Initial Anki add-on starter template.
- Minimal runnable add-on entry point and sample menu action.
- Default Anki config files and documentation placeholders.
- VS Code tasks for validation and packaging.

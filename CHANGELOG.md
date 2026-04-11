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
- Added short and long AnkiWeb product page drafts for publishing and release preparation.

### Changed

- Updated the home screen config button to use a compact Review Heatmap-style settings icon and button treatment.
- Updated progress calculations to use revlog history scoped to cards in each configured deck tree, including subdecks.
- Updated weekly milestone labels to use weekday names instead of calendar dates.
- Updated "show only the next milestone" behavior so passed milestone days no longer linger, completed goals fall back to the half milestone, and hidden per-milestone toggles no longer affect next-only mode.
- Updated the milestone settings UI so individual milestone toggles are hidden while "show only the next milestone" is active.
- Updated fresh-install and restore-default behavior to enable weekly, monthly, and yearly goals by default, start in carousel mode, and preselect the most-used deck tree from review history.
- Updated reward chip hover text so the expanded state no longer repeats the reward level label.
- Updated the config dialog so disabling global reward badges also hides the reward editing controls.
- Updated the repository layout to keep runtime Python code under `goal_tracking_progress_bar/` and moved config documentation into `docs/`.
- Updated the README, config docs, architecture notes, and release copy to match the current milestone behavior and smarter default setup.

## 0.1.0 - 2026-03-27

### Added

- Initial Anki add-on starter template.
- Minimal runnable add-on entry point and sample menu action.
- Default Anki config files and documentation placeholders.
- VS Code tasks for validation and packaging.

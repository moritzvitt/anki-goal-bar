# Architecture

## Overview

Goal Tracking Progress Bar is implemented as a package under `goal_tracking_progress_bar/`. The add-on separates configuration, metrics, rendering, and goal-period logic so the home-screen widget remains configurable without mixing UI and progress calculations.

## Main Entry Points

- `__init__.py`: Anki entry point
- `goal_tracking_progress_bar/addon.py`: bootstrap and hook registration
- `goal_tracking_progress_bar/config_dialog.py`: settings UI
- `goal_tracking_progress_bar/render.py`: home-screen widget rendering

## Main Modules

- `config.py`: config loading and persistence
- `models.py`: goal and view models
- `metrics.py`: progress calculations for reviews, new cards, and study time
- `periods.py`: weekly, monthly, yearly, and custom period helpers
- `service.py`: goal assembly and orchestration

## UI Flow

1. The add-on hooks into the home screen.
2. Configured goals are loaded and grouped.
3. Metric calculations compute current progress values.
4. `render.py` generates the widget HTML for the deck browser.
5. The config dialog updates persisted settings and layout choices.

## Shared Workspace Conventions

- `shared_menu.py`: adds the add-on to the shared menu
- `shared_styling.py`: lets the widget and dialogs use optional global themes

## Supporting Files

- `config.json`: defaults
- `docs/ankiweb-product-page.md`: AnkiWeb description source
- `manifest.json`: Anki metadata

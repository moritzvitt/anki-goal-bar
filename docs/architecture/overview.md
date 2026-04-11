# Architecture Overview

## User-Facing Behavior

The add-on adds a compact goal dashboard to Anki's deck browser home screen. Users can configure one or more deck goal groups, enable weekly, monthly, and yearly goals independently for each deck, and assign each goal one metric:

- `reviews`
- `new_cards`
- `study_minutes`

Each enabled goal renders a label, current value, target value, percentage, and progress bar. Weekly, monthly, and yearly goals can also show optional milestone markers for `1/4`, `1/2`, and `3/4`, either all at once or only the next upcoming milestone. When multiple deck groups are configured, the widget can either show them all or show one deck at a time with manual cycling.

## Hook Registration

- [`goal_tracking_progress_bar/addon.py`](../../goal_tracking_progress_bar/addon.py) registers `aqt.gui_hooks.deck_browser_will_render_content`.
- The widget HTML is appended to `content.stats`, which keeps the integration close to how compact stats widgets are attached by add-ons like Review Heatmap.

## Data Flow

1. `goal_tracking_progress_bar/addon.py` creates `GoalProgressService`.
2. `goal_tracking_progress_bar/service.py` loads config and applies a simple render cache keyed by collection mod time, local day, and config values.
3. `goal_tracking_progress_bar/periods.py` computes local-time week, month, and year boundaries, including milestone dates and a configurable yearly start day.
4. `goal_tracking_progress_bar/metrics.py` queries `revlog` for cards currently in each configured deck tree.
5. `goal_tracking_progress_bar/render.py` builds the compact HTML, CSS, milestone markers, and optional carousel script shown on the home screen.

## Metric Definitions

- `reviews`: number of `revlog` rows in the current period for cards currently in the configured deck tree.
- `new_cards`: cards in that deck tree whose first recorded `revlog` entry falls in the current period.
- `study_minutes`: total `revlog.time` in the period for cards in that deck tree, rounded to whole minutes.

The `new_cards` rule is intentionally simple and documented so it can be refined later if needed.

## Styling

Widget styling lives in [`goal_tracking_progress_bar/render.py`](../../goal_tracking_progress_bar/render.py). The CSS is embedded with the rendered widget and uses a small set of `gpb-*` class names plus a few CSS variables to keep later visual tweaks local.

## Extension Points

- Add new metrics by extending `MetricType` and `GoalMetricsRepository`.
- Add new periods by extending `PeriodKey`, `current_period()`, and the default config.
- Add richer layout modes or interaction controls by expanding `goal_tracking_progress_bar/render.py`.
- Add more deck-selection rules by extending the deck resolution logic in `goal_tracking_progress_bar/service.py`.

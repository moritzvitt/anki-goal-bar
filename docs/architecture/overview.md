# Architecture Overview

## User-Facing Behavior

The add-on adds a compact goal dashboard to Anki's deck browser home screen. Users can configure one or more deck goal groups, create custom goal windows, enable weekly, monthly, yearly, or custom goals, and assign each goal one metric:

- `reviews`
- `new_cards`
- `study_minutes`

Each enabled goal renders a label, current value, target value, percentage, and progress bar. Completed periods can also add streak badges, with either all earned badges shown or only the latest badge shown by default and the rest revealed on hover. Weekly, monthly, and yearly goals can also show optional milestone markers for `1/4`, `1/2`, and `3/4`, either all at once or only the next upcoming milestone. Weekly milestones render weekday labels, while monthly and yearly milestones render calendar dates. When multiple deck groups are configured, the widget can either show them all or show one deck at a time with manual cycling. The toolbar can also show an optional scroll badge to the left of the settings button that opens a centered motivational popup on click.

On first load, the add-on seeds a default deck group for the most-used deck tree it can infer from review history and defaults the layout to carousel mode.

## Hook Registration

- [`goal_tracking_progress_bar/addon.py`](../../goal_tracking_progress_bar/addon.py) registers `aqt.gui_hooks.deck_browser_will_render_content`.
- The widget HTML is appended to `content.stats`, which keeps the integration close to how compact stats widgets are attached by add-ons like Review Heatmap.

## Data Flow

1. `goal_tracking_progress_bar/addon.py` creates `GoalProgressService`.
2. `goal_tracking_progress_bar/service.py` loads config, applies a render cache keyed by collection mod time, active period windows, and config values, selects the next visible milestone based on milestone dates and current goal completion, and derives streak badges from consecutive completed periods.
3. `goal_tracking_progress_bar/periods.py` computes local-time week, month, year, and custom boundaries, including milestone dates and historical period traversal for streaks.
4. `goal_tracking_progress_bar/metrics.py` queries `revlog` for cards currently in each configured deck tree and can load metrics for single historical periods when calculating streaks.
5. `goal_tracking_progress_bar/render.py` builds the compact HTML, CSS, streak badges, milestone markers, optional motivation popup, and optional carousel script shown on the home screen.

## Metric Definitions

- `reviews`: number of `revlog` rows in the current period for cards currently in the configured deck tree.
- `new_cards`: cards in that deck tree whose first recorded `revlog` entry falls in the current period.
- `study_minutes`: total `revlog.time` in the period for cards in that deck tree, rounded to whole minutes.

The `new_cards` rule is intentionally simple and documented so it can be refined later if needed.

## Styling

Widget styling lives in [`goal_tracking_progress_bar/render.py`](../../goal_tracking_progress_bar/render.py). The CSS is embedded with the rendered widget and uses a small set of `gpb-*` class names plus a few CSS variables to keep later visual tweaks local.

The settings UI lives in [`goal_tracking_progress_bar/config_dialog.py`](../../goal_tracking_progress_bar/config_dialog.py) and uses a single dialog with a left-hand page list, a general page for display, streak, and motivation settings, plus dedicated pages for deck goal groups and custom goals.

## Extension Points

- Add new metrics by extending `MetricType` and `GoalMetricsRepository`.
- Add new periods by extending `PeriodKey`, `current_period()`, and the default config.
- Add richer layout modes or interaction controls by expanding `goal_tracking_progress_bar/render.py`.
- Add more deck-selection rules by extending the deck resolution logic in `goal_tracking_progress_bar/service.py`.

# Architecture Overview

## User-Facing Behavior

The add-on adds a compact goal dashboard to Anki's deck browser home screen. Users can enable weekly, monthly, and yearly goals independently and assign each goal one metric:

- `reviews`
- `new_cards`
- `study_minutes`

Each enabled goal renders a label, current value, target value, percentage, and progress bar.

## Hook Registration

- [`addon.py`](../../addon.py) registers `aqt.gui_hooks.deck_browser_will_render_content`.
- The widget HTML is appended to `content.stats`, which keeps the integration close to how compact stats widgets are attached by add-ons like Review Heatmap.

## Data Flow

1. `addon.py` creates `GoalProgressService`.
2. `service.py` loads config and applies a simple render cache keyed by collection mod time, local day, and config values.
3. `periods.py` computes local-time week, month, and year boundaries.
4. `metrics.py` queries `revlog` for the active periods.
5. `render.py` builds the compact HTML and CSS block shown on the home screen.

## Metric Definitions

- `reviews`: number of `revlog` rows in the current period.
- `new_cards`: cards whose first recorded `revlog` entry falls in the current period.
- `study_minutes`: total `revlog.time` in the period, rounded to whole minutes.

The `new_cards` rule is intentionally simple and documented so it can be refined later if needed.

## Styling

Widget styling lives in [`render.py`](../../render.py). The CSS is embedded with the rendered widget and uses a small set of `gpb-*` class names plus a few CSS variables to keep later visual tweaks local.

## Extension Points

- Add new metrics by extending `MetricType` and `GoalMetricsRepository`.
- Add new periods by extending `PeriodKey`, `current_period()`, and the default config.
- Add richer interactions, such as clicking through to detailed stats, by expanding `render.py` and `service.py`.

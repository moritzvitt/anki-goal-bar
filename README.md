# Goal Tracking Progress Bar

An Anki add-on that adds a compact goal dashboard to the deck browser home screen.

It supports optional weekly, monthly, and yearly goals based on:

- reviews completed
- new cards learned
- study time in minutes

The widget is intentionally compact and home-screen friendly, taking visual inspiration from add-ons like Review Heatmap without pulling in its larger feature set.

## File Structure

```text
goal-tracking-progress-bar/
├── __init__.py
├── addon.py
├── config.py
├── config.json
├── config.md
├── manifest.json
├── metrics.py
├── models.py
├── periods.py
├── render.py
├── service.py
└── docs/
```

## How It Works

- [`addon.py`](./addon.py) registers a `deck_browser_will_render_content` hook and appends the widget to the home screen stats area.
- [`service.py`](./service.py) loads config, applies a lightweight cache, computes enabled goals, and returns the final HTML.
- [`metrics.py`](./metrics.py) queries Anki's `revlog` for reviews, first-learned cards, and study time.
- [`render.py`](./render.py) contains the compact HTML and styling for the dashboard.
- [`periods.py`](./periods.py) computes local-time weekly, monthly, and yearly boundaries.

## Config

See [`config.md`](./config.md) for the full schema. Each of `weekly`, `monthly`, and `yearly` can be enabled separately and assigned its own metric and target.

## Notes

- New cards are counted as cards whose first recorded revlog entry falls in the current period.
- Study time is summed from `revlog.time` and rounded to whole minutes.
- Styling lives in [`render.py`](./render.py) so the widget can be adjusted without touching the query logic.

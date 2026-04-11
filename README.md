# Goal Tracking Progress Bar

An Anki add-on that adds a compact goal dashboard to the deck browser home screen.

It supports optional weekly, monthly, and yearly goals for one or more specific decks based on:

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
- [`service.py`](./service.py) loads config, applies a lightweight cache, computes enabled deck groups, and returns the final HTML.
- [`metrics.py`](./metrics.py) queries Anki's `revlog` for reviews, first-learned cards, and study time, scoped to cards currently in each configured deck tree.
- [`render.py`](./render.py) contains the compact HTML, styling, and the one-deck-at-a-time carousel controls.
- [`periods.py`](./periods.py) computes local-time weekly, monthly, and yearly boundaries, including a configurable repeating yearly start month/day.

## Config

See [`config.md`](./config.md) for the full schema. You can configure multiple deck-specific goal groups, choose a global layout mode, and assign separate weekly/monthly/yearly goals to each deck.

## Notes

- Weekly starts on Monday and monthly starts on the first of the month.
- Yearly goals default to January 1 but can be moved to any repeating month/day.
- New cards are counted as cards whose first recorded revlog entry falls in the current period.
- Study time is summed from `revlog.time` and rounded to whole minutes.
- Styling lives in [`render.py`](./render.py) so the widget can be adjusted without touching the query logic.

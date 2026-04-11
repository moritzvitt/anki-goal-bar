# Goal Progress Bars Config

The add-on stores a layout mode plus a list of deck-specific goal groups.

## Top-level keys

### `layout.mode`

One of:

- `all`
- `carousel`

`all` shows every configured deck group at once. `carousel` shows one deck at a time with manual next/previous controls.

### `layout.show_behind_pace`

Set to `true` to show how far behind pace you are for the current point in the week, month, or year.

When enabled, goals that are behind schedule show a subtle red lag segment and a short "Behind pace by ..." note.

### `decks`

Array of deck goal groups. Each entry contains:

- `deck_id`
- `deck_name`
- `weekly`
- `monthly`
- `yearly`

Each period accepts:

- `enabled`
- `metric`
- `target`

The `yearly` section also accepts:

- `start_month`
- `start_day`

Weekly always starts on Monday. Monthly always starts on the 1st. Yearly uses the configured repeating month/day and defaults to January 1.

## Example

```json
{
  "layout": {
    "mode": "carousel",
    "show_behind_pace": true
  },
  "decks": [
    {
      "deck_id": 1234567890,
      "deck_name": "Spanish",
      "weekly": {
        "enabled": true,
        "metric": "reviews",
        "target": 400
      },
      "monthly": {
        "enabled": true,
        "metric": "study_minutes",
        "target": 600
      },
      "yearly": {
        "enabled": true,
        "metric": "new_cards",
        "target": 1500,
        "start_month": 7,
        "start_day": 1
      }
    }
  ]
}
```

## Metric Notes

- `reviews` counts revlog entries for cards currently in the configured deck tree.
- `new_cards` counts cards in that deck tree whose first recorded revlog entry falls in the period.
- `study_minutes` sums revlog study time for cards in that deck tree and rounds to whole minutes.

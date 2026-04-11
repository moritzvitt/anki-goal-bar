# Goal Progress Bars Config

The add-on stores one config object per goal period.

## Goal keys

### `weekly`
### `monthly`
### `yearly`

Each period accepts:

### `enabled`

Set to `true` to show that goal on Anki's home screen.

### `metric`

One of:

- `reviews`
- `new_cards`
- `study_minutes`

### `target`

Positive integer target for the selected metric.

## Example

```json
{
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
    "enabled": false,
    "metric": "new_cards",
    "target": 2000
  }
}
```

## Metric Notes

- `reviews` counts revlog entries in the current week, month, or year.
- `new_cards` counts cards whose first recorded revlog entry falls in that period.
- `study_minutes` sums revlog study time and rounds to whole minutes.

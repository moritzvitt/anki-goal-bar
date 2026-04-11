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

### `layout.show_rewards`

Set to `false` to hide all reward badges globally, even if individual goals still have reward badges enabled.

### `layout.show_milestones`

Set to `false` to hide all milestone markers globally.

Milestones are shown for weekly, monthly, and yearly goals.

### `layout.milestones`

Object with per-milestone toggles:

- `quarter`
- `half`
- `three_quarter`

This lets you show only the milestone markers you want, for example just `half` and `three_quarter`.

These per-milestone toggles apply when `layout.milestone_display_mode` is `all`. In `next` mode, the add-on automatically picks the next milestone from the standard `quarter`, `half`, `three_quarter` sequence.

### `layout.milestone_display_mode`

One of:

- `all`
- `next`

`all` shows every enabled milestone for weekly, monthly, and yearly goals.

`next` only shows the next upcoming milestone for the current period.

Passed milestone days stop showing immediately once that milestone day has been reached.

If the goal is already complete, `next` mode falls back to showing the `half` milestone.

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
- `rewards`
- `show_reward`

The `yearly` section also accepts:

- `start_month`
- `start_day`

Weekly always starts on Monday. Monthly always starts on the 1st. Yearly uses the configured repeating month/day and defaults to January 1.

Weekly milestones use weekday names like `Monday` and `Wednesday`. Monthly and yearly milestones use calendar dates like `14. June`, with a compact `14.06` display on tighter layouts.

`rewards` is a list of reward strings shown as a badge on the widget. The add-on ships with 20 funny default rewards for each period, and users can replace them with their own list. One reward per line in the config dialog becomes one entry in this list.

`show_reward` lets you hide the reward badge for one specific goal while keeping rewards visible elsewhere.

## Example

```json
{
  "layout": {
    "mode": "carousel",
    "show_behind_pace": true,
    "show_rewards": true,
    "show_milestones": true,
    "milestone_display_mode": "next",
    "milestones": {
      "quarter": true,
      "half": true,
      "three_quarter": false
    }
  },
  "decks": [
    {
      "deck_id": 1234567890,
      "deck_name": "Spanish",
      "weekly": {
        "enabled": true,
        "metric": "reviews",
        "target": 400,
        "show_reward": true,
        "rewards": [
          "🍦 Have ice cream for no academically valid reason",
          "🎉 Throw yourself a microscopic parade of triumph"
        ]
      },
      "monthly": {
        "enabled": true,
        "metric": "study_minutes",
        "target": 600,
        "show_reward": false,
        "rewards": [
          "🍣 Go out for sushi and order one mysterious roll",
          "✈️ Take yourself on a glorious mini vacation mission"
        ]
      },
      "yearly": {
        "enabled": true,
        "metric": "new_cards",
        "target": 1500,
        "start_month": 7,
        "start_day": 1,
        "show_reward": true,
        "rewards": [
          "🎒 Take a proud day off and disappear into a museum",
          "🇯🇵 Holiday in Japan and live your final-form montage"
        ]
      }
    }
  ]
}
```

## Metric Notes

- `reviews` counts revlog entries for cards currently in the configured deck tree.
- `new_cards` counts cards in that deck tree whose first recorded revlog entry falls in the period.
- `study_minutes` sums revlog study time for cards in that deck tree and rounds to whole minutes.

## Default Behavior

- Fresh installs default to `carousel` layout.
- Weekly, monthly, and yearly goals are enabled by default.
- The initial deck group is seeded from the most-used deck tree based on review history, falling back to Anki's current deck when needed.

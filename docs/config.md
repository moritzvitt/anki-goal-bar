# Goal Progress Bars Config

The add-on stores global display settings, deck goal groups, and optional custom goal windows.

## Top-level keys

### `layout.mode`

One of:

- `all`
- `carousel`

`all` shows every configured deck group at once. `carousel` shows one deck at a time with manual next/previous controls.

### `layout.show_behind_pace`

Set to `true` to show how far behind pace you are for the current point in the week, month, or year.

When enabled, goals that are behind schedule show a subtle red lag segment and a short "Behind pace by ..." note.

Weekly and monthly behind-pace use completed days, so a fresh week or month starts at zero expected progress.

### `layout.show_motivation`

Set to `false` to hide the motivation scroll button entirely.

### `layout.show_rewards`

Set to `false` to hide all reward badges globally, even if individual goals still have reward badges enabled.

### `layout.show_milestones`

Set to `false` to hide all milestone markers globally.

Milestones are shown for weekly, monthly, and yearly goals.

### `layout.show_streaks`

Set to `false` to hide streak badges globally.

### `layout.streak_display_mode`

One of:

- `all`
- `last`

`all` shows every earned streak badge for a goal.

`last` shows only the latest earned badge by default and reveals the full streak on hover.

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

### `layout.motivation`

Free-form string for the personal motivational text shown in the home-screen scroll popup.

The scroll button sits to the left of the settings button, always uses the tooltip text `my Motivation`, opens on click, and supports Markdown plus inline HTML in the popup body.

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

### `custom_goals`

Array of custom goal windows. Each entry contains:

- `title`
- `deck_id`
- `deck_name`
- `custom`

The `custom` object accepts:

- `enabled`
- `metric`
- `target`
- `start_year`
- `start_month`
- `start_day`
- `duration_days`
- `rewards`
- `show_reward`

Custom goals can target all decks by setting `deck_id` to `null`, or scope to one configured deck tree.

The config dialog also offers an `Ends on` field, but it is stored as `start_*` plus `duration_days`.

## Example

```json
{
  "layout": {
    "mode": "carousel",
    "show_behind_pace": true,
    "show_motivation": true,
    "show_streaks": true,
    "streak_display_mode": "last",
    "show_rewards": true,
    "show_milestones": true,
    "milestone_display_mode": "next",
    "motivation": "Keep going. Each review is a vote for the version of you that remembers.",
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
  ],
  "custom_goals": [
    {
      "title": "Spring Reading Push",
      "deck_id": null,
      "deck_name": "",
      "custom": {
        "enabled": true,
        "metric": "study_minutes",
        "target": 900,
        "start_year": 2026,
        "start_month": 4,
        "start_day": 15,
        "duration_days": 30,
        "show_reward": true,
        "rewards": [
          "📚 Buy the novel you've been saving for later",
          "🍜 Celebrate with elite ramen"
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

## Streak Notes

Streak badges are earned when consecutive completed periods meet or exceed the configured target.

If the most recent completed period misses the target, the streak resets to zero.

Badge tooltips show the exact value reached for that completed period, for example `120/100 reviews`.

## Default Behavior

- Fresh installs default to `carousel` layout.
- Weekly, monthly, and yearly goals are enabled by default.
- Fresh installs include a default personal motivation message for the home-screen scroll badge.
- Fresh installs show streak badges and motivation by default.
- The initial deck group is seeded from the most-used deck tree based on review history, falling back to Anki's current deck when needed.

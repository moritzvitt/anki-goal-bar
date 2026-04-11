# Goal Tracking Progress Bar

Goal Tracking Progress Bar adds a compact goal dashboard to Anki's home screen so you can track real study targets without leaving the deck browser.

It is designed for people who want a cleaner, more goal-oriented view of progress than Anki's default home screen provides.

<p align="center">
  <img src="https://raw.githubusercontent.com/moritzvitt/anki-goal-bar/main/media/goal-progress-widget.png" alt="Goal progress widget" width="900">
</p>

<p align="center">
  <img src="https://raw.githubusercontent.com/moritzvitt/anki-goal-bar/main/media/goal-progress-home-screen.png" alt="Goal progress widget on Anki home screen" width="900">
</p>

## What It Does

The add-on shows polished progress bars on the main deck browser for configurable goals such as:

- weekly goals
- monthly goals
- yearly goals

Each goal can use one of these metrics:

- reviews completed
- new cards learned
- study time in minutes

## Deck-Specific Goals

You can create separate goal groups for specific decks.

Examples:

- one set of goals for `Japanese`
- another set for `Medical School`
- another set for `Spanish::Listening`

Progress is calculated from the review history of cards in that configured deck tree, including subdecks.

## Flexible Yearly Goals

Weekly goals always start on Monday.

Monthly goals always start on the 1st of the month.

Yearly goals can start on a custom month/day, which makes the add-on useful for:

- school years
- fiscal years
- language-learning challenges
- personal study seasons

## Layout Options

If you only track one deck, the widget stays compact and simple.

If you track multiple decks, you can choose between:

- showing all configured deck goal groups at once
- showing one goal bar at a time and cycling manually within a deck

This helps keep Anki's home screen from getting cluttered.

## Visual Style

The widget is intentionally compact, polished, and native-feeling.

It is inspired by the home screen presentation style of add-ons like Review Heatmap:

- compact controls
- readable spacing
- subtle progress styling
- a dashboard feel that fits naturally into Anki

## Configuration

The add-on includes a built-in config dialog where you can:

- add or remove deck goal groups
- choose the target deck for each group
- enable or disable weekly, monthly, and yearly goals independently
- choose the metric for each goal
- set the target value for each goal
- choose the yearly start month/day
- switch between full and one-bar-at-a-time layouts

## Notes

- `reviews completed` counts review log entries in the active time window
- `new cards learned` uses the first recorded review log entry for each card as the learn date
- `study time in minutes` sums study time from Anki's review log

## Good Fit For

- students with weekly review targets
- language learners tracking progress per deck
- people balancing multiple long-term study projects
- anyone who wants visible deck-specific goals directly on the home screen

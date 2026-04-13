# Goal Tracking Progress Bar

Goal Tracking Progress Bar adds compact deck-based and custom goal bars directly to Anki's home screen.

It is for people who want a clearer, more goal-oriented overview of their study progress without leaving the deck browser.

<p align="center">
  <img src="https://raw.githubusercontent.com/moritzvitt/anki-goal-bar/refs/heads/main/media/anki-goal-bar-widget-overview.png" alt="Goal Tracking Progress Bar widget overview" width="900">
</p>

<p align="center">
  <img src="https://raw.githubusercontent.com/moritzvitt/anki-goal-bar/refs/heads/main/media/anki-goal-bar-home-screen.png" alt="Goal Tracking Progress Bar on the Anki home screen" width="900">
</p>

## Main Features

- Weekly, monthly, yearly, and custom goals on the home screen
- Separate goal groups for specific decks
- Custom goal windows with your own start date and duration
- Goals based on reviews, new cards, or study time
- Optional milestone markers for `1/4`, `1/2`, and `3/4` progress
- Optional custom yearly start date
- Optional streak badges for completed goals
- Optional one-bar-at-a-time layout with manual cycling
- Optional behind-pace indicator with a subtle red lag marker
- Optional motivation scroll popup with editable rich text

## Per-Deck Goals

Instead of tracking only one collection-wide target, you can create separate goal groups for different decks.

Examples:

- `Japanese`
- `Medical School`
- `Spanish::Listening`

Progress is calculated from the review history of cards in the configured deck tree, including subdecks.

## Goal Types

Each goal can use one of these metrics:

- reviews completed
- new cards learned
- study time in minutes

That makes the add-on useful for different study styles:

- review-volume goals
- learning-new-material goals
- time-based consistency goals

## Flexible Time Windows

Weekly goals always start on Monday.

Monthly goals always start on the 1st.

Yearly goals can start on a custom month/day, which makes the add-on useful for:

- school years
- fiscal years
- long-term study challenges
- personal learning cycles

Custom goals can use a personal start date plus duration, with the config dialog also letting you edit an end date directly.

Weekly milestones use weekday names, while monthly and yearly milestones show calendar dates.

## Layout Options

If you like a fuller dashboard, you can show all enabled goal bars at once.

If you prefer a cleaner home screen, you can switch to a one-bar-at-a-time layout and cycle through the goals manually with arrow buttons.

Fresh installs default to this carousel-style layout and try to preselect the deck tree you use most based on review history.

## Visual Style

The widget is designed to feel at home in Anki:

- compact
- polished
- readable
- unobtrusive on the home screen

It takes inspiration from the compact dashboard feel of add-ons like Review Heatmap while staying focused on goal tracking.

## Configuration

The built-in config dialog lets you:

- add or remove deck goal groups
- add or remove custom goal windows
- choose the target deck for each group
- enable or disable weekly, monthly, and yearly goals independently
- choose a custom goal title, start date, duration, and optional deck scope
- choose the metric for each goal
- set the target value for each goal
- choose the yearly start month/day
- show or hide the motivation scroll
- show all streak badges, only the latest badge, or hide them entirely
- switch between full and one-bar-at-a-time layouts
- show all milestone markers or only the next upcoming milestone
- enable a behind-pace indicator

## Notes

- `reviews completed` counts review log entries in the active time window
- `new cards learned` uses the first recorded review log entry for each card as the learn date
- `study time in minutes` sums study time from Anki's review log
- weekly and monthly behind-pace start at zero on a fresh period and then advance by completed days
- streak badges reset when the most recent completed period misses the target
- next-only milestone mode hides passed milestone days and falls back to the half milestone when a goal is already complete

## Good Fit For

- students with weekly review targets
- language learners tracking progress per deck
- people balancing multiple long-term study projects
- anyone who wants visible deck-specific goals directly on the home screen

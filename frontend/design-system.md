# Design System — Mentor Bads

Reference for consistent UI across the app. All tokens are defined in `src/styles/global.css` as CSS custom properties.

## Colors

| Token              | Value       | Usage                          |
|--------------------|-------------|--------------------------------|
| `--primary`        | `#2379fb`   | Actions, links, active states  |
| `--primary-light`  | `#e8f0fe`   | Chips, light backgrounds       |
| `--bg`             | `#ffffff`   | Page & card background         |
| `--surface`        | `#f2f2f7`   | Secondary backgrounds, borders |
| `--text`           | `#111111`   | Primary text                   |
| `--text-secondary` | `#6c6c70`   | Labels, hints, meta text       |
| `--success`        | `#34c759`   | Positive / taken               |
| `--danger`         | `#ff3b30`   | Negative / skipped / delete    |
| `--warning`        | `#ff9500`   | Low stock, alerts              |

### Badge palette (status-specific)

| Class           | Background | Text      |
|-----------------|------------|-----------|
| `.badge-taken`  | `#d1fae5`  | `#065f46` |
| `.badge-skipped`| `#fee2e2`  | `#991b1b` |
| `.badge-pending`| `#fef3c7`  | `#92400e` |
| `.badge-snoozed`| `#ede9fe`  | `#4c1d95` |

## Typography

| Element          | Size   | Weight | Notes                        |
|------------------|--------|--------|------------------------------|
| Body             | 16px   | 400    | `line-height: 1.5`          |
| `.page-title`    | 22px   | 700    |                              |
| `.modal-title`   | 18px   | 700    |                              |
| `.section-label` | 12px   | 600    | `color: --text-secondary`, `letter-spacing: 0.3px` |
| `.input-label`   | 13px   | 500    | `color: --text-secondary`    |
| `.btn`           | 15px   | 600    |                              |
| `.btn-sm`        | 13px   | 600    |                              |
| `.btn-ghost`     | 14px   | 600    |                              |
| `.badge`         | 12px   | 600    |                              |
| `.empty-text`    | 15px   | 400    |                              |
| `.nav-label`     | 10px   | 500    |                              |

**Font stack:** `'SF Pro Display', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif`

**No uppercase.** All text uses sentence case.

## Spacing

| Token          | Value  | Usage                          |
|----------------|--------|--------------------------------|
| Page padding   | 16px   | `.page` horizontal padding     |
| Page top       | 20px   | `.page` top padding            |
| Card padding   | 16px   | `.card`, all `*-card` blocks   |
| Card gap       | 10px   | `margin-bottom` between cards  |
| Section gap    | 24px   | `.section` margin-bottom       |
| Input group    | 16px   | `.input-group` margin-bottom   |

## Radii

| Token          | Value  | Usage                        |
|----------------|--------|------------------------------|
| `--radius`     | 9px    | Buttons, inputs, progress    |
| `--radius-lg`  | 16px   | Cards, modal sheet           |
| Pill           | 20px   | Badges, chips                |
| Circle         | 50%    | FAB, stepper buttons         |

## Shadows

| Token      | Value                                         | Usage                |
|------------|-----------------------------------------------|----------------------|
| `--shadow` | `0px 4px 20px -4px rgba(0, 11, 48, 0.12)`    | Cards                |
| FAB shadow | `0 4px 16px rgba(35, 121, 251, 0.4)`         | Floating action btn  |

## Icons

Library: **lucide-react** (tree-shakeable SVG icons).

| Context        | Size | strokeWidth | Notes                              |
|----------------|------|-------------|------------------------------------|
| Bottom nav     | 22   | 1.8 / 2.2  | 2.2 for active tab                 |
| Empty state    | 48   | 1.5         | Centered, `color: --text-secondary`|
| Inline in text | 12-13| default     | Used in chips, meta, stats         |
| Action buttons | 14   | default     | Inside `.btn` with `gap: 6px`      |

**Icon map:**

| Concept     | Icon            |
|-------------|-----------------|
| Today       | `CalendarCheck` |
| Supplements | `Pill`          |
| Stock       | `Package`       |
| Statistics  | `BarChart3`     |
| Taken       | `Check`         |
| Skipped / Close | `X`         |
| Time / Snooze | `Clock`       |
| Delete      | `Trash2`        |
| Warning     | `AlertTriangle` |
| Edit        | `Pencil`        |
| Add         | `Plus`          |

## Components

### Buttons

| Variant      | Class                 | Bg              | Text          |
|--------------|-----------------------|-----------------|---------------|
| Primary      | `.btn .btn-primary`   | `--primary`     | white         |
| Secondary    | `.btn .btn-secondary` | `--surface`     | `--text`      |
| Danger       | `.btn .btn-danger`    | `--danger`      | white         |
| Ghost        | `.btn .btn-ghost`     | transparent     | `--primary`   |
| Small        | add `.btn-sm`         | -               | smaller padding/font |
| Disabled     | `:disabled`           | opacity 0.4     |               |

Active state: `scale(0.97)`, `opacity: 0.85`.

### Cards

All cards follow the same pattern:
- `background: var(--bg)`
- `border-radius: var(--radius-lg)` (16px)
- `padding: 16px`
- `margin-bottom: 10px`
- `box-shadow: var(--shadow)`

Defined per-page (`.today-card`, `.sup-card`, `.stock-card`, `.stats-card`) but share identical base styles.

### Chips

| Type       | Bg               | Text          | Radius |
|------------|------------------|---------------|--------|
| Time chip  | `--primary-light`| `--primary`   | 20px   |
| Low badge  | `#fff3e0`        | `--warning`   | 20px   |

All chips: `display: inline-flex; align-items: center; gap: 4px; font-size: 12px; font-weight: 600`.

### Inputs

- Border: `1.5px solid var(--surface)`
- Focus: `border-color: var(--primary)`
- Padding: `12px 14px`
- Font size: 15px

### Bottom Nav

- Height: `var(--nav-height)` (68px)
- Background: `rgba(255, 255, 255, 0.92)` with `backdrop-filter: blur(12px)`
- Fixed to bottom, z-index: 150

### Modal (bottom sheet)

- Overlay: `rgba(0,0,0,0.4)`, z-index: 200
- Sheet: slides up from bottom, `border-radius: 16px 16px 0 0`
- Handle bar: 36x4px centered, `--surface` color

### FAB

- 52x52px circle, fixed bottom-right
- `bottom: calc(var(--nav-height) + 16px)`
- z-index: 100

### Progress bar

- Height: 6px, `--radius` border-radius
- Track: `--surface`, fill: `--primary` (or `--warning` when low)

## Z-index scale

| Layer        | z-index |
|--------------|---------|
| FAB          | 100     |
| Bottom nav   | 150     |
| Modal overlay| 200     |

## Transitions

Standard duration: `0.15s`. Easing: default (ease) or `ease` for slide animations.

| Property   | Duration | Usage              |
|------------|----------|--------------------|
| color      | 0.15s    | Nav items, links   |
| transform  | 0.1-0.15s| Button press       |
| opacity    | 0.15s    | Button press       |
| border     | 0.15s    | Input focus        |
| width      | 0.4s     | Progress fill      |
| slideUp    | 0.25s    | Modal entrance     |

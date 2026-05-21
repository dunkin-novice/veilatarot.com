# Veila Quick Love Reading — GA4 Reporting Spec v1

**Scope:** `/quick-love-reading/` (EN + TH, single URL)
**Covers product state after:** Question Presets v1, Daily Reflection Loop v1, Manual Card Selection v1, Arc Mode v1, Share Poster v2.
**Owner:** Veila product analytics.
**Status:** v1 — first measurement contract for the love-reading loop. Revise when new modes, free-text questions, or backend persistence ship.

---

## 1. Core funnel

A single, ordered funnel measured per **session × language**. Each step is the count of distinct sessions in which that event fired at least once.

| # | Step | GA4 event (canonical) | Drop-off it measures |
|---|---|---|---|
| 1 | Selection started | `love_card_selection_started` | Landed but did not engage with the deck |
| 2 | 3 cards selected | `love_card_selection_completed` | Picked < 3 (abandonment mid-selection) |
| 3 | Reveal started | `love_manual_reveal_started` | Reached 3 but did not tap Reveal |
| 4 | Reading completed | `love_reading_completed` | Started reveal but left before all 3 flipped |
| 5 | Share / save action | `love_reading_saved` **OR** `love_reading_shared` **OR** `love_reading_link_copied` | Completed but did not externalise the reading |
| 6 | Return reflection viewed | `reflection_return_viewed` | New session on a later day with no return-panel impression |
| 7 | Repeat started | `reflection_repeat_started` | Saw the return panel but did not tap the repeat CTA |

**Notes**
- Steps 1–5 are measured **within one session**; step 6 starts a **new session on a later local day**; step 7 is also new-session.
- Use `love_card_selection_completed` **last-occurrence** per session — the event re-fires if a user deselects then re-reaches 3.
- Step 5 is the **union** of the three terminal share/save events (see §5).
- `love_reading_started` is intentionally co-fired with `love_manual_reveal_started` for legacy v1 parity — pick **one** of the two as the funnel anchor (recommend `love_manual_reveal_started`, since it carries `card_ids`).

---

## 2. Key metrics

All rates are session-based unless stated. Denominator is the session count of the **previous** funnel step (or page_view of `/quick-love-reading/` for `selection_start_rate`).

| Metric | Formula | What it tells you |
|---|---|---|
| `selection_start_rate` | sessions with `love_card_selection_started` ÷ sessions with `page_view` on `/quick-love-reading/` | Intro → selection conversion (Start CTA strength) |
| `card_selection_completion_rate` | sessions with `love_card_selection_completed` ÷ sessions with `love_card_selection_started` | How many engaged users finish a 3-pick |
| `reveal_rate` | sessions with `love_manual_reveal_started` ÷ sessions with `love_card_selection_completed` | Friction between "ready" state and the Reveal tap |
| `reading_completion_rate` | sessions with `love_reading_completed` ÷ sessions with `love_manual_reveal_started` | Drop-off during the stagger flip / scroll-into-view |
| `share_or_save_rate` | sessions with **any** of {`love_reading_saved`, `love_reading_shared`, `love_reading_link_copied`} ÷ sessions with `love_reading_completed` | Reading → externalisation conversion |
| `return_view_rate` | sessions with `reflection_return_viewed` ÷ users with ≥1 prior `reflection_saved` who returned on a later local day | "Did the loop bring them back?" |
| `repeat_reflection_rate` | sessions with `reflection_repeat_started` ÷ sessions with `reflection_return_viewed` | Return panel → loop-close conversion |
| `spread_mode_distribution` | share of `love_card_selection_started` (and of `love_reading_completed`) by `spread_mode` | Which Arc Mode users actually pick |
| `question_key_distribution` | share of `love_question_selected` by `question_key` + share of `love_reading_completed` where `question_key` is set | Which presets resonate; how often readings run with no preset |

**Secondary / quality metrics**

| Metric | Formula | Why |
|---|---|---|
| `reversed_rate` | avg(`reversed_count`) on `love_reading_completed` ÷ 3 | Sanity check on the ~32% reversal probability |
| `mode_change_rate` | sessions with ≥1 `love_spread_mode_selected` ÷ sessions with `love_card_selection_started` | How often users deviate from the default Connection mode (lower bound — see §5) |
| `ios_save_proxy_rate` | sessions on iOS with `love_reading_shared` ÷ iOS sessions with `love_reading_completed` | Replaces `love_reading_saved` on iOS where the Download button is hidden |

---

## 3. Segments

All metrics in §2 should be sliceable by:

| Segment | Source | Notes |
|---|---|---|
| `lang` | event param on every love event | `en` / `th` — primary product split |
| `spread_mode` | event param on every post-selection event | `connection`, `emotional-arc`, `clarity`, `reconnection` — read from `love_card_selection_started` for mode-attribution (§5) |
| `question_key` | event param on every event after the chip is tapped | Includes the 6 preset keys plus "" (skipped) |
| Device class | GA4 built-in `device_category` | `mobile` vs `desktop` (tablet folds into desktop for this product) |
| New vs returning users | GA4 built-in `new_vs_returning` | First-touch users vs repeat visitors |
| `days_since` previous reading | event param `days_since` on `reflection_return_viewed` / `reflection_repeat_started` | Bucket as `1`, `2–3`, `4–7`, `8+` |

**Cross-cuts of interest**
- `lang × spread_mode` — does TH skew toward `connection` while EN tries Arc Modes?
- `device_category × share_or_save_rate` — iOS share/save composition vs Android/desktop.
- `days_since × repeat_reflection_rate` — does the loop decay with time away?
- `question_key × reading_completion_rate` — do certain questions correlate with abandonment?

---

## 4. Dashboard layout

A single **Quick Love Reading** report in GA4 Explore (or Looker Studio), grouped into the panels below. All panels respect the global date-range and lang filter.

### 4.1 Top KPI cards (single row, 6 tiles)

| Tile | Metric | Comparison |
|---|---|---|
| 1 | Sessions starting selection | count | vs prior period |
| 2 | Completion → 3 cards | `card_selection_completion_rate` | vs prior period |
| 3 | Readings completed | count | vs prior period |
| 4 | Share/save rate | `share_or_save_rate` | vs prior period |
| 5 | Return-view rate (D+1 cohort) | `return_view_rate` | vs prior period |
| 6 | Repeat reflection rate | `repeat_reflection_rate` | vs prior period |

### 4.2 Funnel chart

Vertical 7-step funnel matching §1. Each bar shows session count + step-over-step retention %. Configurable breakdown by `lang` or `spread_mode`.

### 4.3 Spread mode table

| spread_mode | sessions started | reached 3 | completed | shared/saved | completion rate | share/save rate |
|---|---|---|---|---|---|---|
| connection | … | … | … | … | … | … |
| emotional-arc | … | … | … | … | … | … |
| clarity | … | … | … | … | … | … |
| reconnection | … | … | … | … | … | … |

Mode attribution = `spread_mode` param on `love_card_selection_started` (see §5).

### 4.4 Question table

| question_key | times selected | readings with this key | completion rate | share/save rate |
|---|---|---|---|---|
| their-energy | … | … | … | … |
| honest | … | … | … | … |
| *(others)* | … | … | … | … |
| *(none / skipped)* | n/a | … | … | … |

`(none / skipped)` row is built from `love_reading_completed` where `question_key = ""`.

### 4.5 Share/save breakdown

Stacked horizontal bar, one row per `lang × device_category`:

- `love_reading_shared` (native share — primary on mobile)
- `love_reading_saved` (download — desktop + Android only by design)
- `love_reading_link_copied` (copy-link fallback)

Annotation: "iOS Download button is intentionally hidden; expect 0 saves and elevated shared/copied on iOS." See §5.

### 4.6 Return loop panel

Two-row layout.

**Row A — Loop close**
- `reflection_saved` count (today's cohort)
- `reflection_return_viewed` count (next-day cohort, lagged 1 day)
- `reflection_repeat_started` count
- `return_view_rate` and `repeat_reflection_rate` as KPI tiles

**Row B — Time-to-return distribution**
Histogram of `days_since` from `reflection_return_viewed`, bucketed `1 / 2–3 / 4–7 / 8+`.

### 4.7 Thai vs English comparison

Side-by-side mirror of the funnel (§4.2) and the top KPI strip (§4.1) — one column for `lang = th`, one for `lang = en`. Surfaces voice/translation-quality issues that show up as different drop-off shapes per language.

---

## 5. GA4 implementation notes

These are non-obvious gotchas — bake them into every query and saved exploration.

### 5.1 Mode attribution: don't count `love_spread_mode_selected`

`love_spread_mode_selected` **only fires when the user changes away from the default `connection`** (`selectMode()` early-returns on `modeKey === selectedMode`). Counting that event will undercount the true `connection` slice by exactly the number of users who accepted the default.

→ **Use `love_card_selection_started`** as the canonical mode-attribution event. Its `spread_mode` param is always present and reflects the user's active choice when they engage with the deck.

### 5.2 Share/save is a union, not three separate steps

iOS Safari ignores the anchor `download` attribute on blob URLs, so the share sheet **hides the Download button entirely on iOS**. That means `love_reading_saved` is structurally undercounted on iOS — using it alone for "did the user save?" biases the funnel against iOS users.

→ Step 5 of the funnel and `share_or_save_rate` must be computed as the **union** of `love_reading_saved`, `love_reading_shared`, and `love_reading_link_copied`. In GA4 Explore use a segment with OR conditions; in BigQuery use `event_name IN (…)`.

### 5.3 Re-selection noise in `love_card_selection_completed`

The event fires every time selected-count crosses to 3. A user who picks 3, deselects one, picks again, re-fires the event.

→ For session-level "reached 3 picks", use **last occurrence per session** (or `COUNT(DISTINCT session_id)` rather than `COUNT(event_name)`).

### 5.4 `love_reading_started` and `love_manual_reveal_started` are co-fired

Both fire in the same `onReveal()` block as a deliberate v1-compat measure. Treat them as the **same step**; do not sum them.

→ Recommended: use `love_manual_reveal_started` (carries `card_ids`); keep `love_reading_started` only as the legacy v1 funnel anchor.

### 5.5 `love_reading_completed` and `reflection_saved` can re-fire in one session

There is no per-day dedupe on completion or save. A user who runs two readings in one page session triggers both events twice.

→ For unique-reading-per-session metrics, use `COUNT(DISTINCT session_id)`. For "readings per session" as a quality metric, use `COUNT(event_name)`.

### 5.6 `reflection_return_viewed` is throttled to once-per-page-load

Guarded by a DOM `dataset.fired` flag, so language toggles and `restart()` do not re-fire it.

→ Safe to count raw event volume; session count and event count will match.

### 5.7 `love_question_selected` does not fire on deselect

Tapping the same chip a second time toggles the preset off silently. There is no `_deselected` companion.

→ "Sessions with a question chosen" should be measured as `COUNT(DISTINCT session_id WHERE event_name = 'love_question_selected')`, and **don't** infer skip-rate from event volume alone — a user can fire `love_question_selected` and still end up running the reading with no preset selected.

### 5.8 Aborted native share does not fire `love_reading_shared`

The share-sheet handler suppresses `AbortError` (the user cancelling the system share sheet). Only successful shares are counted.

→ `share_or_save_rate` correctly excludes abandoned shares — no adjustment needed, but note it for definition.

---

## 6. Open questions for v2

- Add `previous_spread_mode` to `reflection_return_viewed` and `reflection_repeat_started` to enable mode-pivot return analysis.
- Add `card_ids` to `love_reading_started` for parity with the manual-reveal event.
- Add `previous_mode` to `love_spread_mode_selected` to measure mode-shopping behaviour.
- Per-day dedupe of `reflection_saved` if loop-quality analysis becomes important.
- Consider an `engaged_session` GA4 condition tuned to this product (current default may misclassify short, intentional reflective sessions).

---

*v1 — locked against PR #33 (Quick Love Reading: share poster v2). No code changes required to implement this report.*

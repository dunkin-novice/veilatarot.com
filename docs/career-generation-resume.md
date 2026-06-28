# Career vertical — generation state

**COMPLETE as of 2026-06-26.** All 18/18 career-reading datasets generated,
validated (78 cards each, every EN/TH slot filled), on disk, and wired into
`/career/reading/`. The 14-wide fan-out hit the session limit mid-run (8 came
back partial); those 8 were resumed **one-at-a-time** via `resumeFromRunId`
(completed card-batches cached, only missing cards re-ran) and collected.

## All 18 (on disk, wired)
should-i-take-this-job · should-i-quit · is-this-career-right · am-i-underpaid ·
will-money-improve · should-i-ask-for-a-raise · change-careers · why-is-work-stuck ·
whats-blocking-my-success · should-i-start-my-own-thing · is-this-offer-good ·
how-to-grow-here · are-they-valuing-me · should-i-wait-or-move · what-is-my-calling ·
how-to-handle-money-fear · will-this-project-land · should-i-go-back-to-study

## App build + de-love (done 2026-06-26)
`build-career-reading-app.py` clones `/quick-love-reading/` → `/career/reading/`.
Beyond the copy swap it now also (all in the `structural` dict, regeneratable):
- **Removes the love spread-mode picker** (connection/emotional-arc/clarity/
  reconnection) — career questions each carry their own fixed 3 positions, so
  there is no lens to choose. `currentPositions()` is overridden to read the
  selected question's `dataset.spread.positions`, which cascades to the
  selection "Next:" label, the draw mapping, and the share subtitle.
- Refreshes the selection UI when a dataset finishes loading mid-screen.
- Repoints the **Continue-reflecting** block from love pages → career questions.
- **Hides** the love-authored **Emotional Weather** + **Quiet Pause** ambient
  layers (career banks = future content task).
- Neutralizes `posTrail`; repoints "Spreads to try" → "More questions" (career);
  fixes share-path URL/filename + JSON-LD url + analytics provenance.
- **Bugfix:** the hero `introH1` replacement injected `you're` into a
  single-quoted JS dict value, which silently broke the ENTIRE inlined script
  (only the EN static HTML rendered). Reworded apostrophe-free
  ("question on your mind"). Verified: headless Chrome console clean, exit 0.

## Hub + Thai mirrors — DONE (2026-06-26)
- **`/career/` + `/th/career/` hub pages** built via `scripts/build-career-hub.py`
  (regeneratable; reads `assets/career-questions.js`). Portal brand system +
  vertical-nav (Career active) + footer-cols + in-page EN/TH toggle; all 18
  questions grouped by 5 pillars, each deep-linking `/career/reading/?q=<slug>`;
  CollectionPage + ItemList JSON-LD. EN-default + TH-default files.
- **`/th/career/reading/`** Thai reading app now emitted by
  `build-career-reading-app.py` (th-default mirror: surgical head/brand/lang
  swaps, hreflang pair stays reciprocal). The app's `hreflang="th"` + in-app
  "About career readings" link now resolve (no more 404s).
- **Career destination repointed** `/career-tarot-reading/` → `/career/`
  site-wide: `assets/chrome.js` (nav injector, EN+TH), portal `index.html` +
  `th/index.html` (nav + signpost card + footer + JSON-LD ItemList).
- Sitemap → **430 URLs** (all 4 career pages present).
- All four pages render + console-clean at mobile (headless Chrome), EN & TH.

## Still open (decisions / lower-value, NOT blocking)
- **Thin `/career-tarot-reading/` + `/th/career-tarot-reading/`** are now
  unlinked from nav/portal. Spec (§2.3) calls for a **redirect → `/career/`**,
  but that's SEO-sensitive/irreversible — left for an explicit decision
  (redirect vs. keep as a supporting article linking up to `/career/`).
- **Footer-cols rollout** to the other ~400 `page.css` pages — deferred
  (existing footers work; vertical-nav already injected site-wide).
- **Per-slug `/career/<slug>/` SEO scenario pages** — future; scale on winners
  after the reading app indexes (mirrors `/love-readings/<slug>/`).
- Merge branch `homepage-three-vertical-reframe` → `main` when ready to ship.
- The 8 unreachable `CONTINUE_RECS` entries for non-`connection` modes still
  hold love URLs — dead code (career is always `connection`), harmless.

## Pipeline artifacts
- generator: `scripts/build-career-question.workflow.js` (career VOICE)
- postprocess (single): `scripts/postprocess-career-question.py <out_file> <slug> <key>`
- batch collector: `scripts/collect-career-datasets.py`
- app builder: `scripts/build-career-reading-app.py` (idempotent; hard-fails if a
  love-source string drifts so the de-love fixes can't silently no-op)
- question set: `assets/career-questions.js` (18 Qs)
- datasets: `assets/data/career-readings/<slug>-reading.json`
- sitemap: `scripts/generate-sitemap.py` (427 URLs; `/career/reading/` included)

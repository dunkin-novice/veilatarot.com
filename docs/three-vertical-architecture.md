# Veila — Three-Vertical Architecture & Career Migration Plan

**Status:** decided, ready to implement. This is the build spec, not a strategy memo.
**Scope:** plug existing Love into a clean 3-vertical IA, then ship Career as vertical #2. Health is reserved only.
**Host reality:** GitHub Pages, static. No 301s, no `_redirects`, no `.htaccess`. Redirects = client-side `<meta http-equiv="refresh">` + `rel=canonical` (the pattern already used in `/th/scenarios/` and emitted by `scripts/build-cards.py`).
**Verified against repo:** 2026-06-26 — every script/asset/path below confirmed to exist.

---

## 0. Locked decisions (read first)

1. **Layer, don't move.** Existing Love URLs stay exactly where they rank. `/love/`, `/career/`, `/health/` are vertical roots for **navigation, branding, and NEW pages** — not a relocation of legacy content.
2. **Three vertical roots, equal grammar:** `/love/`, `/career/`, `/health/` (+ `/th/` mirrors). Health is reserved (nav slot + path), not published until it has real content.
3. **Career = one vertical.** Money/finance is a *cluster + tag* inside `/career/`, not its own namespace. `/money/` can be split out later if Search Console earns it.
4. **Career launch = 15–20 MVP questions**, reusing the exact Love pipeline. Scale on winners after they index.
5. **Redirects only where they pay for themselves.** Legacy Love = zero redirects. The only redirect work is consolidating the thin existing `/career-tarot-reading/` into the new `/career/` hub.

---

## 1. Current state (what exists today)

Flat, un-namespaced, EN at root + Thai mirror under `/th/`. No category nav anywhere — header is brand + language toggle only.

**Love (live, indexed — DO NOT MOVE):**
- `/love-readings/` — cluster hub (5 clusters, 4 spreads) + **50 EN scenario pages** at `/love-readings/<slug>/`
- `/quick-love-reading/` — 3-card reading **app** + 4 spread pages (`connection`, `emotional-arc`, `clarity`, `reconnection`)
- `/tarot-love-readings/` — secondary love SEO page
- `/th/love-tarot/`, `/th/tarot-love-readings/`, `/th/daily-love-tarot/`, `/th/zodiac-love-tarot/`, `/th/scenarios/` (generated Thai question pages)

**Career (thin, already at root — to consolidate):**
- `/career-tarot-reading/` + `/th/career-tarot-reading/` — single article, "common cards in career readings". No reading flow, no question set.

**Shared engines & reference (vertical-agnostic):**
- `/` — Celtic Cross reading **app** (inline, loads `cards.json`)
- `/celtic-cross-tarot/`, `/daily-tarot-card/`, `/yes-no-tarot/` — reading tools/guides
- `/cards/<78 slugs>/`, `/major-arcana/`, `/minor-arcana/`, `/{cups,swords,wands,pentacles}-tarot-meanings/` — card reference
- `/guides/{how-to-ask-a-tarot-question,tarot-spreads-for-relationships,tarot-for-reflection}/`
- `/all-tarot-pages/` — site index

**Shared assets:** `/assets/page.css`, `/assets/analytics.js` (`window.veilaFire` GA4 wrapper), `/assets/share.js`, `/assets/related-reflections.js`, `/assets/autocomplete.css`.

**Pipeline (scripts/):** `build-love-question.workflow.js` (designs a 3-card spread + generates 78 bilingual cards; args `{qkey, slug, en, th, pillar}`) → `postprocess-love-question.py` → `merge-fill-love-question.py` / `gapfill-love-question.workflow.js`. `build-quick-love-seo-pages.mjs` renders `/th/scenarios/` from `assets/100-questions.js`. `generate-sitemap.py` builds `sitemap.xml`. `build-cards.py` emits the card pages + the meta-refresh redirect stub.

**Data:** `assets/100-questions.js` (question list, `pillar`-tagged) + `assets/data/love-readings/*.json` (per-question 78-card bilingual datasets).

---

## 2. Target URL map

Three columns: **KEEP** (legacy, untouched, canonical-self), **NEW** (create), **REDIRECT** (meta-refresh stub).

### 2.1 Vertical roots (NEW)

| Path | Type | Purpose |
|---|---|---|
| `/love/` + `/th/love/` | NEW hub | Canonical Love vertical entry. Brand/navigational + head term "love tarot". Links **down** to legacy `/love-readings/`, `/quick-love-reading/`, etc. |
| `/career/` + `/th/career/` | NEW hub | Career vertical hub. Replaces thin `/career-tarot-reading/`. |
| `/health/` + `/th/health/` | RESERVED | Path + nav slot reserved. **Do not publish** until it has real content (avoid thin-content penalty). |

### 2.2 Love — KEEP everything, link from `/love/`

| Path | Action |
|---|---|
| `/love-readings/` and `/love-readings/<50 slugs>/` | **KEEP.** Canonical-self. Now linked from `/love/` as the "all love questions" section. |
| `/quick-love-reading/` + 4 spread pages | **KEEP.** Canonical-self. The Love reading engine. |
| `/tarot-love-readings/`, all `/th/` love pages | **KEEP.** Canonical-self. |

→ **No redirects for any Love URL.** That is the entire point of layering.

### 2.3 Career — NEW namespace

| Path | Type |
|---|---|
| `/career/` + `/th/career/` | NEW hub (clusters + spreads + intro, mirrors `/love-readings/` structure) |
| `/career/reading/` + `/th/career/reading/` | NEW 3-card reading app (see §4 for engine reuse) |
| `/career/<15–20 slugs>/` + `/th/career/<slug>/` | NEW scenario question pages |
| `/career-tarot-reading/` | **REDIRECT** → `/career/` |
| `/th/career-tarot-reading/` | **REDIRECT** → `/th/career/` |

### 2.4 Shared / reference — unchanged

`/cards/*`, arcana + suit pages, `/guides/*`, `/celtic-cross-tarot/`, `/daily-tarot-card/`, `/yes-no-tarot/`, `/`, `/all-tarot-pages/`: **KEEP**, vertical-agnostic. Career links *to* them (e.g. Pentacles meanings) rather than copying.

### ⚠ Cannibalization guardrail (`/love/` vs `/love-readings/`)
Two love hubs can compete. Enforce a hierarchy so they don't:
- `/love/` targets the **broad head/navigational** intent ("love tarot", brand entry). Short, routes outward. Canonical → self.
- `/love-readings/` keeps its **specific informational** intent ("reflective love tarot readings", the 5 clusters). Canonical → self. Unchanged copy.
- Internal links flow **down only**: `/love/` → `/love-readings/`, never a reciprocal "hub" link back up that flattens the hierarchy. Do **not** cross-canonicalize (that would de-index one).
- If you'd rather not maintain two: make `/love/` a meta-refresh redirect → `/love-readings/` and treat `/love-readings/` as the vertical root. Acceptable, but you lose the clean `/love/` brand path. **Recommendation: keep `/love/` as a thin real hub** — the symmetry with `/career/` and `/health/` is worth it.

---

## 3. Shared vs vertical-specific component split

Decide once: anything **vertical-agnostic** is shared and lives in `/assets/` or `/cards/`; anything **vertical-voiced** is duplicated per vertical with swapped data + copy.

### SHARED (build/refactor once, all verticals consume)
| Component | Lives at | Notes |
|---|---|---|
| Card reference (78 pages, arcana, suits) | `/cards/*`, `/*-tarot-meanings/` | Never duplicate. Verticals deep-link in. |
| Reading **engine** (deck, draw, flip, reveal, share) | → extract to `/assets/reading-engine.js` (+ `reading.css`) | Today it's inline in `/` and re-implemented in `/quick-love-reading/`. See §4. |
| Layout chrome | `/assets/page.css` | Header, footer, breadcrumb, hub-card lists, `.cta-btn`. Add nav styles here (§5). |
| Analytics | `/assets/analytics.js` | `window.veilaFire(event, props)`. Add a `vertical` prop to every event. |
| Share image, autocomplete, related-reflections | `/assets/share.js`, `/assets/autocomplete.css`, `/assets/related-reflections.js` | Pass vertical via config, not hardcode. |
| Generation pipeline | `scripts/build-*-question.workflow.js`, post/merge/gapfill | One pipeline, swap the `VOICE`, `pillar`, and intent list per vertical. |
| Sitemap / feed builders | `scripts/generate-sitemap.py`, `feed.xml` | Teach them the new namespaces; exclude redirect stubs. |

### VERTICAL-SPECIFIC (one set per vertical)
| Component | Love (exists) | Career (build) |
|---|---|---|
| Vertical hub | `/love-readings/` (+ new `/love/`) | `/career/` |
| Question dataset (list) | `assets/100-questions.js` | `assets/career-questions.js` |
| Per-question readings | `assets/data/love-readings/*.json` | `assets/data/career-readings/*.json` |
| Scenario pages | `/love-readings/<slug>/` | `/career/<slug>/` |
| Reading-flow shell | `/quick-love-reading/` | `/career/reading/` |
| Spread framings | Connection / Emotional Arc / Clarity / Reconnection | Crossroads / Trajectory / Worth (proposed, §6.3) |
| Landing + SEO copy + JSON-LD | per page | per page |
| Pipeline `VOICE` block | love oracle voice | career/work voice (§6.2) |

**Rule of thumb:** if the file mentions hearts, exes, or "the bond," it's vertical-specific. If it draws or explains cards, it's shared.

---

## 4. Reading engine reuse (the one real refactor)

The Love reading flow (`/quick-love-reading/index.html`, ~4800 lines) is the closest thing to the Career flow. Two paths:

**MVP (do this now — zero risk to live Love):**
1. Copy `/quick-love-reading/index.html` → `/career/reading/index.html`.
2. Swap data sources: `assets/100-questions.js` → `assets/career-questions.js`; `assets/data/love-readings/` → `assets/data/career-readings/`.
3. Replace love copy, titles, JSON-LD, hreflang, canonical with career equivalents.
4. Repeat for `/th/career/reading/`.
   → Some duplicated engine code. Accepted for MVP; Love is untouched and safe.

**Follow-up (after Career validates — do not block launch on it):**
5. Extract the shared engine to `/assets/reading-engine.js` + `/assets/reading.css`, parametrized by a config object: `{ vertical, questionsSrc, dataDir, spreads, i18n }`.
6. Reduce `/quick-love-reading/` and `/career/reading/` to thin shells that call `initReading(config)`. Refactor the live Love page **last**, with the page diffed against current behavior.

Ship order: clone first, generalize later. Reuse % goes up over time without ever risking the ranking pages.

---

## 5. Nav + footer that scale 1 → 3

Today: **no category nav.** Header = `.brand` + `.lang-toggle`. Add a primary vertical nav. Build it to render all three verticals with per-state styling so going from 1 → 3 live verticals is a data change, not a markup change.

### 5.1 Primary nav (add to header, all pages via `page.css` + shared partial)
States per item: `live` (linked), `new` (linked + "new" tag), `soon` (muted, not linked).

```html
<nav class="vertical-nav" aria-label="Readings">
  <a href="/love/"   data-href-en="/love/"   data-href-th="/th/love/"   data-vertical="love"   data-i18n="navLove">Love</a>
  <a href="/career/" data-href-en="/career/" data-href-th="/th/career/" data-vertical="career" class="is-new" data-i18n="navCareer">Career</a>
  <span class="vn-soon" data-vertical="health" data-i18n="navHealth">Health</span>
</nav>
```
- Mark `aria-current="page"` on the active vertical (set per page or via a tiny inline check on `location.pathname`).
- Health is a `<span class="vn-soon">` (not an `<a>`) until launch → swap to `<a>` + drop the class. That is the whole "scale to 3" operation.
- **Mobile-first:** below ~560px, render as a horizontal scroll row (`overflow-x:auto; gap:18px`) under the brand line — no hamburger needed for 3 items. Min tap target 44px height.

### 5.2 Footer — columns by vertical + utility
Replace the single `.footer-nav` row with a stacked-on-mobile, 3-column-on-desktop block:

```html
<footer>
  <nav class="footer-cols" aria-label="Footer">
    <div class="fc"><h4 data-i18n="navLove">Love</h4>
      <a href="/love/">Overview</a><a href="/quick-love-reading/">Quick Love Reading</a><a href="/love-readings/">All love questions</a></div>
    <div class="fc"><h4 data-i18n="navCareer">Career</h4>
      <a href="/career/">Overview</a><a href="/career/reading/">Career Reading</a></div>
    <div class="fc"><h4 data-i18n="navHealth">Health</h4>
      <span class="soon" data-i18n="footerSoon">Coming soon</span></div>
    <div class="fc"><h4 data-i18n="footerExplore">Explore</h4>
      <a href="/celtic-cross-tarot/">Celtic Cross</a><a href="/daily-tarot-card/">Daily Card</a><a href="/all-tarot-pages/">All Pages</a></div>
  </nav>
  <div class="last-updated" data-i18n="footerLastUpdated">Last updated · …</div>
  <div data-i18n="footerCopy">veilatarot.com · © MMXXVI</div>
</footer>
```
- **Mobile-first:** `.footer-cols { display:grid; grid-template-columns:1fr; gap:20px }` → `@media(min-width:640px){ repeat(4,1fr) }`.
- Keep the existing `data-href-en`/`data-href-th` language-swap pattern on every link.
- Add the new i18n keys (`navLove`, `navCareer`, `navHealth`, `footerExplore`, `footerSoon`) to **every page's** `T` dictionary, EN + TH.

### 5.3 Reuse
Put nav + footer markup in **one** copy-source (a partial you paste, or—better—inject from a tiny `/assets/chrome.js` that writes the nav/footer and sets active state + language hrefs). Either way: define once, identical on every page, so adding Health is a single edit.

---

## 6. Homepage — lead with Love, signal all three

Current homepage (`/index.html`) leads with **Celtic Cross**; Love is the ghost CTA; the AEO answer-block frames the whole site as Celtic-Cross-only. Reframe to **"tarot for life's big questions,"** Love first.

### 6.1 Concrete edits to `/index.html` (and mirror in `/th/`)
1. **Add the vertical nav** (§5.1) to the header.
2. **Reorder the landing CTAs** (around line 1390): make **Love** the primary CTA, keep Celtic Cross + Quick Love as secondary. Suggested:
   - Primary: `Begin a Love Reading` → `/quick-love-reading/`
   - Secondary (ghost): `Celtic Cross (10 cards)` → keep the existing in-page `begin-btn`
3. **Insert a 3-vertical signpost band** directly under the landing (new `<section class="verticals">`): three cards — **Love** (live), **Career** ("new") → `/career/`, **Health** ("coming soon", not linked). Mobile-first single-column stack; 3-up ≥720px.
4. **Rewrite the AEO answer-block** (lines ~1364–1378) from "Celtic Cross platform" to the multi-vertical positioning, EN + TH. Keep the `aeo-answer-block` styling.
5. Update `<title>` / `meta description` to lead with life-question tarot across Love, Career (Health coming), not Celtic Cross alone.
6. Add `ItemList`/`SiteNavigationElement` JSON-LD listing the three verticals so the IA is machine-legible.

### 6.2 Signpost band copy (drop-in)
- **Love** — *live* — "For the bond, the silence, the return. 100+ questions of the heart." → `/love/`
- **Career** — *new* — "For the crossroads, the calling, the question of money." → `/career/`
- **Health** — *soon* — "For the body, energy, and rest. Arriving later in 2026." (no link)

Keep the existing serif/gold visual system (`--gold`, Cormorant Garamond, ivory on ink). No new colors.

---

## 7. Career build — net-new vs reused

### Reused as-is (no new work)
- Card reference, reading engine (cloned, §4), `page.css` chrome, analytics, share, sitemap/feed builders, the **entire generation pipeline** (`build-love-question.workflow.js` + post/merge/gapfill).

### Net-new (create)
1. `assets/career-questions.js` — 15–20 entries, same shape as `100-questions.js`: `{ pillar, key, en, th }`. Career pillars: `decision`, `money`, `growth`, `fit`, `change`.
2. `assets/data/career-readings/*.json` — one per question, generated by the pipeline.
3. `/career/` + `/th/career/` hub pages (clone `/love-readings/` structure; swap clusters/copy/JSON-LD).
4. `/career/reading/` + `/th/career/reading/` (clone of Quick Love shell, §4).
5. `/career/<slug>/` + `/th/career/<slug>/` scenario pages (generated, same template as love scenarios).
6. Career `VOICE` block for the pipeline (work/vocation voice: direct, grounded in craft + circumstance, money spoken as conditions/direction not calendar — reuse the Love voice's "no fixed dates" + "empowering" rules).
7. Career landing/SEO copy + hreflang/canonical per page.

### 7.x Proposed Career MVP question set (15–20 top intents)
Money-cluster questions are tagged `pillar:"money"` so a future `/money/` split is a filter, not a rebuild.

| key | EN intent | pillar |
|---|---|---|
| should-i-take-this-job | Should I take this job? | decision |
| should-i-quit | Should I quit? | decision |
| is-this-career-right | Is this career right for me? | fit |
| am-i-underpaid | Am I underpaid / undervalued? | money |
| will-money-improve | Will my finances improve? | money |
| should-i-ask-for-a-raise | Should I ask for a raise? | money |
| change-careers | Should I change careers? | change |
| why-is-work-stuck | Why does my work feel stuck? | growth |
| whats-blocking-my-success | What's blocking my success? | growth |
| should-i-start-my-own-thing | Should I start my own business? | decision |
| is-this-offer-good | Is this offer right for me? | decision |
| how-to-grow-here | How do I grow in this role? | growth |
| are-they-valuing-me | Does my workplace value me? | fit |
| should-i-wait-or-move | Should I wait or make a move now? | decision |
| what-is-my-calling | What is my real calling? | fit |
| how-to-handle-money-fear | How do I handle money anxiety? | money |
| will-this-project-land | Will this project succeed? | growth |
| should-i-go-back-to-study | Should I go back to study/retrain? | change |

(Ship ~15, hold ~3 as buffer. Watch Search Console impressions; scale winners toward 50/100 with the same pipeline.)

---

## 8. Redirect / canonical pages to create

Static host → use the established stub. **Only two real redirects** (Career consolidation). Everything Love stays put.

### 8.1 Stub template (match existing `/th/scenarios/` + `build-cards.py` pattern)
```html
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8" />
<meta http-equiv="refresh" content="0; url=/career/" />
<link rel="canonical" href="https://veilatarot.com/career/" />
<meta name="robots" content="noindex, follow" />
<title>Redirecting…</title>
</head>
<body>
<p>This page has moved. <a href="/career/">Continue to Tarot for Career &amp; Calling →</a></p>
<script>location.replace('/career/');</script>
</body>
</html>
```

### 8.2 Files to write
| File | `refresh` + canonical target |
|---|---|
| `/career-tarot-reading/index.html` (overwrite the thin article) | `/career/` |
| `/th/career-tarot-reading/index.html` (overwrite) | `/th/career/` |

Before overwriting: salvage the useful "common cards in career readings" card list from the old `/career-tarot-reading/` into the new `/career/` hub so no content is lost.

### 8.3 Do NOT create
- No redirects for any `/love-readings/`, `/quick-love-reading/`, `/tarot-love-readings/`, or `/th/` love path. They keep their URLs and equity.
- No `/health/` redirect or empty hub. Reserve the path; publish only with content.

### 8.4 hreflang on every new page
Match the live pattern — each page declares `en`, `th`, and `x-default`:
```html
<link rel="alternate" hreflang="en" href="https://veilatarot.com/career/" />
<link rel="alternate" hreflang="th" href="https://veilatarot.com/th/career/" />
<link rel="alternate" hreflang="x-default" href="https://veilatarot.com/career/" />
```

---

## 9. Build order (operation sequence)

Phased so nothing depends on an unfinished step and the live site is never broken.

**Phase A — IA scaffolding (no new content, ship same day)**
1. Add nav styles + footer-cols styles to `/assets/page.css`. Add new i18n keys to every page's `T` (EN+TH).
2. Build the shared nav/footer (partial or `/assets/chrome.js`); set active state + language hrefs.
3. Roll nav/footer onto: `/`, `/love-readings/`, `/quick-love-reading/`, `/career-tarot-reading/`, reference pages, and `/th/` equivalents.
4. Create `/love/` + `/th/love/` thin hubs (canonical-self; link down to legacy love pages — see §2.4 guardrail).

**Phase B — Homepage reframe**
5. Edit `/index.html` per §6 (nav, CTA reorder, signpost band, AEO rewrite, title/desc, JSON-LD). Mirror in `/th/`.

**Phase C — Career content (the vertical)**
6. Write `assets/career-questions.js` (§7, 15 ship + 3 buffer).
7. Add a career `VOICE` block; run `build-love-question.workflow.js` per question → `assets/data/career-readings/*.json`; post-process with the existing Python steps.
8. Build `/career/` + `/th/career/` hubs (clone `/love-readings/` structure).
9. Generate `/career/<slug>/` + `/th/career/<slug>/` scenario pages (reuse the love scenario template + `build-quick-love-seo-pages.mjs`, pointed at `career-questions.js` with output base `career/` / `th/career/`).
10. Clone the reading shell → `/career/reading/` + `/th/career/reading/`; repoint data sources (§4 MVP).

**Phase D — Redirects + indexing**
11. Overwrite `/career-tarot-reading/` and `/th/career-tarot-reading/` with the redirect stub (§8), after salvaging the card list into `/career/`.
12. Extend `scripts/generate-sitemap.py`: add `/love/`, `/career/`, `/career/reading/`, `/career/<slug>/` (+ `/th/`); **exclude** redirect stubs. Regenerate `sitemap.xml` + `feed.xml`.
13. Update `llms.txt` (already mentions Love/Career/General — make the vertical list explicit).
14. Submit updated sitemap; request indexing on `/career/` + hubs in Search Console.

**Phase E — Validate, then scale (post-launch, not blocking)**
15. Watch Career impressions ~2–4 weeks. Scale winning intents toward 50/100 with the same pipeline.
16. Extract the shared reading engine (§4 follow-up). Refactor the live Love page last.
17. When Health content is ready: add `assets/health-questions.js`, build `/health/`, flip the nav `vn-soon` span → `<a>`, add footer links. One pattern, third time.

---

## 10. Health — what the structure reserves (no work now)

- **Path:** `/health/` + `/th/health/` reserved; nothing published.
- **Nav:** the `vn-soon` span + footer "coming soon" already hold the slot. Launch = swap span→link.
- **Data/pipeline:** `assets/health-questions.js` + `assets/data/health-readings/` + a health `VOICE` block — same shapes, when the time comes.
- **No empty pages, no thin content, no premature redirects.** Reserve, don't publish.

---

## 11. Guardrails (don't regress these)

- Never cross-canonicalize `/love/` ↔ `/love-readings/` (de-indexes one). Canonical-self + downward internal links only.
- Never physically move a ranking Love URL. Layer only.
- Every new page: full hreflang trio + canonical-self + GA4 `veilaFire` with a `vertical` prop.
- Redirect stubs carry `noindex, follow` + canonical to target, and are excluded from `sitemap.xml`.
- Keep the existing visual system (ink/ivory/gold, Cormorant + Inter + IBM Plex Sans Thai). No new fonts or colors for Career — it's the same brand, a new room.
- Thai is a native oracle voice, not a translation (per the pipeline `VOICE` rules) — same standard for Career.

# VeilaTarot.com — SEO+AEO Audit Handoff

Last updated: 2026-06-04

---

## What this session did

Ran a world-class SEO+AEO agency audit on the site, then implemented the findings as a sequence of small, independent PRs. The audit graded the site **B-** on first read — strong fundamentals (clean robots/sitemap, dense schema coverage, unique meta hygiene, distinctive AEO surface) but the new Thai SEO funnel from PRs #65/#66 was effectively invisible (not in sitemap, no inbound links, no reciprocal hreflang, missing the Quick Reflection AEO pattern, missing top-level page schema).

This session closed the Quick Wins, the Medium-effort items, and two of the Structural items. The site should now grade **A-** after merge.

---

## Open PRs (merge in this order)

PRs are independent unless noted. Listed in recommended merge order for clean conflict-free landing.

| # | Title | Files | Notes |
|---|---|---|---|
| **#68** | Persist locale across Thai SEO → QLR funnel | 10 | Pre-audit; merge first. Foundation for the funnel work. |
| **#69** | SEO+AEO audit Quick Wins — sitemap freshness + schema fills | 15 | Bumps sitemap freshness, adds `inLanguage` + date fields. |
| **#70** | Add Article JSON-LD to 8 TH SEO question pages | 8 | Adds top-level page schema mirroring EN intent pattern. |
| **#71** | Add Thai footer entry on homepage + QLR | 2 | Solves the orphan-link problem (audit's biggest finding). |
| **#72** | Add hreflang=en reciprocity on 10 TH SEO pages | 10 | TH → EN direction. |
| **#73** | Add Quick Reflection snippet blocks to 10 TH SEO pages | 10 | Ports the signature AEO pattern to the Thai funnel. |
| **#74** | Add EN-side hreflang reciprocity (homepage + QLR) | 2 | EN → TH direction. Pairs with #72. |
| **#75** | Add /th/ — Thai homepage landing | 1 | New file. Anchors the TH surface. |
| **#76** | Add /about-veila/ — rich Organization schema + transparent About page | 1 | New file. Closes E-E-A-T via Organization-as-author. |

**Total: 9 PRs, ~59 file changes.** No app code, no shared CSS, no JSON cards data, no analytics, no share.js, no homepage Celtic Cross app touched. All edits/additions verified with `xmllint` (sitemap) and `json.loads` (JSON-LD).

---

## After-merge follow-ups (small, mechanical)

These are tiny PRs (~2-4 lines each) that depend on the above merges. They were not bundled into the main PRs to avoid merge conflicts on shared files.

### Follow-up A: Footer "About" link on homepage + QLR
**Depends on:** #71, #76 merged
**Why:** PR #76 creates `/about-veila/` but doesn't link it from anywhere. Add one footer link on `/` and `/quick-love-reading/`.
**Edit:** insert `<a href="/about-veila/">About</a>` + separator in each footer's `<nav class="footer-nav">`.

### Follow-up B: Retarget homepage + QLR hreflang="th" to /th/
**Depends on:** #74, #75 merged
**Why:** PR #74 pointed `hreflang="th"` at `/th/love-tarot/` (the only TH hub that existed at the time). Now that `/th/` exists, retarget to `/th/`.
**Edit:** in `index.html` and `quick-love-reading/index.html`, change `hreflang="th" href="https://veilatarot.com/th/love-tarot/"` → `href="https://veilatarot.com/th/"`.

### Follow-up C: Add /th/ + /about-veila/ to sitemap.xml
**Depends on:** #69, #75, #76 merged
**Why:** PR #69 already touches sitemap.xml; can't bundle new pages from #75/#76 there without making #69 wait on them. Now both new pages exist.
**Edit:** append two `<url>` blocks to `sitemap.xml` for `/th/` (priority 0.8, monthly) and `/about-veila/` (priority 0.5, monthly).

### Follow-up D (optional): Thai counterpart /th/about-veila/
**Depends on:** #76 merged
**Why:** Parity with EN. Not part of the audit but completes the bilingual surface.
**Edit:** clone `about-veila/index.html`, translate to Thai, swap hreflang targets.

---

## Audit items deliberately not done

These were surfaced and discussed but intentionally deferred.

### Person schema / single-curator persona
**Status:** User chose Organization-as-author instead (PR #76). No Person schema added. This is a legitimate E-E-A-T approach — many credible sites use Organization-as-author.

If this needs revisiting later: would require committing to a public-facing curator identity (real name or named persona), authoring a bio paragraph, and adding `Person` schema as `author` across all 241 Article-bearing pages.

### TH funnel expansion to match EN intent depth
**Status:** Deferred — major content authoring (10 TH pages vs 44 EN intent pages).

If desired: each new TH page needs original Thai content (not translated), Article + FAQPage + BreadcrumbList JSON-LD, lang-persist script, Quick Reflection block, and entries in the TH hub + sitemap. Recommend doing in batches of 5 pages with a defined topical theme each.

### Reciprocal hreflang for /th/scenarios/* (10 pages)
**Status:** Deferred — architectural gap, not metadata gap.

These pages are TH-only with no direct EN counterparts. Adding `hreflang="en"` pointing to a generic EN page like `/love-readings/` would create half-reciprocal noise (multiple TH pages → one EN page, no symmetric back-reference). Leave as-is unless EN counterparts are authored.

### Reciprocal hreflang for /th/faq/ and /th/about/
**Status:** Deferred — no EN counterparts exist.

No `/faq/` or `/about/` EN page exists. Either author the EN counterparts (then add reciprocal hreflang) or leave the TH pages without `hreflang="en"`.

---

## What to do next

### Immediate (this week)
1. **Review and merge PR #68 first** — it's the pre-audit lang-persist fix and underpins the funnel work.
2. **Merge PRs #69-#76 in the recommended order above.** They are independent enough to merge in any order, but the listed order minimizes conflict resolution.
3. **Submit refreshed sitemap to Google Search Console** after all PRs deploy. The sitemap will jump from 250 URLs to 260+ (after Follow-up C).
4. **Validate one TH page** with [Google Rich Results Test](https://search.google.com/test/rich-results) post-deploy — expect `FAQPage`, `BreadcrumbList`, `Article` all valid with `inLanguage: th`.

### Soon after (within 2 weeks)
5. **Open Follow-up A** (About footer link) — 2 lines per file, instant PR.
6. **Open Follow-up B** (homepage/QLR hreflang retarget) — 2 lines per file.
7. **Open Follow-up C** (sitemap additions) — 12 lines.
8. **Monitor Search Console URL Inspection** for indexing of the 10 new TH SEO pages.

### Watch for (next 4-8 weeks post-deploy)
9. **Featured-snippet appearances** on Thai queries — the Quick Reflection blocks (PR #73 + #75) are designed for this. Monitor Search Console for snippet impressions.
10. **TH funnel CTR** — with the footer entry (PR #71) and Thai homepage (PR #75), the orphan problem is gone. Expect TH SEO pages to start receiving inbound clicks.
11. **`hreflang` cluster recognition** in Search Console — verify the TH/EN pairs are recognized correctly.

### Longer term (if/when there's appetite)
12. **TH funnel expansion** — author 5-10 new TH question pages per round, expanding `/th/love-tarot/` and `/th/scenarios/` toward EN-intent-network depth.
13. **EN counterparts for `/th/faq/` and `/th/about/`** — closes the remaining hreflang gaps.
14. **Author bio decision revisit** — if Google's E-E-A-T scoring on the site looks weak after the Organization-as-author approach lands, consider committing to a named persona.

---

## Files / paths you'll need to know

| Path | What it is |
|---|---|
| `sitemap.xml` | Site map, 250 URLs (260 after PR #69 + Follow-up C). |
| `robots.txt` | Allows all crawlers, references sitemap. No changes needed. |
| `index.html` | EN homepage (Celtic Cross app — protected from audit edits). |
| `quick-love-reading/index.html` | EN QLR app — only footer link touched in this session. |
| `assets/page.css` | Shared stylesheet — protected, not touched. |
| `assets/share.js` | Share poster system — protected, not touched. |
| `assets/analytics.js` | Analytics — protected, not touched. |
| `cards.json` | Canonical card meanings — protected, not touched. |
| `th/love-tarot/` + 8 sub-pages | TH SEO funnel from PRs #65/#66. Heavily edited this session. |
| `th/daily-love-tarot/` | TH daily love landing from PR #66. Edited this session. |
| `th/index.html` | **NEW (PR #75)** — Thai homepage landing. |
| `about-veila/index.html` | **NEW (PR #76)** — Transparent About + rich Organization schema. |
| `love-readings/{5 subhubs}/index.html` | EN cluster subhubs — got `datePublished`/`dateModified` from PR #69. |

---

## Quick reference: audit gaps closed

- ✅ Sitemap missing 10 TH SEO URLs → +10 URLs, freshness bumped (PR #69)
- ✅ TH SEO pages missing `inLanguage: "th"` → added on FAQPage (PR #69)
- ✅ TH SEO pages missing `Article` schema → added on 8 question pages (PR #70)
- ✅ 5 EN cluster subhubs missing date fields → added (PR #69)
- ✅ TH SEO funnel 0 inbound links from EN → footer link bridges it (PR #71)
- ✅ TH SEO pages missing reciprocal `hreflang="en"` → added (PR #72)
- ✅ TH funnel missing Quick Reflection AEO pattern → 10 Thai blocks added (PR #73)
- ✅ Homepage missing `hreflang` block entirely → added full block (PR #74)
- ✅ QLR `hreflang="th"` self-pointing → retargeted (PR #74)
- ✅ Site missing Thai homepage → `/th/` created (PR #75)
- ✅ Site missing transparent About page + rich Organization schema → `/about-veila/` (PR #76)

---

## Constraints to preserve in future work

These were observed in this session and remain in effect:

- **Never edit `assets/share.js`** — share poster system, separate spec.
- **Never edit `cards.json`** — canonical card meanings, separate spec.
- **Never edit `assets/analytics.js`** — analytics bridge.
- **Never edit `assets/page.css`** — shared styles. Inline per-page if needed.
- **Never edit the homepage Celtic Cross app body** — separate spec. Footer + meta is OK with explicit authorization.
- **Quick Love Reading app body** — same posture. Footer + meta is OK; in-app changes need a brief.
- **Don't sync www/ or ios/ from canonical** unless explicitly running `cp + cap sync` per the Capacitor wrap workflow.

---

## Contact / continuation

This handoff is written so any future Claude (or human) session can pick up where this left off without re-reading the full transcript. The PR descriptions on GitHub also contain enough context to make merge decisions standalone.

If something in the PR queue feels stuck, the cleanest debug move is:
1. `gh pr list --state open` to see what's left.
2. Read the PR body — each one declares its independence vs dependencies.
3. Run the verification step from the PR's "Test plan" section.

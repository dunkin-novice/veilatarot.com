# Daily Reading Pipeline

How the daily 3-card collective reading gets from the scheduled cloud task to
production (`/daily-tarot-card/`).

## What the cloud task does today

A scheduled cloud task runs every morning and pushes a branch containing
exactly one new file:

- Branch: `daily-reading/<date>` (older runs: `daily-reading-<date>` with hyphens)
- File: `data/daily-readings/<date>.json`

JSON schema (all EN-only as of 2026-07):

| Field | Type | Notes |
|---|---|---|
| `date` | `YYYY-MM-DD` | Reading date |
| `title` | string | e.g. "Veila Daily Tarot: Three of Swords, The Lovers, Two of Pentacles" |
| `meta_description` | string | |
| `cards_drawn` | array of 3 | `{ name, orientation (Upright/Reversed), position (Anchor/Current/Trajectory) }` |
| `interpretation_markdown` | markdown | `## The Anchor`, `## Current Energy`, `## The Trajectory`, `## Synthesis` sections |
| `tags` | string[] | `daily-reading`, `love-tarot`, `veilatarot` |

Historically these branches were **never merged**, so the data never reached
production. Readings 2026-06-28 → 2026-07-02 were landed manually into
`data/daily-readings/` on 2026-07-02.

## What consumes the data now

1. **`scripts/build-daily-reading.mjs`** (Node, no deps) — finds the newest
   `data/daily-readings/<date>.json` and regenerates the server-rendered
   section in `daily-tarot-card/index.html` between the
   `<!-- DAILY-READING:START -->` / `<!-- DAILY-READING:END -->` markers:
   today's 3 cards + their interpretations, a 40–60-word summary built from
   the reading's own sentences, and a publish-cadence note. It also sets the
   Article JSON-LD `dateModified` to the reading date and ensures the
   `author` `@id` (`https://veilatarot.com/#person`). Idempotent — same input
   produces byte-identical output. The interactive client-side one-card draw
   on the page is untouched.

   The TH surface `th/daily-love-tarot/index.html` is *not* injected: the
   JSON carries English text only. If the cloud task starts emitting Thai
   fields, extend the script (do not hand-edit that page's section).

2. **`.github/workflows/daily-reading-publish.yml`** — triggers on pushes to
   `daily-reading/**` and `daily-reading-*` (plus `workflow_dispatch`). It
   checks out `main`, copies any new daily-readings JSONs from the pushed
   branch (validating they parse), runs the build script, regenerates
   `sitemap.xml` (`python3 scripts/generate-sitemap.py`) and `feed.xml`
   (`node scripts/generate-feed.mjs`), then commits and pushes to `main`.

   **Branch-protection fallback:** if the direct push to `main` is rejected,
   the workflow pushes `daily-reading-publish/<date>-<run id>` and opens a PR
   with `gh pr create`. If protection also blocks automated merging, that PR
   still needs a human or agent to merge before the reading goes live.

## What the cloud task SHOULD do going forward

Either of these works — pick one and keep it consistent:

- **Keep pushing `daily-reading/<date>` branches** (no change needed). The
  Action now picks them up automatically. Prefer the slash naming; the
  hyphen naming is only supported for backwards compatibility.
- **Push the JSON straight to `main`** (if permitted): add the file, run
  `node scripts/build-daily-reading.mjs`, `python3 scripts/generate-sitemap.py`
  and `node scripts/generate-feed.mjs`, commit everything in one push. This
  skips the Action round-trip entirely.

Old daily-reading branches can be deleted once their JSON is on `main`.

## Manual recovery

If a day's reading never made it to production:

```bash
# 1. See which branches exist
git fetch origin && git branch -r | grep daily-reading

# 2. Land the JSON(s) into the working tree
git show origin/daily-reading/<date>:data/daily-readings/<date>.json \
  > data/daily-readings/<date>.json
python3 -c "import json;json.load(open('data/daily-readings/<date>.json'))"  # validate

# 3. Rebuild the page + sitemap + feed
node scripts/build-daily-reading.mjs
python3 scripts/generate-sitemap.py
node scripts/generate-feed.mjs

# 4. Ship via the usual squash-PR to main (GitHub Pages deploys from main)
```

You can also run the workflow by hand (Actions → "Daily reading publish" →
Run workflow) — the `workflow_dispatch` path rebuilds from whatever JSONs are
already on `main`.

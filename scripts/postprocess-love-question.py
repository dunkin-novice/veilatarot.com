#!/usr/bin/env python3
"""Post-process one build-love-question workflow output:
  - extract result, strip _meta, write assets/data/love-readings/<slug>-reading.json
  - validate completeness (78 cards x up/rev x positions x en/th)
  - register key->path in quick-love-reading/index.html QUESTION_DATASETS
  - tick the Qn line in the Obsidian tracker and recompute pillar/total counts

Usage: postprocess-love-question.py <output_file> <slug> <key> <qnum>
"""
import json, os, re, sys

REPO = "/Users/kitikornrakhangthong/projects/veilatarot.com"
TRACKER = "/Users/kitikornrakhangthong/Brain/VeilaTarot/100 Questions Tracker.md"
APP = os.path.join(REPO, "quick-love-reading/index.html")

def main():
    out_file, slug, key, qnum = sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4]

    CANON = [
        "01-the-fool","02-the-magician","03-the-high-priestess","04-the-empress","05-the-emperor","06-the-hierophant","07-the-lovers","08-the-chariot","09-strength","10-the-hermit","11-wheel-of-fortune","12-justice","13-the-hanged-man","14-death","15-temperance","16-the-devil","17-the-tower","18-the-star","19-the-moon","20-the-sun","21-judgement","22-the-world","23-ace-of-wands","24-two-of-wands","25-three-of-wands","26-four-of-wands","27-five-of-wands","28-six-of-wands","29-seven-of-wands","30-eight-of-wands","31-nine-of-wands","32-ten-of-wands","33-page-of-wands","34-knight-of-wands","35-queen-of-wands","36-king-of-wands","37-ace-of-cups","38-two-of-cups","39-three-of-cups","40-four-of-cups","41-five-of-cups","42-six-of-cups","43-seven-of-cups","44-eight-of-cups","45-nine-of-cups","46-ten-of-cups","47-page-of-cups","48-knight-of-cups","49-queen-of-cups","50-king-of-cups","51-ace-of-swords","52-two-of-swords","53-three-of-swords","54-four-of-swords","55-five-of-swords","56-six-of-swords","57-seven-of-swords","58-eight-of-swords","59-nine-of-swords","60-ten-of-swords","61-page-of-swords","62-knight-of-swords","63-queen-of-swords","64-king-of-swords","65-ace-of-pentacles","66-two-of-pentacles","67-three-of-pentacles","68-four-of-pentacles","69-five-of-pentacles","70-six-of-pentacles","71-seven-of-pentacles","72-eight-of-pentacles","73-nine-of-pentacles","74-ten-of-pentacles","75-page-of-pentacles","76-knight-of-pentacles","77-queen-of-pentacles","78-king-of-pentacles"
    ]
    w = json.load(open(out_file))
    d = w["result"] if isinstance(w.get("result"), dict) else json.loads(w["result"])
    d.pop("_meta", None)

    # prune any non-canonical (mislabeled/duplicate) keys, keep exactly the 78
    extras = [k for k in d["cards"] if k not in CANON]
    if extras:
        print(f"  pruning {len(extras)} non-canonical keys: {extras}")
        d["cards"] = {k: v for k, v in d["cards"].items() if k in CANON}

    # validate
    pks = [p["key"] for p in d["spread"]["positions"]]
    assert len(d["cards"]) == 78, f"expected 78 cards, got {len(d['cards'])}"
    bad = []
    for k, v in d["cards"].items():
        for o in ("upright", "reversed"):
            for pk in pks:
                cell = v.get(o, {}).get(pk, {})
                if not (cell.get("en") and cell.get("th")):
                    bad.append(f"{k}:{o}:{pk}")
    assert not bad, f"{len(bad)} bad slots: {bad[:10]}"

    rel = f"assets/data/love-readings/{slug}-reading.json"
    path = os.path.join(REPO, rel)
    json.dump(d, open(path, "w"), ensure_ascii=False, indent=2)
    size = os.path.getsize(path)

    # wire into QUESTION_DATASETS (idempotent)
    html = open(APP).read()
    entry = f"  '{key}': '/assets/data/love-readings/{slug}-reading.json'"
    if f"'{key}':" not in html:
        # insert before the closing }; of the QUESTION_DATASETS object
        m = re.search(r"(const QUESTION_DATASETS = \{.*?)(\n\};)", html, re.S)
        if not m:
            raise SystemExit("could not locate QUESTION_DATASETS block")
        block = m.group(1).rstrip()
        if not block.endswith(","):
            block += ","
        html = html[:m.start()] + block + "\n" + entry + "\n};" + html[m.end():]
        open(APP, "w").write(html)
        wired = "wired"
    else:
        wired = "already-wired"

    # tracker: tick the Qn line, append slug/key note, recompute counts
    t = open(TRACKER).read()
    lines = t.split("\n")
    pillar = None
    for i, ln in enumerate(lines):
        pm = re.match(r"### Pillar: (\w+)", ln)
        if pm:
            pillar = pm.group(1)
        m = re.match(rf"- \[[ x~]\] Q{qnum}: (.+)", ln)
        if m and re.match(rf"- \[[ x~]\] Q{qnum}:", ln):
            body = m.group(1)
            # strip any existing trailing note
            body = re.split(r"\s+→\s+`", body)[0].rstrip()
            lines[i] = f"- [x] Q{qnum}: {body} → `{slug}-reading.json` (key: `{key}`)"
            break
    t = "\n".join(lines)

    # recompute per-pillar counts
    def recount(text):
        out = []
        cur_done = cur_total = 0
        cur_hdr_idx = None
        res = text.split("\n")
        # first pass: compute counts per pillar section
        sections = []
        idx = None
        for i, ln in enumerate(res):
            if ln.startswith("### Pillar:"):
                sections.append([i, 0, 0])
            elif sections and re.match(r"- \[[ x~]\] Q", ln):
                sections[-1][2] += 1
                if re.match(r"- \[x\] Q", ln):
                    sections[-1][1] += 1
        for i, done, total in sections:
            if total > 0:  # leave unpopulated pillar headers (placeholder denominators) untouched
                res[i] = re.sub(r"\(\d+/\d+\)", f"({done}/{total})", res[i])
        # total
        total_done = sum(1 for ln in res if re.match(r"- \[x\] Q", ln))
        for i, ln in enumerate(res):
            if ln.startswith("**Total Progress:**"):
                res[i] = re.sub(r"\d+ / 100", f"{total_done} / 100", ln)
        return "\n".join(res)

    t = recount(t)
    open(TRACKER, "w").write(t)

    print(f"OK {slug}: {size} bytes, {wired}, tracker Q{qnum} ticked")

if __name__ == "__main__":
    main()

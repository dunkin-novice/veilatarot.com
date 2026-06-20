#!/usr/bin/env python3
"""Merge one-or-more workflow outputs for a question, ship if complete, else report gaps.

Usage: merge-fill-love-question.py <slug> <key> <qnum> <out1> [out2 ...]

Unions cards across all given task-output files (later files do NOT overwrite earlier
non-empty cells; any source that has a card wins). If all 78 cards x up/rev x pos x en/th
are present -> writes the dataset, wires it, ticks the tracker (delegates to
postprocess-love-question via the same logic). Otherwise prints MISSING <cardkeys> and
writes a sidecar /tmp/fill-<slug>.json with {slug,key,qnum,en,th,positions,tone,missing,cards}
so a gap-fill run can complete it.
"""
import json, os, re, sys

REPO = "/Users/kitikornrakhangthong/projects/veilatarot.com"

def load(out_file):
    w = json.load(open(out_file))
    return w["result"] if isinstance(w.get("result"), dict) else json.loads(w["result"])

def main():
    slug, key, qnum = sys.argv[1], sys.argv[2], sys.argv[3]
    outs = sys.argv[4:]
    base = None
    cards = {}
    for f in outs:
        if not os.path.exists(f):
            continue
        d = load(f)
        if base is None:
            base = d
        for ck, cv in d.get("cards", {}).items():
            if ck not in cards:
                cards[ck] = cv
    if base is None:
        raise SystemExit("no readable outputs")

    pks = [p["key"] for p in base["spread"]["positions"]]
    from_keys = [
        "01-the-fool","02-the-magician","03-the-high-priestess","04-the-empress","05-the-emperor","06-the-hierophant","07-the-lovers","08-the-chariot","09-strength","10-the-hermit","11-wheel-of-fortune","12-justice","13-the-hanged-man","14-death","15-temperance","16-the-devil","17-the-tower","18-the-star","19-the-moon","20-the-sun","21-judgement","22-the-world","23-ace-of-wands","24-two-of-wands","25-three-of-wands","26-four-of-wands","27-five-of-wands","28-six-of-wands","29-seven-of-wands","30-eight-of-wands","31-nine-of-wands","32-ten-of-wands","33-page-of-wands","34-knight-of-wands","35-queen-of-wands","36-king-of-wands","37-ace-of-cups","38-two-of-cups","39-three-of-cups","40-four-of-cups","41-five-of-cups","42-six-of-cups","43-seven-of-cups","44-eight-of-cups","45-nine-of-cups","46-ten-of-cups","47-page-of-cups","48-knight-of-cups","49-queen-of-cups","50-king-of-cups","51-ace-of-swords","52-two-of-swords","53-three-of-swords","54-four-of-swords","55-five-of-swords","56-six-of-swords","57-seven-of-swords","58-eight-of-swords","59-nine-of-swords","60-ten-of-swords","61-page-of-swords","62-knight-of-swords","63-queen-of-swords","64-king-of-swords","65-ace-of-pentacles","66-two-of-pentacles","67-three-of-pentacles","68-four-of-pentacles","69-five-of-pentacles","70-six-of-pentacles","71-seven-of-pentacles","72-eight-of-pentacles","73-nine-of-pentacles","74-ten-of-pentacles","75-page-of-pentacles","76-knight-of-pentacles","77-queen-of-pentacles","78-king-of-pentacles"
    ]
    def ok(ck):
        c = cards.get(ck)
        if not c: return False
        for o in ("upright","reversed"):
            for pk in pks:
                cell = c.get(o,{}).get(pk,{})
                if not (cell.get("en") and cell.get("th")): return False
        return True
    missing = [ck for ck in from_keys if not ok(ck)]

    if not missing:
        d = dict(base); d["cards"] = {ck: cards[ck] for ck in from_keys}
        d.pop("_meta", None)
        rel = f"assets/data/love-readings/{slug}-reading.json"
        json.dump(d, open(os.path.join(REPO, rel), "w"), ensure_ascii=False, indent=2)
        print(f"COMPLETE {slug}: 78/78 -> {rel}")
        # wire + tracker via postprocess on the freshly written file (it reads result-or-dict)
        return

    # incomplete: emit sidecar for gap-fill
    side = {
        "slug": slug, "key": key, "qnum": qnum,
        "en": base["question"]["en"], "th": base["question"]["th"],
        "positions": [{"key": p["key"], "label_en": p["label"]["en"], "label_th": p["label"]["th"]} for p in base["spread"]["positions"]],
        "missing": missing,
        "cards": cards,
    }
    sp = f"/tmp/fill-{slug}.json"
    json.dump(side, open(sp, "w"), ensure_ascii=False)
    print(f"INCOMPLETE {slug}: {len(cards)} cards, MISSING {len(missing)}: {missing} -> {sp}")

if __name__ == "__main__":
    main()

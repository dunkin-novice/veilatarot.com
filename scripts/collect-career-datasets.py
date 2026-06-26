#!/usr/bin/env python3
"""Scan the tasks dir for completed career workflow outputs and process any
dataset not yet on disk. Re-runnable. Reports complete / incomplete(needs-resume).

Usage: collect-career-datasets.py
"""
import json, os, glob, subprocess

REPO = "/Users/kitikornrakhangthong/projects/veilatarot.com"
TASKS = "/private/tmp/claude-501/-Users-kitikornrakhangthong/1c090e57-1c4a-469c-a42b-07ba82d8d196/tasks"
OUTDIR = os.path.join(REPO, "assets/data/career-readings")
POST = os.path.join(REPO, "scripts/postprocess-career-question.py")

KEYS = {
    "should-i-take-this-job","should-i-quit","is-this-career-right","am-i-underpaid",
    "will-money-improve","should-i-ask-for-a-raise","change-careers","why-is-work-stuck",
    "whats-blocking-my-success","should-i-start-my-own-thing","is-this-offer-good",
    "how-to-grow-here","are-they-valuing-me","should-i-wait-or-move","what-is-my-calling",
    "how-to-handle-money-fear","will-this-project-land","should-i-go-back-to-study",
}

def main():
    done, incomplete, pending = [], [], set(KEYS)
    for f in glob.glob(os.path.join(TASKS, "*.output")):
        try:
            w = json.load(open(f))
        except Exception:
            continue
        r = w.get("result")
        if not isinstance(r, dict) or "cards" not in r:
            continue
        key = r.get("question", {}).get("key")
        if key not in KEYS:
            continue
        pending.discard(key)
        dest = os.path.join(OUTDIR, f"{key}-reading.json")
        if os.path.exists(dest):
            done.append(key); continue
        # try to process
        res = subprocess.run(["python3", POST, f, key, key], capture_output=True, text=True)
        if res.returncode == 0:
            done.append(key)
        else:
            ncards = len(r.get("cards", {}))
            incomplete.append((key, ncards, res.stderr.strip().splitlines()[-1] if res.stderr else ""))

    print(f"=== career datasets: {len([k for k in KEYS if os.path.exists(os.path.join(OUTDIR, k+'-reading.json'))])}/18 on disk ===")
    if incomplete:
        print("INCOMPLETE (needs resume):")
        for k, n, err in incomplete:
            print(f"  - {k}: {n}/78 cards | {err}")
    still = sorted(pending)
    if still:
        print(f"NOT YET COMPLETED ({len(still)}): {', '.join(still)}")

if __name__ == "__main__":
    main()

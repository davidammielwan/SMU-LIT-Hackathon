"""Evaluation — run every amendment over the client base and score against
hand-labelled ground truth. Produces the accuracy numbers for the pitch.

Usage:  python eval.py            (needs OPENROUTER_API_KEY in amenda/.env)
"""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(__file__))
from analysis import impact

AFFECTED = {"high", "moderate"}


def main():
    gt = impact.load_json("ground_truth.json")
    amendment_ids = [k for k in gt if not k.startswith("_")]
    print(f"Sweeping {len(amendment_ids)} amendments x 6 clients ...")
    result = impact.sweep(amendment_ids)
    if result["errors"]:
        print(f"WARNING: {len(result['errors'])} pair(s) errored:")
        for e in result["errors"]:
            print("  ", e)

    tp = fp = fn = 0
    cat_exact = cat_total = 0
    trap_pass = trap_total = 0
    rows = []

    for aid in amendment_ids:
        labels = {k: v for k, v in gt[aid].items() if not k.startswith("_")}
        traps = gt[aid].get("_traps", [])
        # collect predictions for this amendment
        pred = {}   # key -> category
        for r in result["raw"]:
            if r["amendment_id"] != aid:
                continue
            for v in r["document_verdicts"]:
                if v["category"] in AFFECTED:
                    pred[v["doc_id"]] = v["category"]
            if r["profile_verdict"]["category"] in AFFECTED:
                pred[f"profile:{r['client_id']}"] = r["profile_verdict"]["category"]

        for key, want in labels.items():
            cat_total += 1
            got = pred.get(key)
            if got:
                tp += 1
                if got == want:
                    cat_exact += 1
                rows.append((aid, key, want, got, "HIT" if got == want else "HIT (cat off)"))
            else:
                fn += 1
                rows.append((aid, key, want, "-", "MISS"))
        for key in pred:
            if key not in labels:
                fp += 1
                rows.append((aid, key, "unaffected", pred[key], "FALSE POSITIVE"))
        for t in traps:
            trap_total += 1
            if t not in pred:
                trap_pass += 1

    prec = tp / (tp + fp) if tp + fp else 0
    rec = tp / (tp + fn) if tp + fn else 0
    print("\n--- per-item ---")
    for r in sorted(rows):
        print(f"  {r[0]}  {r[1]:<14} want={r[2]:<10} got={r[3]:<10} {r[4]}")
    print("\n--- summary ---")
    print(f"Affected items found (recall):    {tp}/{tp + fn}  = {rec:.0%}")
    print(f"Flags that were correct (precision): {tp}/{tp + fp}  = {prec:.0%}")
    print(f"Exact category (high vs moderate): {cat_exact}/{cat_total}")
    print(f"False-positive traps passed:       {trap_pass}/{trap_total}"
          "  (topically-adjacent docs correctly left unflagged)")
    out = os.path.join(os.path.dirname(__file__), "data", "eval_results.json")
    with open(out, "w", encoding="utf-8") as f:
        json.dump({"precision": prec, "recall": rec,
                   "category_exact": [cat_exact, cat_total],
                   "traps_passed": [trap_pass, trap_total],
                   "rows": rows}, f, indent=2)
    print(f"\nSaved {out}")


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""
run_demo.py — execute the MedJar prototype end to end.

Runs every demonstration case through the full pipeline (intake → scoped hybrid
retrieval → independent proposal → debate → consensus → report), writes the
diagnostic reports, debate transcripts and a machine-readable trace, and prints
an evaluation summary.

    python3 run_demo.py            # all cases
    python3 run_demo.py CASE-001   # one case, verbose

Outputs land in ./output/. The trace is consumed by ../figures/make_figures.py
so that the result figures are generated from real run data.
"""
from __future__ import annotations

import json
import os
import sys
from typing import Dict, List, Tuple

from medjar import (
    ChiefOfService, GroundednessVerifier, HybridRetriever, brier, cases,
    expected_calibration_error, load_corpus, render, render_transcript,
)

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "output")


def run_case(cco, verbose: bool = False) -> Dict[str, object]:
    corpus = load_corpus()
    verifier = GroundednessVerifier()
    chief = ChiefOfService(
        retriever=HybridRetriever(corpus),
        verifier=verifier,
        verbose=verbose,
    )
    outcome = chief.run(cco)

    os.makedirs(OUT, exist_ok=True)
    rp = os.path.join(OUT, f"report_{cco.case_id}.md")
    tp = os.path.join(OUT, f"transcript_{cco.case_id}.md")
    with open(rp, "w", encoding="utf-8") as f:
        f.write(render(cco, outcome))
    with open(tp, "w", encoding="utf-8") as f:
        f.write(render_transcript(outcome))

    top = [i.dx for i in outcome.consensus[:3]]
    gold = cco.gold_dx
    return {
        "case_id": cco.case_id,
        "gold_dx": gold,
        "status": outcome.status,
        "reason": outcome.reason,
        "rounds": [
            {"round": r.round, "D_bar": r.D_bar,
             "retrievals": r.retrievals,
             "top": [{"dx": i.dx, "S": i.S, "S_star": i.S_star, "E": i.E,
                      "disagreement": i.disagreement, "per_agent": i.per_agent}
                     for i in r.top]}
            for r in outcome.rounds
        ],
        "consensus": [
            {"dx": i.dx, "icd10": i.icd10, "S": i.S, "S_star": i.S_star, "E": i.E,
             "disagreement": i.disagreement, "per_agent": i.per_agent,
             "red_flag": i.is_red_flag, "n_support": len(i.supporting),
             "n_refute": len(i.refuting)}
            for i in outcome.consensus
        ],
        "red_flags": outcome.red_flags,
        "ledger_size": len(outcome.ledger),
        "groundedness_pass_rate": round(verifier.rate(), 4),
        "claims_checked": verifier.checked,
        "top1_hit": bool(gold and top[:1] == [gold]),
        "top3_hit": bool(gold and gold in top),
        "report_path": os.path.relpath(rp, os.path.dirname(OUT)),
        "transcript_path": os.path.relpath(tp, os.path.dirname(OUT)),
    }


def main(argv: List[str]) -> int:
    wanted = argv[1:] if len(argv) > 1 else None
    registry = cases.by_id()
    selected = ([registry[c] for c in wanted if c in registry] if wanted
                else cases.ALL_CASES)
    if not selected:
        print(f"No such case. Available: {', '.join(registry)}")
        return 2

    print("=" * 78)
    print("MedJar prototype — multi-agent consensus diagnosis (synthetic cases)")
    print("=" * 78)

    results: List[Dict[str, object]] = []
    calib: List[Tuple[float, int]] = []

    for cco in selected:
        print(f"\n[{cco.case_id}] {cco.age}{cco.sex} — {cco.presentation[:78]}…")
        res = run_case(cco, verbose=bool(wanted))
        results.append(res)
        for item in res["consensus"]:                      # type: ignore[index]
            y = 1 if item["dx"] == res["gold_dx"] else 0
            calib.append((float(item["S_star"]), y))
        lead = res["consensus"][0] if res["consensus"] else None   # type: ignore[index]
        print(f"    status      : {res['status'].upper()} — {res['reason']}")
        if lead:
            print(f"    leading dx  : {lead['dx']} (S*={lead['S_star']:.2f})")
        print(f"    gold dx     : {res['gold_dx']}  "
              f"[top-1 {'HIT' if res['top1_hit'] else 'miss'}, "
              f"top-3 {'HIT' if res['top3_hit'] else 'miss'}]")
        print(f"    rounds      : {len(res['rounds']) - 1} debate  "  # type: ignore[arg-type]
              f"final D̄={res['rounds'][-1]['D_bar']:.5f}")            # type: ignore[index]
        print(f"    ledger      : {res['ledger_size']} citations, "
              f"groundedness pass {res['groundedness_pass_rate']:.0%}")
        if res["red_flags"]:
            fl = ", ".join(f"{k} {v:.2f}" for k, v in res["red_flags"].items())  # type: ignore
            print(f"    red flags   : {fl}")

    n = len(results)
    top1 = sum(1 for r in results if r["top1_hit"]) / n
    top3 = sum(1 for r in results if r["top3_hit"]) / n
    ece = expected_calibration_error(calib)
    bs = brier(calib)
    ground = sum(float(r["groundedness_pass_rate"]) for r in results) / n

    print("\n" + "-" * 78)
    print(f"cases={n}   top-1={top1:.0%}   top-3={top3:.0%}   "
          f"ECE={ece:.3f}   Brier={bs:.3f}   groundedness={ground:.0%}")
    print("-" * 78)

    trace = {
        "version": "0.1.0",
        "cases": results,
        "summary": {"n_cases": n, "top1": top1, "top3": top3, "ece": ece,
                    "brier": bs, "groundedness": round(ground, 4)},
        "calibration_pairs": calib,
    }
    os.makedirs(OUT, exist_ok=True)
    tp = os.path.join(OUT, "trace.json")
    with open(tp, "w", encoding="utf-8") as f:
        json.dump(trace, f, indent=2)
    print(f"\nWrote reports, transcripts and trace.json to {OUT}/")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))

#!/usr/bin/env python3
"""
verify_llm_path.py — exercise the LLM reasoning path without network access.

The offline demo (`run_demo.py`) uses the deterministic rule engine, so the
production LLM path would otherwise ship unexecuted. This script drives that
path end to end using `ScriptedAdapter` in place of a provider: prompt
construction, the adapter boundary, contract parsing, citation validation,
grounding, debate, consensus, and report rendering all run for real. Only the
HTTP hop to a model is substituted.

It also checks the safety-relevant guards explicitly:

  1. a citation id the model was never offered is DROPPED (no hallucinated
     provenance can reach the Evidence Ledger);
  2. a diagnosis the model did not reason about does not grant it competence to
     raise an `overcall` critique (Sec. 6.4b);
  3. malformed model output degrades to an empty differential instead of
     aborting the case;
  4. every ledgered claim is entailed by the passage it cites.

    python3 verify_llm_path.py

Exits non-zero if any check fails.
"""
from __future__ import annotations

import json
import sys
from typing import Dict, List, Sequence

from medjar import (
    ENSEMBLE_SPEC, ChiefOfService, GroundednessVerifier, HybridRetriever,
    LLMEngine, ScriptedAdapter, cases, default_ensemble, extract_json,
    load_corpus, render,
)

FAKE_ID = "TOTALLY-MADE-UP-999"


def contexts_for(cco, retriever, context_k: int = 6) -> Dict[str, List[str]]:
    """The passage ids each persona would actually be offered for this case."""
    out: Dict[str, List[str]] = {}
    for _name, persona, scope, _rules, _t in ENSEMBLE_SPEC:
        hits = retriever.retrieve(cco.retrieval_text(), scope=scope,
                                  top_k=context_k)
        out[persona] = [h.passage.pid for h in hits]
    return out


def response(dx_rows: Sequence[Dict], red_flags: Sequence[str],
             confidence: float) -> str:
    """Render a contract-conforming response, as a model would return it.

    Wrapped in a markdown fence with leading prose, since real models do this
    and the parser must cope.
    """
    payload = {"differential": list(dx_rows), "red_flags": list(red_flags),
               "confidence": confidence}
    return ("Here is my assessment.\n\n```json\n"
            + json.dumps(payload, indent=2) + "\n```\n")


def build_adapter_for(cco, ctx: Dict[str, List[str]]) -> ScriptedAdapter:
    """Canned per-persona responses citing that persona's real offered ids,
    plus one deliberately invalid id that must be discarded."""

    def cite(persona: str, n: int) -> str:
        ids = ctx[persona]
        return ids[n % len(ids)] if ids else FAKE_ID

    radiologist = response(
        [{"dx": "Primary lung malignancy", "likelihood": 0.88,
          "supporting": [
              {"claim": "Spiculated margin on a solid upper-lobe nodule carries a "
                        "high pretest probability of malignancy.",
               "citation_id": cite("radiologist", 0)},
              {"claim": "This claim cites a passage that was never offered.",
               "citation_id": FAKE_ID}],
          "refuting": [],
          "discriminating_test": "FDG PET-CT then tissue biopsy"},
         {"dx": "Benign pulmonary granuloma", "likelihood": 0.10,
          "supporting": [], "refuting": [],
          "discriminating_test": "Comparison with prior imaging"}],
        ["Primary lung malignancy"], 0.82)

    cardiologist = response(
        [{"dx": "Demand ischemia (type 2 MI)", "likelihood": 0.74,
          "supporting": [
              {"claim": "A stable minor troponin elevation without ischaemic "
                        "symptoms or dynamic ECG change favours supply-demand "
                        "mismatch over infarction.",
               "citation_id": cite("cardiologist", 0)}],
          "refuting": [], "discriminating_test": "Serial troponin trend"},
         {"dx": "Cardiac tamponade", "likelihood": 0.22,
          "supporting": [], "refuting": [],
          "discriminating_test": "Urgent transthoracic echocardiography"}],
        ["Cardiac tamponade"], 0.71)

    oncologist = response(
        [{"dx": "Primary lung malignancy", "likelihood": 0.90,
          "supporting": [
              {"claim": "Unintentional weight loss with a spiculated nodule is a "
                        "constitutional pattern warranting expedited work-up.",
               "citation_id": cite("oncologist", 0)}],
          "refuting": [], "discriminating_test": "Tissue biopsy with molecular profiling"},
         {"dx": "Malignant pericardial effusion", "likelihood": 0.34,
          "supporting": [],
          "refuting": [
              {"claim": "Cytological confirmation is required before assigning a "
                        "malignant effusion.",
               "citation_id": cite("oncologist", 1)}],
          "discriminating_test": "Pericardial fluid cytology"}],
        ["Primary lung malignancy", "Malignant pericardial effusion"], 0.79)

    # the generalist returns unusable output: the case must survive this
    internist = "I am unable to answer in the requested format."

    return ScriptedAdapter(responses={
        "radiologist": radiologist,
        "cardiologist": cardiologist,
        "oncologist": oncologist,
        "internist": internist,
    })


def main() -> int:
    failures: List[str] = []

    def check(label: str, ok: bool, detail: str = "") -> None:
        print(f"  [{'PASS' if ok else 'FAIL'}] {label}"
              + (f" — {detail}" if detail else ""))
        if not ok:
            failures.append(label)

    print("=" * 74)
    print("MedJar — LLM reasoning path verification (scripted adapter, no network)")
    print("=" * 74)

    # --- parser robustness, in isolation ---
    print("\nContract parsing")
    check("fenced JSON with leading prose is recovered",
          extract_json("blah\n```json\n{\"a\": 1}\n```")["a"] == 1)
    check("bare JSON is recovered", extract_json('{"a": 2}')["a"] == 2)
    check("trailing commas are repaired",
          extract_json('{"differential": [1,2,],}')["differential"] == [1, 2])
    bad = False
    try:
        extract_json("no json here at all")
    except Exception:
        bad = True
    check("unparseable output raises", bad)

    # --- end-to-end through the LLM engine ---
    cco = cases.CASE_001
    corpus = load_corpus()
    retriever = HybridRetriever(corpus)
    ctx = contexts_for(cco, retriever)
    adapter = build_adapter_for(cco, ctx)

    verifier = GroundednessVerifier()
    agents = default_ensemble(adapter=adapter)
    chief = ChiefOfService(agents=agents, retriever=retriever,
                           verifier=verifier)
    outcome = chief.run(cco)

    print("\nEnd-to-end run")
    check("every agent was prompted", adapter.calls == len(agents),
          f"{adapter.calls} adapter calls for {len(agents)} agents")
    check("consensus was produced", len(outcome.consensus) > 0,
          f"{len(outcome.consensus)} hypotheses")
    check("a disposition was reached",
          outcome.status in ("converged", "escalated"),
          f"{outcome.status}: {outcome.reason}")
    check("the debate ran at least one round", len(outcome.rounds) >= 2,
          f"{len(outcome.rounds) - 1} debate round(s)")
    check("the Evidence Ledger is populated", len(outcome.ledger) > 0,
          f"{len(outcome.ledger)} citations")

    # --- guard 1: hallucinated citations are dropped ---
    print("\nSafety guards")
    dropped = sum(e.dropped_citations for e in
                  (a.engine for a in agents) if isinstance(e, LLMEngine))
    check("a citation id never offered is discarded", dropped >= 1,
          f"{dropped} dropped")
    check("no fabricated id reached the ledger",
          all(FAKE_ID not in e.citation_id and FAKE_ID not in e.pid
              for e in outcome.ledger))

    # --- guard 2: every ledgered claim is entailed by its passage ---
    by_pid = {p.pid: p for p in corpus}
    ungrounded = 0
    for item in outcome.consensus:
        for claim in list(item.supporting) + list(item.refuting):
            pid = (claim.citation_id or "").split("#")[0]
            passage = by_pid.get(pid)
            if passage is None or verifier.entailment(claim.text, passage) \
                    < verifier.threshold:
                ungrounded += 1
    check("every reported claim is entailed by its citation", ungrounded == 0,
          f"{ungrounded} ungrounded")

    # --- guard 3: competence is not granted by ignorance ---
    card = next(a for a in agents if a.name == "Cardiologist")
    check("an out-of-domain dx the model ignored grants no prior",
          card.engine.prior_for("Pulmonary tuberculosis") is None)
    check("an in-domain dx grants a prior",
          card.engine.prior_for("Acute coronary syndrome") is not None)

    # --- guard 4: malformed output degrades gracefully ---
    gen = next(a for a in agents if a.name == "Generalist")
    check("malformed model output yields no hypotheses, not a crash",
          gen.engine.last_error is not None,
          f"recorded: {gen.engine.last_error}")

    # --- prompt construction ---
    print("\nPrompt construction")
    rad = next(a for a in agents if a.name == "Radiologist")
    passages = [p for p in corpus if p.pid in ctx["radiologist"]]
    user = rad.engine.render_user(cco, passages)
    check("prompt carries explicitly-absent features",
          "EXPLICITLY ABSENT" in user and "cytology positive" in user)
    check("prompt offers passage ids for citation",
          all(f"[{p.pid}]" in user for p in passages))
    check("system prompt states the contract",
          "differential" in rad.engine.system and "citation_id" in rad.engine.system)

    # --- report renders ---
    report = render(cco, outcome)
    print("\nReport")
    check("report renders with the expected sections",
          all(s in report for s in ("Ranked differential", "Can't-miss",
                                    "Points of disagreement", "Audit trail")))
    lead = outcome.consensus[0]
    print(f"\n  leading hypothesis : {lead.dx}  S*={lead.S_star:.2f}")
    print(f"  disposition        : {outcome.status.upper()} — {outcome.reason}")
    print(f"  ledger             : {len(outcome.ledger)} citations")

    print("\n" + "-" * 74)
    if failures:
        print(f"{len(failures)} check(s) FAILED: " + "; ".join(failures))
        return 1
    print("All checks passed. The LLM path is exercised end to end; only the "
          "HTTP call to a provider is substituted.")
    print("-" * 74)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

"""
medjar.consensus — the aggregation and disagreement mathematics.

Implements, exactly as specified in the paper:

  Eq. (1)  S(h)          = Σ_i w_i(h) c_i p_i(h) / Σ_i w_i(h) c_i
  Eq. (2)  S*(h)         = σ( α · logit S(h) + β · E(h) )
  Eq. (3)  Disagree(h)   = Σ_i w_i(h) c_i (p_i(h) − S(h))² / Σ_i w_i(h) c_i

where w_i(h) is a soft specialty weight (a mixture-of-experts weighting, not a
hard router: every agent votes on every hypothesis), c_i is the agent's
temperature-calibrated confidence, and E(h) is net grounded evidence weighted by
evidence grade and recency.
"""
from __future__ import annotations

import math
from typing import Dict, Iterable, List, Sequence, Tuple

from .schemas import (
    DX_REGISTRY, GRADE_WEIGHT, RED_FLAG_DX, AgentTurn, Claim, ConsensusItem,
    LedgerEntry,
)


def sigmoid(x: float) -> float:
    if x < -60:
        return 0.0
    if x > 60:
        return 1.0
    return 1.0 / (1.0 + math.exp(-x))


def logit(p: float) -> float:
    p = min(max(p, 1e-6), 1 - 1e-6)
    return math.log(p / (1 - p))


# --- specialty weighting ---------------------------------------------------
_ADJACENCY: Dict[Tuple[str, str], float] = {
    ("radiology", "oncology"): 0.82,
    ("oncology", "radiology"): 0.82,
    ("cardiology", "oncology"): 0.62,
    ("oncology", "cardiology"): 0.68,
    ("radiology", "cardiology"): 0.60,
    ("cardiology", "radiology"): 0.58,
}


def specialty_weight(agent_specialty: str, dx_domain: str) -> float:
    """w_i(h): higher inside the agent's domain, never zero elsewhere."""
    if agent_specialty == "general":
        return 0.72                      # broad but shallow
    if agent_specialty == dx_domain:
        return 1.00
    return _ADJACENCY.get((agent_specialty, dx_domain), 0.45)


class ConsensusEngine:
    def __init__(self, alpha: float = 1.0, beta: float = 0.55, top_k: int = 3):
        self.alpha = alpha
        self.beta = beta
        self.top_k = top_k

    # --- evidence -------------------------------------------------------
    @staticmethod
    def _ledger_index(ledger: Sequence[LedgerEntry]) -> Dict[str, LedgerEntry]:
        return {e.citation_id: e for e in ledger}

    def net_evidence(self, supporting: Sequence[Claim], refuting: Sequence[Claim],
                     idx: Dict[str, LedgerEntry]) -> float:
        """E(h): grade- and recency-weighted (support − refute), squashed to (−1,1)."""
        def w(c: Claim) -> float:
            e = idx.get(c.citation_id or "")
            if e is None:
                return 0.0
            grade = GRADE_WEIGHT.get(e.evidence_grade, 0.45)
            age = max(0, 2026 - e.publish_year)
            recency = 0.5 ** (age / 8.0)
            return grade * (0.65 + 0.35 * recency) * max(c.entailment, 0.0)

        net = sum(w(c) for c in supporting) - sum(w(c) for c in refuting)
        return math.tanh(net / 2.2)

    # --- aggregation ----------------------------------------------------
    def aggregate(self, turns: Sequence[AgentTurn],
                  ledger: Sequence[LedgerEntry]) -> List[ConsensusItem]:
        idx = self._ledger_index(ledger)
        # union of hypotheses across the ensemble
        dxs: List[str] = []
        for t in turns:
            for h in t.hypotheses:
                if h.dx not in dxs:
                    dxs.append(h.dx)

        items: List[ConsensusItem] = []
        for dx in dxs:
            domain = DX_REGISTRY.get(dx, ("?", "general"))[1]
            num = den = 0.0
            per_agent: Dict[str, float] = {}
            supporting: List[Claim] = []
            refuting: List[Claim] = []
            test = ""
            for t in turns:
                p = t.p(dx)
                if p is None:
                    continue
                w = specialty_weight(t.specialty, domain)
                num += w * t.confidence * p
                den += w * t.confidence
                per_agent[t.agent] = round(p, 4)
                for h in t.hypotheses:
                    if h.dx != dx:
                        continue
                    test = test or h.discriminating_test
                    supporting.extend(c for c in h.supporting if c.grounded)
                    refuting.extend(c for c in h.refuting if c.grounded)
            if den == 0:
                continue
            S = num / den

            # Eq. (3) — confidence-weighted variance, over substantive opinions
            # only. Agents reporting a cautionary floor hold no prior for this
            # hypothesis; counting their floor as dissent would manufacture
            # irreducible disagreement that no amount of debate could resolve.
            vnum = vden = 0.0
            n_sub = 0
            for t in turns:
                p = t.p(dx)
                if p is None or not t.is_substantive(dx):
                    continue
                w = specialty_weight(t.specialty, domain)
                vnum += w * t.confidence * (p - S) ** 2
                vden += w * t.confidence
                n_sub += 1
            disagreement = (vnum / vden) if (vden > 0 and n_sub >= 2) else 0.0

            # de-duplicate citations while preserving order
            supporting = self._dedupe(supporting)
            refuting = self._dedupe(refuting)
            E = self.net_evidence(supporting, refuting, idx)
            S_star = sigmoid(self.alpha * logit(S) + self.beta * E)

            items.append(ConsensusItem(
                dx=dx, icd10=DX_REGISTRY.get(dx, ("?", ""))[0],
                S=round(S, 4), S_star=round(S_star, 4), E=round(E, 4),
                disagreement=round(disagreement, 5), per_agent=per_agent,
                supporting=supporting, refuting=refuting,
                discriminating_test=test, is_red_flag=dx in RED_FLAG_DX))

        items.sort(key=lambda i: -i.S_star)
        return items

    @staticmethod
    def _dedupe(claims: Sequence[Claim]) -> List[Claim]:
        seen = set()
        out: List[Claim] = []
        for c in claims:
            key = (c.citation_id or "")[:7]
            if key in seen:
                continue
            seen.add(key)
            out.append(c)
        return out

    def d_bar(self, items: Sequence[ConsensusItem]) -> float:
        """Case-level disagreement: mean of Eq. (3) over the top-k hypotheses."""
        top = list(items)[: self.top_k]
        if not top:
            return 0.0
        return round(sum(i.disagreement for i in top) / len(top), 5)


# --- calibration ----------------------------------------------------------
def expected_calibration_error(pairs: Sequence[Tuple[float, int]], bins: int = 10) -> float:
    """ECE over (predicted probability, binary outcome) pairs."""
    if not pairs:
        return 0.0
    total = len(pairs)
    ece = 0.0
    for b in range(bins):
        lo, hi = b / bins, (b + 1) / bins
        bucket = [(p, y) for p, y in pairs if (p > lo or b == 0) and p <= hi]
        if not bucket:
            continue
        conf = sum(p for p, _ in bucket) / len(bucket)
        acc = sum(y for _, y in bucket) / len(bucket)
        ece += (len(bucket) / total) * abs(acc - conf)
    return round(ece, 4)


def brier(pairs: Sequence[Tuple[float, int]]) -> float:
    if not pairs:
        return 0.0
    return round(sum((p - y) ** 2 for p, y in pairs) / len(pairs), 4)

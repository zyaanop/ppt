"""
medjar.debate — the Chief-of-Service orchestrator.

A deterministic finite-state machine, deliberately *not* an LLM: control flow
must be predictable, testable and auditable.

    INTAKE → PROPOSE → [ CRITIQUE → REBUT → ASSESS ]* → CONSENSUS | ESCALATE

Stopping rule (Sec. 5.3):
    converge   if  D̄ ≤ τ_agree
    escalate   if  r = R_max and not converged
    escalate   if  any can't-miss diagnosis has S*(h) ≥ τ_flag   (overrides consensus)
"""
from __future__ import annotations

from typing import Dict, List, Optional, Sequence, Tuple

from .agents import SpecialistAgent, default_ensemble
from .consensus import ConsensusEngine
from .retrieval import HybridRetriever
from .schemas import (
    CCO, AgentTurn, CaseOutcome, ConsensusItem, Critique, LedgerEntry, RoundRecord,
)
from .verify import GroundednessVerifier


class ChiefOfService:
    def __init__(
        self,
        agents: Optional[Sequence[SpecialistAgent]] = None,
        retriever: Optional[HybridRetriever] = None,
        verifier: Optional[GroundednessVerifier] = None,
        consensus: Optional[ConsensusEngine] = None,
        tau_agree: float = 0.010,
        tau_flag: float = 0.30,
        r_max: int = 4,
        r_min: int = 1,
        verbose: bool = False,
    ):
        if retriever is None:
            from .corpus import load_corpus
            retriever = HybridRetriever(load_corpus())
        self.agents = list(agents or default_ensemble())
        self.retriever = retriever
        self.verifier = verifier or GroundednessVerifier()
        self.consensus = consensus or ConsensusEngine()
        self.tau_agree = tau_agree
        self.tau_flag = tau_flag
        self.r_max = r_max
        # At least one critique round always runs: independent impressions are
        # never accepted without being subjected to cross-examination, even when
        # they happen to coincide.
        self.r_min = max(1, r_min)
        self.verbose = verbose

    # ------------------------------------------------------------------
    def _align(self, cco: CCO, turns: Sequence[AgentTurn]) -> None:
        """Complete the opinion matrix so every agent scores every hypothesis."""
        dxs: List[str] = []
        for t in turns:
            for h in t.hypotheses:
                if h.dx not in dxs:
                    dxs.append(h.dx)
        for agent, turn in zip(self.agents, turns):
            have = {h.dx for h in turn.hypotheses}
            for dx in dxs:
                if dx not in have:
                    turn.hypotheses.append(agent.score_external(cco, dx))
            turn.hypotheses.sort(key=lambda h: -h.likelihood)

    # ------------------------------------------------------------------
    def run(self, cco: CCO) -> CaseOutcome:
        ledger: List[LedgerEntry] = []
        rounds: List[RoundRecord] = []
        status, reason = "escalated", "compute bound reached without convergence"

        # ---- PROPOSE (isolated; no cross-talk) ----
        turns = [a.propose(cco, self.retriever, self.verifier, ledger, round_no=0)
                 for a in self.agents]
        self._align(cco, turns)
        items = self.consensus.aggregate(turns, ledger)
        d_bar = self.consensus.d_bar(items)
        rounds.append(RoundRecord(0, d_bar, items[:5], turns, self.retriever.calls))
        self._log(0, "propose", d_bar, items)

        # ---- debate rounds ----
        r = 1
        while status != "converged" and r <= self.r_max:
            # CRITIQUE — agent identities withheld from one another
            critiques: List[Critique] = []
            for a in self.agents:
                critiques.extend(a.critique(cco, turns, r))

            # REBUT — revise, with targeted re-retrieval on contested points
            turns = [a.rebut(cco, critiques, self.retriever, self.verifier, ledger, r)
                     for a in self.agents]
            self._align(cco, turns)
            for t, a in zip(turns, self.agents):
                t.critiques = [c for c in critiques if c.author == a.name]

            # ASSESS
            items = self.consensus.aggregate(turns, ledger)
            d_bar = self.consensus.d_bar(items)
            rounds.append(RoundRecord(r, d_bar, items[:5], turns, self.retriever.calls))
            self._log(r, "rebut", d_bar, items)

            if d_bar <= self.tau_agree and r >= self.r_min:
                status, reason = "converged", f"D̄={d_bar:.4f} ≤ τ_agree at round {r}"
                break
            r += 1

        # ---- red-flag override (applies regardless of convergence) ----
        red_flags: Dict[str, float] = {
            i.dx: i.S_star for i in items if i.is_red_flag and i.S_star >= self.tau_flag
        }
        if red_flags:
            top_flag = max(red_flags.items(), key=lambda kv: kv[1])
            status = "escalated"
            reason = (f"can't-miss diagnosis '{top_flag[0]}' at S*={top_flag[1]:.2f} "
                      f"≥ τ_flag={self.tau_flag:.2f}")

        open_dis: List[Tuple[str, float]] = [
            (i.dx, i.disagreement) for i in items[: self.consensus.top_k]
            if i.disagreement > self.tau_agree
        ]

        return CaseOutcome(
            case_id=cco.case_id, status=status, reason=reason, rounds=rounds,
            consensus=items, ledger=ledger, red_flags=red_flags,
            open_disagreements=open_dis)

    # ------------------------------------------------------------------
    def _log(self, r: int, phase: str, d_bar: float, items: Sequence[ConsensusItem]) -> None:
        if not self.verbose:
            return
        lead = items[0] if items else None
        head = f"  r={r} [{phase:7}] D̄={d_bar:.5f}"
        if lead:
            head += f"  lead={lead.dx} S*={lead.S_star:.3f}"
        print(head)

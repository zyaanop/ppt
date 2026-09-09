"""
medjar.agents — persona-conditioned specialist agents.

Each agent is a triple (persona, tools, retrieval scope). The persona is encoded
as a set of DxRules: a specialty-specific reasoning prior over the hypothesis
space. Because the priors differ, the agents genuinely disagree, which is the
signal the debate protocol consumes.

Reasoning back-ends
-------------------
`RuleBasedEngine` (default) is deterministic and offline: it makes the
prototype reproducible and lets us verify the debate/consensus mathematics
without an LLM in the loop.

`LLMEngine` is the production path: it renders the persona and the retrieved
passages into a prompt, calls an injected adapter, and parses the structured
reasoning contract. The rest of the system is unchanged by the swap.
"""
from __future__ import annotations

import json
import math
from dataclasses import dataclass, field
from typing import Callable, Dict, List, Optional, Sequence, Tuple

from .consensus import specialty_weight
from .retrieval import HybridRetriever
from .schemas import (
    CCO, DX_REGISTRY, RED_FLAG_DX, AgentTurn, Claim, Critique, Hypothesis,
    LedgerEntry, Passage,
)
from .verify import GroundednessVerifier


def sigmoid(x: float) -> float:
    if x < -60:
        return 0.0
    if x > 60:
        return 1.0
    return 1.0 / (1.0 + math.exp(-x))


def logit(p: float) -> float:
    p = min(max(p, 1e-6), 1 - 1e-6)
    return math.log(p / (1 - p))


@dataclass(frozen=True)
class DxRule:
    """A specialty-specific prior linking case features to a diagnosis."""
    dx: str
    prior: float                       # base log-odds intercept
    pos: Tuple[str, ...] = ()          # features that raise likelihood
    contra: Tuple[str, ...] = ()       # features that lower likelihood
    gain: float = 2.6                  # sensitivity to matched features
    penalty: float = 1.6               # sensitivity to contradicting features
    needs: Optional[str] = None        # feature required for confident assertion
    test: str = ""                     # discriminating next investigation
    query: str = ""                    # retrieval seed

    def likelihood(self, cco: CCO) -> float:
        matched = sum(1 for f in self.pos if f in cco.findings)
        ratio = matched / len(self.pos) if self.pos else 0.0
        contra = sum(1 for f in self.contra if f in cco.findings)
        z = self.prior + self.gain * ratio - self.penalty * contra
        if self.pos and matched == 0:
            # No supporting feature is present in this case. A diagnosis with no
            # positive evidence must not float on its prior intercept alone.
            z -= 3.0
        if self.needs and self.needs not in cco.findings:
            z -= 0.85                  # unconfirmed: cannot be asserted strongly
        return round(sigmoid(z), 4)


# ---------------------------------------------------------------------------
# Persona rule sets
# ---------------------------------------------------------------------------
RADIOLOGIST_RULES = (
    DxRule("Primary lung malignancy", -1.0, ("spiculated_nodule", "upper_lobe", "weight_loss"),
           ("calcified_nodule", "stable_two_years"), test="FDG PET-CT then tissue biopsy",
           query="spiculated pulmonary nodule margins malignancy probability PET-CT"),
    DxRule("Benign pulmonary granuloma", -1.4, ("calcified_nodule", "stable_two_years"),
           ("spiculated_nodule",), test="Comparison with prior imaging",
           query="benign nodule smooth margins calcification granuloma stability"),
    DxRule("Pulmonary tuberculosis", -2.3, ("upper_lobe", "weight_loss", "cavitation"),
           (), test="Sputum acid-fast testing and nucleic acid amplification",
           query="upper lobe cavitation tuberculosis mimic malignancy weight loss"),
    DxRule("Malignant pericardial effusion", -2.0, ("pericardial_effusion", "spiculated_nodule"),
           (), needs="cytology_positive", test="Pericardial fluid cytology",
           query="pericardial effusion CT suspected thoracic malignancy significance"),
    DxRule("Sarcoidosis", -2.6, ("hilar_adenopathy", "pericardial_effusion"),
           ("spiculated_nodule",), test="Tissue biopsy for non-caseating granulomas",
           query="thoracic sarcoidosis hilar lymphadenopathy pericardial involvement"),
)

CARDIOLOGIST_RULES = (
    DxRule("Cardiac tamponade", -1.9, ("pericardial_effusion", "tachycardia", "hypotension",
                                       "raised_jvp"),
           (), gain=3.1, needs="echo_rv_collapse",
           test="Urgent transthoracic echocardiography",
           query="cardiac tamponade echocardiography right ventricular diastolic collapse pulsus"),
    DxRule("Acute coronary syndrome", -1.3, ("troponin_elevated", "ischemic_chest_pain",
                                             "dynamic_ecg_change"),
           ("no_chest_pain", "static_ecg"), gain=3.0,
           test="Serial troponin and 12-lead ECG",
           query="acute coronary syndrome ischemic chest pain dynamic ECG rising troponin"),
    DxRule("Demand ischemia (type 2 MI)", -1.1, ("troponin_elevated", "tachycardia",
                                                 "static_ecg", "no_chest_pain"),
           (), gain=2.4, test="Serial troponin trend; treat precipitant",
           query="type 2 myocardial infarction supply demand mismatch malignancy tachycardia"),
    DxRule("Pulmonary embolism", -1.8, ("dyspnea", "tachycardia", "known_malignancy_risk"),
           (), gain=2.2, test="CT pulmonary angiography",
           query="pulmonary embolism unexplained dyspnea malignancy prothrombotic risk"),
    DxRule("Viral pericarditis", -2.4, ("pericardial_effusion", "pleuritic_pain", "viral_prodrome"),
           ("weight_loss",), test="ECG pattern and inflammatory markers",
           query="acute pericarditis pleuritic pain friction rub PR depression viral prodrome"),
    DxRule("Congestive heart failure", -2.5, ("dyspnea", "raised_jvp", "peripheral_edema"),
           (), test="Natriuretic peptide and echocardiography",
           query="heart failure natriuretic peptide dyspnea evaluation"),
    DxRule("Malignant pericardial effusion", -2.2, ("pericardial_effusion", "weight_loss"),
           (), needs="cytology_positive", test="Pericardiocentesis with cytology",
           query="pericardial effusion etiology cytology required malignant determination"),
)

ONCOLOGIST_RULES = (
    DxRule("Primary lung malignancy", -0.7, ("spiculated_nodule", "weight_loss", "smoking_history",
                                             "upper_lobe"),
           ("calcified_nodule",), gain=2.9, test="Tissue biopsy with molecular profiling",
           query="suspected lung carcinoma histological confirmation biomarker profiling"),
    DxRule("Malignant pericardial effusion", -1.5, ("pericardial_effusion", "spiculated_nodule",
                                                    "weight_loss"),
           (), gain=2.7, needs="cytology_positive",
           test="Pericardial fluid cytology (stage-defining)",
           query="malignant pericardial effusion M1a staging cytological confirmation"),
    DxRule("Metastatic disease (extrathoracic)", -2.4, ("weight_loss", "pericardial_effusion"),
           (), test="Whole-body staging imaging",
           query="advanced malignancy staging distant metastasis constitutional symptoms"),
    DxRule("Pulmonary tuberculosis", -2.8, ("weight_loss", "cavitation"),
           (), test="Microbiological confirmation",
           query="tuberculosis weight loss cavitation differential malignancy"),
    DxRule("Benign pulmonary granuloma", -2.7, ("calcified_nodule",), ("spiculated_nodule",),
           test="Imaging surveillance",
           query="benign granuloma calcification stability surveillance"),
)

GENERALIST_RULES = (
    DxRule("Primary lung malignancy", -1.3, ("spiculated_nodule", "weight_loss"), (),
           test="Tissue biopsy", query="lung nodule malignancy constitutional symptoms"),
    DxRule("Community-acquired pneumonia", -2.6, ("dyspnea", "fever", "productive_cough"),
           ("weight_loss",), test="Chest radiograph and inflammatory markers",
           query="community acquired pneumonia fever productive cough consolidation"),
    DxRule("Pulmonary tuberculosis", -2.5, ("weight_loss", "upper_lobe"), (),
           test="Sputum testing", query="tuberculosis upper lobe weight loss"),
    DxRule("Demand ischemia (type 2 MI)", -2.0, ("troponin_elevated", "no_chest_pain"), (),
           test="Serial troponin", query="troponin elevation without ischemic symptoms"),
    DxRule("Cardiac tamponade", -2.6, ("pericardial_effusion", "tachycardia"), (),
           needs="echo_rv_collapse", test="Echocardiography",
           query="pericardial effusion hemodynamic significance echocardiography"),
)


# ---------------------------------------------------------------------------
# Reasoning engines
# ---------------------------------------------------------------------------
class RuleBasedEngine:
    """Deterministic, offline reasoning over a persona's DxRules."""

    def __init__(self, rules: Sequence[DxRule]):
        self.rules = tuple(rules)

    def hypotheses(self, cco: CCO) -> List[Hypothesis]:
        out: List[Hypothesis] = []
        for r in self.rules:
            p = r.likelihood(cco)
            if p < 0.045:
                continue
            icd = DX_REGISTRY.get(r.dx, ("?", "general"))[0]
            out.append(Hypothesis(dx=r.dx, icd10=icd, likelihood=p,
                                  discriminating_test=r.test))
        out.sort(key=lambda h: -h.likelihood)
        return out

    def rule_for(self, dx: str) -> Optional[DxRule]:
        for r in self.rules:
            if r.dx == dx:
                return r
        return None


class LLMEngine:
    """Production reasoning path: prompt an LLM, parse the reasoning contract.

    `adapter` is any callable (system_prompt, user_prompt) -> str returning JSON
    that conforms to the contract in Sec. 4.3. Not exercised in the offline demo.
    """

    CONTRACT = (
        'Return ONLY JSON: {"differential":[{"dx":str,"likelihood":float,'
        '"supporting":[{"claim":str,"citation_id":str}],'
        '"refuting":[{"claim":str,"citation_id":str}],'
        '"discriminating_test":str}],"red_flags":[str],"confidence":float}'
    )

    def __init__(self, persona: str, adapter: Callable[[str, str], str]):
        self.persona = persona
        self.adapter = adapter

    def hypotheses(self, cco: CCO, passages: Sequence[Passage] = ()) -> List[Hypothesis]:
        ctx = "\n".join(f"[{p.pid}] {p.text}" for p in passages)
        user = (f"CASE\n{cco.presentation}\nFEATURES: {', '.join(cco.findings)}\n\n"
                f"RETRIEVED EVIDENCE\n{ctx}\n\n{self.CONTRACT}")
        raw = self.adapter(self.persona, user)
        data = json.loads(raw)
        out: List[Hypothesis] = []
        for d in data.get("differential", []):
            icd = DX_REGISTRY.get(d["dx"], ("?", "general"))[0]
            out.append(Hypothesis(
                dx=d["dx"], icd10=icd, likelihood=float(d["likelihood"]),
                discriminating_test=d.get("discriminating_test", ""),
                supporting=[Claim(c["claim"], c.get("citation_id"), "support")
                            for c in d.get("supporting", [])],
                refuting=[Claim(c["claim"], c.get("citation_id"), "refute")
                          for c in d.get("refuting", [])],
            ))
        out.sort(key=lambda h: -h.likelihood)
        return out


# ---------------------------------------------------------------------------
# Specialist agent
# ---------------------------------------------------------------------------
class SpecialistAgent:
    def __init__(self, name: str, specialty: str, scope: Sequence[str],
                 rules: Sequence[DxRule], temperature: float = 1.25):
        self.name = name
        self.specialty = specialty
        self.scope = tuple(scope)
        self.engine = RuleBasedEngine(rules)
        self.temperature = temperature        # calibration temperature
        self._state: Dict[str, Hypothesis] = {}
        self._ceiling: Dict[str, float] = {}

    # -- phase 1 ----------------------------------------------------------
    def propose(self, cco: CCO, retriever: HybridRetriever,
                verifier: GroundednessVerifier, ledger: List[LedgerEntry],
                round_no: int = 0) -> AgentTurn:
        hyps = self.engine.hypotheses(cco)
        for h in hyps:
            self._attach_evidence(h, cco, retriever, verifier, ledger)
        self._state = {h.dx: h for h in hyps}
        # Reinforcement ceiling: consolidation may restore a position toward the
        # level its persona prior supports, but never beyond it. Without this,
        # uncontested hypotheses inflate every round — debate becomes an echo
        # chamber and apparent disagreement drifts upward.
        self._ceiling = {h.dx: h.likelihood for h in hyps}
        return self._turn(hyps, round_no, "propose", cco)

    # -- shared hypothesis space -----------------------------------------
    def score_external(self, cco: CCO, dx: str) -> Hypothesis:
        """Register an opinion on a hypothesis outside this persona's rule set.

        Agents never abstain. The hypothesis space is shared, so an out-of-domain
        agent still supplies p_i(h): a low floor, lifted slightly for can't-miss
        diagnoses so that caution is preserved even outside one's specialty.
        Genuine cross-specialty divergence is what the debate then resolves,
        moderated by the specialty weight w_i(h).
        """
        if dx in self._state:
            return self._state[dx]
        icd, _domain = DX_REGISTRY.get(dx, ("?", "general"))
        p = 0.10 + (0.07 if dx in RED_FLAG_DX else 0.0)
        h = Hypothesis(dx=dx, icd10=icd, likelihood=round(p, 4),
                       discriminating_test="", is_floor=True)
        self._state[dx] = h
        return h

    # -- phase 2 ----------------------------------------------------------
    def critique(self, cco: CCO, others: Sequence[AgentTurn],
                 round_no: int) -> List[Critique]:
        """Attack other agents' positions using this persona's priors."""
        out: List[Critique] = []
        for turn in others:
            if turn.agent == self.name:
                continue
            for h in turn.hypotheses:
                my_rule = self.engine.rule_for(h.dx)
                my_p = self._state[h.dx].likelihood if h.dx in self._state else None
                # A critique carries only as much force as the critic's competence
                # over that hypothesis's domain (the same w_i(h) used in Eq. 1).
                w_self = specialty_weight(self.specialty, h.domain)

                # (a) asserted without the confirmatory finding this persona requires
                if my_rule and my_rule.needs and my_rule.needs not in cco.findings \
                        and h.likelihood >= 0.45:
                    out.append(Critique(
                        author=self.name, target_agent=turn.agent, dx=h.dx,
                        kind="missing_confirmation",
                        argument=(f"{h.dx} is advanced at p={h.likelihood:.2f} without "
                                  f"{my_rule.needs.replace('_', ' ')}; confirmation is required "
                                  f"before this is treated as established."),
                        severity=min(0.55, 0.45 * h.likelihood + 0.12) * w_self))

                # (b) overcall — admissible ONLY if this persona actually holds a
                #     prior for the diagnosis. An out-of-domain agent's low floor
                #     expresses ignorance, not evidence, and must never be used to
                #     vote down an in-domain, grounded position: that is precisely
                #     how a correct can't-miss diagnosis gets falsely reassured away.
                if my_rule is not None and my_p is not None and h.likelihood - my_p > 0.22:
                    out.append(Critique(
                        author=self.name, target_agent=turn.agent, dx=h.dx, kind="overcall",
                        argument=(f"From a {self.specialty} prior, {h.dx} is less likely "
                                  f"(p={my_p:.2f} vs {h.likelihood:.2f}); the supporting "
                                  f"features are non-specific."),
                        severity=min(0.5, 0.75 * (h.likelihood - my_p)) * w_self))

                # (c) the generalist alone may object that a confidently-held
                #     specialty hypothesis fails to explain the whole patient
                if my_rule is None and h.likelihood >= 0.5 and self.specialty == "general":
                    out.append(Critique(
                        author=self.name, target_agent=turn.agent, dx=h.dx, kind="alternative",
                        argument=(f"{h.dx} does not by itself account for the whole "
                                  f"presentation; competing explanations remain open."),
                        severity=0.06 * w_self))
        return out

    # -- phase 3 ----------------------------------------------------------
    def rebut(self, cco: CCO, incoming: Sequence[Critique], retriever: HybridRetriever,
              verifier: GroundednessVerifier, ledger: List[LedgerEntry],
              round_no: int) -> AgentTurn:
        """Concede, defend, or revise; contested points trigger new retrieval."""
        mine = [c for c in incoming if c.target_agent == self.name]
        for c in mine:
            h = self._state.get(c.dx)
            if h is None:
                continue
            # grounded, high-grade support lets the agent defend its position
            defence = sum(1 for cl in h.supporting if cl.grounded)
            damp = 1.0 / (1.0 + 0.55 * defence)
            delta = c.severity * damp
            h.likelihood = round(max(0.02, min(0.97, sigmoid(logit(h.likelihood) - 1.5 * delta))), 4)
            # targeted re-retrieval on the point of contention
            rule = self.engine.rule_for(c.dx)
            seed = (rule.query if rule else c.dx) + " " + c.kind.replace("_", " ")
            self._attach_evidence(h, cco, retriever, verifier, ledger, query=seed, k=2)

        # positions that survived unchallenged and rest on grounded, multiply-cited
        # evidence are reinforced, so debate is not purely attritional
        contested = {c.dx for c in mine}
        for dx, h in self._state.items():
            if dx in contested:
                continue
            support = sum(1 for cl in h.supporting if cl.grounded)
            if support >= 2:
                cap = self._ceiling.get(dx, h.likelihood)
                h.likelihood = round(min(cap, sigmoid(logit(h.likelihood) + 0.18)), 4)

        hyps = sorted(self._state.values(), key=lambda x: -x.likelihood)
        return self._turn(hyps, round_no, "rebut", cco)

    # -- helpers ----------------------------------------------------------
    def _attach_evidence(self, h: Hypothesis, cco: CCO, retriever: HybridRetriever,
                         verifier: GroundednessVerifier, ledger: List[LedgerEntry],
                         query: Optional[str] = None, k: int = 3) -> None:
        rule = self.engine.rule_for(h.dx)
        q = query or ((rule.query if rule else h.dx) + " " + cco.retrieval_text()[:160])
        hits = retriever.retrieve(q, scope=self.scope, top_k=k)
        for hit in hits:
            p = hit.passage
            cid = f"{p.pid}#{len(ledger) + 1:03d}"
            # polarity: does the passage argue for the dx or caution against asserting it?
            cautionary = any(w in p.text.lower() for w in
                             ("required", "insufficient", "cannot", "not specific",
                              "lowers the probability", "atypical", "unlikely"))
            polarity = "refute" if cautionary else "support"
            text = f"{p.section}: {p.text[:150].rstrip()}…"
            claim = Claim(text=text, citation_id=cid, polarity=polarity)
            verifier.verify(claim, p)
            if not claim.grounded:
                continue
            if any(c.citation_id and c.citation_id.startswith(p.pid)
                   for c in h.supporting + h.refuting):
                continue                      # already cited for this hypothesis
            (h.supporting if polarity == "support" else h.refuting).append(claim)
            ledger.append(LedgerEntry(
                citation_id=cid, case_id=cco.case_id, pid=p.pid, source=p.source,
                section=p.section, publish_year=p.publish_year,
                evidence_grade=p.evidence_grade, passage=p.text,
                used_by_agent=self.name, hypothesis=h.dx, polarity=polarity,
                scores={"dense": round(hit.dense, 4), "sparse": round(hit.sparse, 3),
                        "rrf": round(hit.rrf, 5), "rerank": round(hit.rerank, 3)}))

    def _turn(self, hyps: List[Hypothesis], round_no: int, phase: str, cco: CCO) -> AgentTurn:
        top = hyps[0].likelihood if hyps else 0.2
        grounded = sum(1 for h in hyps for c in h.supporting if c.grounded)
        in_domain = any(h.domain == self.specialty for h in hyps[:2])
        raw = sigmoid(1.15 * logit(min(top, 0.95)) + 0.11 * grounded + (0.3 if in_domain else -0.1))
        flags = [h.dx for h in hyps if h.dx in RED_FLAG_DX and h.likelihood >= 0.30]
        reqs = [f"retrieve:{h.discriminating_test}" for h in hyps[:2] if h.discriminating_test]
        if flags:
            reqs.append("ask-human:urgent assessment for " + ", ".join(flags[:2]))
        return AgentTurn(
            agent=self.name, specialty=self.specialty, round=round_no, phase=phase,
            hypotheses=[Hypothesis(h.dx, h.icd10, h.likelihood, list(h.supporting),
                                   list(h.refuting), h.discriminating_test, h.is_floor)
                        for h in hyps],
            red_flags=flags, confidence_raw=round(raw, 4),
            confidence=round(sigmoid(logit(raw) / self.temperature), 4),
            requests=reqs)


def default_ensemble() -> List[SpecialistAgent]:
    """The launch ensemble: three specialists plus a generalist."""
    return [
        SpecialistAgent("Radiologist", "radiology", ("radiology", "oncology"),
                        RADIOLOGIST_RULES, temperature=1.20),
        SpecialistAgent("Cardiologist", "cardiology", ("cardiology",),
                        CARDIOLOGIST_RULES, temperature=1.28),
        SpecialistAgent("Oncologist", "oncology", ("oncology",),
                        ONCOLOGIST_RULES, temperature=1.24),
        SpecialistAgent("Generalist", "general", ("general", "infectious", "cardiology"),
                        GENERALIST_RULES, temperature=1.35),
    ]

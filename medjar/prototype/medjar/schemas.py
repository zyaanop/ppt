"""
medjar.schemas — canonical data structures for the MedJar prototype.

Every object that crosses a layer boundary is defined here so that the
reasoning contract (Sec. 4.3 of the paper) is enforced structurally rather
than by convention. Standard library only.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Sequence, Tuple

# --------------------------------------------------------------------------
# Diagnosis registry: name -> (ICD-10, clinical domain)
# The domain drives the specialty weight w_i(h) in the consensus engine.
# --------------------------------------------------------------------------
DX_REGISTRY: Dict[str, Tuple[str, str]] = {
    "Primary lung malignancy":            ("C34.90", "oncology"),
    "Malignant pericardial effusion":     ("C79.89", "oncology"),
    "Metastatic disease (extrathoracic)": ("C79.9",  "oncology"),
    "Cardiac tamponade":                  ("I31.4",  "cardiology"),
    "Acute coronary syndrome":            ("I24.9",  "cardiology"),
    "Demand ischemia (type 2 MI)":        ("I21.A1", "cardiology"),
    "Pulmonary embolism":                 ("I26.99", "cardiology"),
    "Viral pericarditis":                 ("I30.1",  "cardiology"),
    "Pulmonary tuberculosis":             ("A15.0",  "infectious"),
    "Community-acquired pneumonia":       ("J18.9",  "infectious"),
    "Sarcoidosis":                        ("D86.0",  "general"),
    "Benign pulmonary granuloma":         ("D14.30", "radiology"),
    "Congestive heart failure":           ("I50.9",  "cardiology"),
}

# Diagnoses that must never be silently down-ranked ("can't-miss").
RED_FLAG_DX: Tuple[str, ...] = (
    "Cardiac tamponade",
    "Acute coronary syndrome",
    "Pulmonary embolism",
    "Primary lung malignancy",
    "Malignant pericardial effusion",
)

# Evidence-grade weights used when computing net evidence E(h).
GRADE_WEIGHT: Dict[str, float] = {
    "I-A": 1.00, "I-B": 0.88, "IIa-B": 0.72,
    "IIb-B": 0.58, "III-C": 0.40, "review": 0.50, "textbook": 0.45,
}


@dataclass(frozen=True)
class Passage:
    """An indexed, citable unit of the knowledge corpus."""
    pid: str
    source: str
    section: str
    publish_year: int
    evidence_grade: str
    specialty_tags: Tuple[str, ...]
    text: str

    def grade_weight(self) -> float:
        return GRADE_WEIGHT.get(self.evidence_grade, 0.45)

    def recency_weight(self, now: int = 2026, half_life: float = 8.0) -> float:
        """Exponential decay so stale guidance carries less weight."""
        age = max(0, now - self.publish_year)
        return 0.5 ** (age / half_life)


@dataclass
class RetrievalHit:
    passage: Passage
    dense: float = 0.0
    sparse: float = 0.0
    rrf: float = 0.0
    rerank: float = 0.0


@dataclass
class Claim:
    """An assertion an agent makes, bound to a citation."""
    text: str
    citation_id: Optional[str]
    polarity: str                  # "support" | "refute"
    entailment: float = 0.0        # groundedness score in [0,1]
    grounded: bool = False


@dataclass
class Hypothesis:
    dx: str
    icd10: str
    likelihood: float                              # p_i(h)
    supporting: List[Claim] = field(default_factory=list)
    refuting: List[Claim] = field(default_factory=list)
    discriminating_test: str = ""
    is_floor: bool = False
    """True when the agent holds no persona prior for this diagnosis and is
    reporting only a cautionary floor. Floors participate in the ensemble score
    S(h) (with reduced specialty weight) but are excluded from the disagreement
    metric: absence of an opinion is not dissent."""

    @property
    def domain(self) -> str:
        return DX_REGISTRY.get(self.dx, ("", "general"))[1]


@dataclass
class Critique:
    """A grounded objection raised by one agent against another's hypothesis."""
    author: str
    target_agent: str
    dx: str
    kind: str          # unsupported | missing_confirmation | alternative | overcall
    argument: str
    citation_id: Optional[str] = None
    severity: float = 0.0          # [0,1]; scales the likelihood penalty


@dataclass
class AgentTurn:
    agent: str
    specialty: str
    round: int
    phase: str                     # propose | critique | rebut
    hypotheses: List[Hypothesis] = field(default_factory=list)
    critiques: List[Critique] = field(default_factory=list)
    red_flags: List[str] = field(default_factory=list)
    confidence_raw: float = 0.5
    confidence: float = 0.5        # calibrated c_i
    requests: List[str] = field(default_factory=list)

    def p(self, dx: str) -> Optional[float]:
        for h in self.hypotheses:
            if h.dx == dx:
                return h.likelihood
        return None

    def is_substantive(self, dx: str) -> bool:
        """True if this agent holds a genuine prior (not a floor) for `dx`."""
        for h in self.hypotheses:
            if h.dx == dx:
                return not h.is_floor
        return False


@dataclass
class LedgerEntry:
    """Append-only provenance record (Evidence Ledger)."""
    citation_id: str
    case_id: str
    pid: str
    source: str
    section: str
    publish_year: int
    evidence_grade: str
    passage: str
    used_by_agent: str
    hypothesis: str
    polarity: str
    scores: Dict[str, float] = field(default_factory=dict)


@dataclass
class CCO:
    """Case Context Object — the de-identified, normalized shared representation."""
    case_id: str
    age: int
    sex: str
    presentation: str
    findings: Tuple[str, ...]           # canonical feature keys
    vitals: Dict[str, float] = field(default_factory=dict)
    labs: List[Dict[str, object]] = field(default_factory=list)
    imaging: List[Dict[str, str]] = field(default_factory=list)
    absent: Tuple[str, ...] = ()        # explicitly-negated findings
    gold_dx: Optional[str] = None       # for evaluation only; never shown to agents

    def has(self, *keys: str) -> bool:
        return all(k in self.findings for k in keys)

    def any_of(self, *keys: str) -> bool:
        return any(k in self.findings for k in keys)

    def retrieval_text(self) -> str:
        return f"{self.presentation} " + " ".join(f.replace("_", " ") for f in self.findings)


@dataclass
class ConsensusItem:
    dx: str
    icd10: str
    S: float            # Eq. (1) confidence-weighted score
    S_star: float       # Eq. (2) evidence-adjusted score
    E: float            # net grounded evidence
    disagreement: float # Eq. (3)
    per_agent: Dict[str, float] = field(default_factory=dict)
    supporting: List[Claim] = field(default_factory=list)
    refuting: List[Claim] = field(default_factory=list)
    discriminating_test: str = ""
    is_red_flag: bool = False


@dataclass
class RoundRecord:
    round: int
    D_bar: float
    top: List[ConsensusItem]
    turns: List[AgentTurn]
    retrievals: int


@dataclass
class CaseOutcome:
    case_id: str
    status: str                 # "converged" | "escalated"
    reason: str
    rounds: List[RoundRecord]
    consensus: List[ConsensusItem]
    ledger: List[LedgerEntry]
    red_flags: Dict[str, float]
    open_disagreements: List[Tuple[str, float]]

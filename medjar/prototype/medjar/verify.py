"""
medjar.verify — groundedness verification.

Every clinical claim an agent makes must be entailed by the passage it cites.
Production systems use a trained NLI model; here we use a lexical-coverage
surrogate with the same interface and the same gate semantics: a claim whose
entailment score falls below `threshold` is marked ungrounded and is excluded
from consensus aggregation.
"""
from __future__ import annotations

from typing import Iterable, Optional

from .retrieval import tokenize
from .schemas import Claim, Passage


class GroundednessVerifier:
    def __init__(self, threshold: float = 0.34):
        self.threshold = threshold
        self.checked = 0
        self.rejected = 0

    def entailment(self, claim_text: str, passage: Optional[Passage]) -> float:
        """Fraction of the claim's content terms covered by the cited passage."""
        if passage is None:
            return 0.0
        c = set(tokenize(claim_text))
        if not c:
            return 0.0
        d = set(tokenize(passage.section + " " + passage.text))
        return len(c & d) / len(c)

    def verify(self, claim: Claim, passage: Optional[Passage]) -> Claim:
        self.checked += 1
        claim.entailment = round(self.entailment(claim.text, passage), 3)
        claim.grounded = claim.entailment >= self.threshold and claim.citation_id is not None
        if not claim.grounded:
            self.rejected += 1
        return claim

    def rate(self) -> float:
        """Proportion of checked claims that passed the gate."""
        if not self.checked:
            return 0.0
        return 1.0 - self.rejected / self.checked

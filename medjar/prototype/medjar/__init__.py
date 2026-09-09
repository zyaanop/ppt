"""
MedJar — a multi-agent consensus system for complex medical diagnosis.

Research prototype. Standard library only, fully deterministic, offline.

    from medjar import ChiefOfService, cases, render
    outcome = ChiefOfService().run(cases.CASE_001)
    print(render(cases.CASE_001, outcome))

This software is a research demonstration on synthetic data. It is not a
medical device, produces no clinical advice, and must not be used for care.
"""
from __future__ import annotations

from . import cases
from .agents import (
    CARDIOLOGIST_RULES, GENERALIST_RULES, ONCOLOGIST_RULES, RADIOLOGIST_RULES,
    DxRule, LLMEngine, RuleBasedEngine, SpecialistAgent, default_ensemble,
)
from .consensus import (
    ConsensusEngine, brier, expected_calibration_error, specialty_weight,
)
from .corpus import load_corpus
from .debate import ChiefOfService
from .report import render, render_transcript
from .retrieval import BM25Index, DenseIndex, HybridRetriever, tokenize
from .schemas import CCO, DX_REGISTRY, RED_FLAG_DX, CaseOutcome, ConsensusItem
from .verify import GroundednessVerifier

__version__ = "0.1.0"

__all__ = [
    "CCO", "CaseOutcome", "ConsensusItem", "DX_REGISTRY", "RED_FLAG_DX",
    "ChiefOfService", "ConsensusEngine", "SpecialistAgent", "DxRule",
    "RuleBasedEngine", "LLMEngine", "HybridRetriever", "BM25Index", "DenseIndex",
    "GroundednessVerifier", "default_ensemble", "load_corpus", "render",
    "render_transcript", "tokenize", "specialty_weight",
    "expected_calibration_error", "brier", "cases",
    "RADIOLOGIST_RULES", "CARDIOLOGIST_RULES", "ONCOLOGIST_RULES", "GENERALIST_RULES",
]

# MedJar
### A Multi-Agent Consensus System for Complex Medical Diagnosis

**A Seminar-Grade Research Report**

> *"No single mind holds the whole of medicine. The best diagnoses emerge from a room of disagreeing experts who are forced to reconcile their evidence."*

| | |
|---|---|
| **System** | MedJar — Medical Judgment via Agent Reasoning |
| **Paradigm** | Multi-agent LLM debate + Retrieval-Augmented Generation (RAG) |
| **Domain** | Clinical decision support for complex / multi-system cases |
| **Positioning** | Assistive, human-in-the-loop; **not** an autonomous diagnostician |
| **Document type** | Research seminar (architecture, formalism, evaluation, ethics) |

---

## Table of Contents

1. [Abstract](#1-abstract)
2. [Executive Summary](#2-executive-summary)
3. [Problem Statement & Motivation](#3-problem-statement--motivation)
4. [Background & Related Work](#4-background--related-work)
5. [System Architecture Overview](#5-system-architecture-overview)
6. [The Specialist Agent Ensemble](#6-the-specialist-agent-ensemble)
7. [Knowledge Grounding: The RAG Pipeline](#7-knowledge-grounding-the-rag-pipeline)
8. [The Debate & Consensus Protocol](#8-the-debate--consensus-protocol)
9. [Orchestration: The Chief-of-Service State Machine](#9-orchestration-the-chief-of-service-state-machine)
10. [Multimodal Case Ingestion](#10-multimodal-case-ingestion)
11. [The Unified Diagnostic Report](#11-the-unified-diagnostic-report)
12. [Evaluation Methodology](#12-evaluation-methodology)
13. [Safety, Ethics & Regulatory Compliance](#13-safety-ethics--regulatory-compliance)
14. [Limitations & Failure Modes](#14-limitations--failure-modes)
15. [Implementation Stack](#15-implementation-stack)
16. [Roadmap](#16-roadmap)
17. [References](#17-references)
18. [Appendix A — Agent System Prompts](#appendix-a--agent-system-prompts)
19. [Appendix B — Data Schemas](#appendix-b--data-schemas)
20. [Appendix C — Worked Case Walkthrough](#appendix-c--worked-case-walkthrough)

---

## 1. Abstract

Diagnostic error affects an estimated **1 in 20 adults** in outpatient care and contributes to a substantial fraction of serious patient harm. Complex cases — those spanning multiple organ systems, presenting with atypical findings, or sitting at the boundary of several specialties — are disproportionately vulnerable, because they require the integration of expertise that no single clinician (or single language model) fully possesses.

**MedJar** is a multi-agent consensus system that operationalizes the clinical "tumor board" or "morbidity & mortality conference" as a computational protocol. Independent large-language-model (LLM) agents are instantiated as domain specialists — **Radiologist**, **Cardiologist**, **Oncologist**, and extensible others — each equipped with (a) a persona-conditioned reasoning prior, (b) private access to a **retrieval-augmented generation (RAG)** layer over curated medical literature and guidelines, and (c) the patient's structured and unstructured case files. The agents produce independent differential diagnoses, then engage in a **structured, adversarial-cooperative debate** moderated by an orchestrator ("Chief of Service"). Disagreement is treated as a first-class signal: it triggers targeted evidence retrieval, uncertainty quantification, and, where consensus cannot be reached, an explicit escalation to a human clinician.

The system emits a **single, provenance-linked diagnostic report** containing a ranked differential, per-hypothesis evidence and counter-evidence, calibrated confidence, recommended next investigations, and a full audit trail of the reasoning. This document specifies MedJar's architecture, formalizes its consensus mathematics, and details its evaluation, safety, and regulatory framework.

---

## 2. Executive Summary

- **What it is:** A decision-support layer that convenes multiple specialist LLM agents to debate a case and converge on a defensible, evidence-grounded differential diagnosis.
- **Why it matters:** Ensemble disagreement surfaces the blind spots that cause diagnostic error; RAG grounding suppresses hallucination and ties every claim to a citation.
- **Key innovations:**
  1. **Persona-conditioned specialist agents** with distinct reasoning priors and retrieval scopes.
  2. A **structured debate protocol** (propose → critique → rebut → converge) rather than naive majority voting.
  3. **Disagreement as a control signal** — drives adaptive retrieval and human escalation.
  4. **Calibrated, provenance-linked confidence** on every hypothesis.
  5. **Human-in-the-loop by design** — MedJar recommends; the clinician decides.
- **What it is *not*:** An autonomous diagnostic device, a replacement for a physician, or a system that should ever act without clinician sign-off.

---

## 3. Problem Statement & Motivation

### 3.1 The clinical problem

Complex diagnosis fails for structural reasons, not merely individual ones:

| Failure mode | Description | How MedJar addresses it |
|---|---|---|
| **Anchoring bias** | Fixating on an initial impression and discounting contradictory data. | Independent agents anchor differently; debate forces reconciliation. |
| **Premature closure** | Ending the workup once a plausible answer appears. | The orchestrator requires each hypothesis to survive adversarial critique. |
| **Specialty siloing** | A cardiologist and an oncologist rarely reason on the same case simultaneously. | All specialists reason on the case concurrently and must respond to each other. |
| **Knowledge staleness** | Guidelines evolve faster than any individual can track. | RAG retrieves current, versioned guideline text at inference time. |
| **Hallucinated confidence** | LLMs assert false facts fluently. | Every claim must be grounded in a retrieved, cited passage; ungrounded claims are penalized. |

### 3.2 Why a single LLM is insufficient

A single model conditioned on "you are an expert physician" collapses the diversity of clinical reasoning into one distribution. It cannot represent the *productive tension* between specialties. Empirically, single-model chain-of-thought is prone to (i) self-consistent but wrong reasoning chains, and (ii) overconfident calibration. Ensembling with **structured disagreement** is the mechanism that recovers the value of a real multidisciplinary team.

### 3.3 Design goals

- **G1 — Grounded:** No diagnostic claim without a citation.
- **G2 — Transparent:** Every conclusion is traceable to inputs and evidence.
- **G3 — Calibrated:** Confidence scores must match empirical accuracy.
- **G4 — Safe:** Uncertainty and red-flags escalate to humans; the system never "closes" a dangerous case silently.
- **G5 — Auditable:** The full debate is logged and replayable.

---

## 4. Background & Related Work

MedJar sits at the intersection of four research threads. *(Citations are indicative of the literature families; see §17.)*

1. **Multi-agent LLM debate & self-refinement** — work showing that agents that critique and debate reach more accurate, better-calibrated conclusions than single models (e.g., "society of minds" debate, multi-agent reflection, LLM-as-judge protocols).
2. **Retrieval-Augmented Generation (RAG)** — grounding generation in retrieved documents to reduce hallucination and enable citation; extensions include hybrid dense/sparse retrieval, re-ranking, and graph RAG.
3. **Clinical LLMs & medical QA** — domain-adapted models and benchmarks (MedQA/USMLE, MedMCQA, PubMedQA, MIMIC-based tasks) that measure medical reasoning.
4. **Ensemble & mixture-of-experts diagnosis** — classical work on combining diagnostic classifiers, plus the clinical evidence that multidisciplinary team review improves outcomes in oncology and complex care.

**MedJar's contribution** is to fuse these: a *specialist* multi-agent debate that is *individually RAG-grounded* and *orchestrated toward calibrated consensus with explicit human escalation*, specialized for the clinical setting rather than general QA.

---

## 5. System Architecture Overview

MedJar is a layered pipeline. Data flows top-to-bottom; control (the debate loop) circulates within the Reasoning layer.

```
┌──────────────────────────────────────────────────────────────────────┐
│  0. INTAKE LAYER                                                       │
│     Patient case files → de-identification → normalization             │
│     (EHR/FHIR, labs, imaging, notes, genomics)                         │
└───────────────────────────────┬──────────────────────────────────────┘
                                 ▼
┌──────────────────────────────────────────────────────────────────────┐
│  1. REPRESENTATION LAYER                                               │
│     Multimodal encoders → unified Case Context Object (CCO)            │
│     • Text embeddings   • Image findings   • Structured features       │
└───────────────────────────────┬──────────────────────────────────────┘
                                 ▼
┌──────────────────────────────────────────────────────────────────────┐
│  2. KNOWLEDGE LAYER (RAG)                                              │
│     Vector store + BM25 + re-ranker over guidelines, textbooks,        │
│     journals, drug DBs. Per-specialty retrieval scopes.                │
└───────────────────────────────┬──────────────────────────────────────┘
                                 ▼
┌──────────────────────────────────────────────────────────────────────┐
│  3. REASONING LAYER  ◄──────────── the debate loop lives here          │
│     ┌──────────┐ ┌──────────┐ ┌──────────┐   ...extensible            │
│     │Radiolog. │ │Cardiolog.│ │Oncolog.  │                            │
│     └────┬─────┘ └────┬─────┘ └────┬─────┘                            │
│          └──── CHIEF-OF-SERVICE ORCHESTRATOR ────┘                     │
│               propose → critique → rebut → converge                    │
└───────────────────────────────┬──────────────────────────────────────┘
                                 ▼
┌──────────────────────────────────────────────────────────────────────┐
│  4. CONSENSUS & CALIBRATION LAYER                                      │
│     Weighted aggregation • uncertainty • red-flag detection            │
│     • human-escalation gate                                            │
└───────────────────────────────┬──────────────────────────────────────┘
                                 ▼
┌──────────────────────────────────────────────────────────────────────┐
│  5. REPORTING LAYER                                                    │
│     Unified diagnostic report + provenance + audit log                 │
└──────────────────────────────────────────────────────────────────────┘
```

**Core components:**

- **Case Context Object (CCO):** the canonical, de-identified, multimodal representation of the patient shared by all agents.
- **Specialist Agents:** persona-conditioned LLMs with private retrieval scopes.
- **Chief-of-Service Orchestrator:** a deterministic controller that runs the debate state machine, allocates turns, and enforces stopping/escalation rules.
- **Evidence Ledger:** an append-only store of every retrieved passage, claim, and citation, keyed to the case.
- **Consensus Engine:** aggregates positions with calibrated, confidence-weighted voting.

---

## 6. The Specialist Agent Ensemble

Each agent is a triplet **A = ⟨persona, tools, scope⟩**:

- **persona** — a system prompt encoding the specialty's reasoning style, priors, and "what this specialist worries about first."
- **tools** — RAG retrieval, unit/lab-range calculators, scoring tools (e.g., risk scores), and image-finding lookups.
- **scope** — the subset of the knowledge base the agent preferentially retrieves from (e.g., the Radiologist over imaging atlases; the Oncologist over staging and NCCN-style guideline text).

### 6.1 The launch specialists

| Agent | Reasoning prior | Primary inputs | Retrieval scope | Characteristic question |
|---|---|---|---|---|
| **Radiologist** | Pattern → localization → differential by imaging morphology | DICOM-derived findings, prior imaging, reports | Imaging atlases, ACR appropriateness criteria, radiographic sign databases | *"What does the image actually show, independent of the referral hypothesis?"* |
| **Cardiologist** | Hemodynamics, rhythm, ischemia, structure | ECG, echo, troponin/BNP, vitals, cath data | ESC/ACC guidelines, cardiac risk scores, ECG pattern libraries | *"Is there a cardiac cause or cardiac consequence we must not miss?"* |
| **Oncologist** | Tissue of origin, staging, biomarkers, tempo | Pathology, tumor markers, imaging staging, genomics | Staging manuals, oncology guidelines, biomarker/therapy databases | *"Is this neoplastic, and if so, what is the stage-defining evidence?"* |

### 6.2 Extensibility

The ensemble is a plug-in registry. Adding a **Neurologist**, **Infectious Disease**, **Endocrinologist**, or **Pathologist** requires only a new persona spec + retrieval scope; the orchestration and consensus layers are agent-agnostic. A **Generalist/Internist** agent is always present to guard against over-specialization and to represent the "whole patient."

### 6.3 Reasoning contract

Every agent must return a structured object per turn (see Appendix B), never free prose alone:

```json
{
  "differential": [
    {"dx": "…", "icd10": "…", "likelihood": 0.0-1.0,
     "supporting_evidence": [{"claim": "…", "citation_id": "…"}],
     "refuting_evidence":  [{"claim": "…", "citation_id": "…"}],
     "discriminating_test": "…"}
  ],
  "red_flags": ["…"],
  "confidence": 0.0-1.0,
  "requests": ["retrieve:…", "ask-human:…"]
}
```

This contract makes positions **comparable, aggregable, and auditable**.

---

## 7. Knowledge Grounding: The RAG Pipeline

RAG is the mechanism that satisfies **G1 (grounded)**. Every clinical claim an agent makes must be attributable to a retrieved passage in the Evidence Ledger.

### 7.1 Corpus

- **Guidelines** (cardiology, oncology, radiology appropriateness, sepsis, etc.) — versioned, with effective dates.
- **Reference texts & review articles** (curated, licensed).
- **Drug & interaction databases.**
- **Coding ontologies** — ICD-10, SNOMED CT, LOINC, RxNorm — used both for retrieval and for structured output.
- **Institution-local protocols** (optional overlay).

Each document is chunked (semantically, not by fixed length), embedded, and stored with rich metadata: `{source, section, publish_date, evidence_grade, specialty_tags}`.

### 7.2 Retrieval

Hybrid retrieval maximizes recall and precision:

1. **Dense retrieval** — embed the query (agent's sub-question + relevant CCO fields) and search a vector index (cosine similarity).
2. **Sparse retrieval** — BM25 over the same corpus to catch exact clinical terms, drug names, gene symbols.
3. **Fusion** — Reciprocal Rank Fusion (RRF) merges the two ranked lists:

   \[
   \text{RRF}(d) = \sum_{r \in \{dense, sparse\}} \frac{1}{k + \text{rank}_r(d)}, \quad k \approx 60
   \]

4. **Re-ranking** — a cross-encoder re-scores the top-N candidates against the exact query for precision.
5. **Scope filtering** — results are filtered/boosted by the requesting agent's specialty scope and by guideline recency.

### 7.3 Grounding & anti-hallucination

- The generation prompt injects only retrieved passages and instructs the agent to **cite passage IDs inline**.
- A **groundedness check** (an NLI-style verifier) tests each output claim against its cited passage; unsupported claims are flagged and down-weighted before they can enter the debate.
- Retrieved passages, their scores, and the resulting citations are written to the **Evidence Ledger** — this is what makes the final report provenance-linked.

### 7.4 Why per-specialty scopes matter

Global retrieval would return the same passages to every agent, homogenizing their views and destroying the diversity that makes debate valuable. Scoped retrieval preserves specialty perspective while the debate protocol forces cross-scope reconciliation.

---

## 8. The Debate & Consensus Protocol

This is MedJar's intellectual core. Naive approaches (majority vote over one-shot answers) discard *why* agents disagree. MedJar instead runs a **structured multi-round debate** and treats disagreement as information.

### 8.1 The four phases

**Phase 1 — Independent Proposal (no cross-talk).**
Each agent `Aᵢ` reads the CCO, retrieves privately, and emits an independent differential `Dᵢ`. Isolation here is deliberate: it prevents early anchoring and preserves diversity. This is the ensemble's "prior."

**Phase 2 — Critique (adversarial).**
Agents see each other's differentials (anonymized to reduce authority bias). Each agent produces targeted critiques: which hypotheses lack support, which evidence is misread, which discriminating test is missing. Critiques must themselves be grounded.

**Phase 3 — Rebuttal & Revision.**
Each agent responds to critiques of its own positions and revises its differential. New retrieval is triggered by the specific points of contention (disagreement drives retrieval). Agents may concede, defend, or reformulate.

**Phase 4 — Convergence / Escalation.**
The orchestrator measures agreement. If the ensemble has converged within tolerance, the Consensus Engine aggregates. If not, either another round runs (up to `R_max`) or the case escalates to a human with the open disagreement made explicit.

### 8.2 Consensus mathematics

Let hypotheses be indexed by `h ∈ H` (the union of all agents' differentials). Agent `Aᵢ` assigns a likelihood `pᵢ(h) ∈ [0,1]` to hypothesis `h` and carries a **competence weight** `wᵢ(h)` that depends on the *match between the hypothesis and the agent's specialty*.

**Confidence-weighted aggregation.** The ensemble score for hypothesis `h`:

\[
S(h) = \frac{\sum_{i} w_i(h)\, c_i \, p_i(h)}{\sum_{i} w_i(h)\, c_i}
\]

where `cᵢ` is agent `i`'s self-reported, **calibrated** confidence (post-hoc temperature/Platt-scaled against a validation set so that stated confidence matches empirical accuracy).

**Specialty weighting.** `wᵢ(h)` is higher when `h` falls inside agent `i`'s domain (e.g., the Oncologist's weight on a malignancy hypothesis > the Cardiologist's), encoded as a learned or expert-set relevance matrix. This is a *soft* mixture-of-experts, not a hard router — every agent still votes on every hypothesis.

**Disagreement metric.** Ensemble disagreement on `h` is the weighted variance:

\[
\mathrm{Disagree}(h) = \frac{\sum_i w_i(h)\, c_i \,\big(p_i(h) - S(h)\big)^2}{\sum_i w_i(h)\, c_i}
\]

Aggregate case disagreement `D̄ = mean over top-k hypotheses`. High `D̄` is the trigger for another debate round or human escalation.

**Evidence adjustment.** Each hypothesis score is modulated by the **net grounded evidence** `E(h)` = (weighted supporting citations − weighted refuting citations), so that positions backed by higher-grade, more recent guidelines are rewarded:

\[
S^{*}(h) = \sigma\!\Big(\alpha \cdot \operatorname{logit} S(h) + \beta \cdot E(h)\Big)
\]

with `σ` the logistic function and `α, β` tuned on validation data.

### 8.3 Stopping rule

The debate halts when **either**:
- `D̄ ≤ τ_agree` (converged), **or**
- round count `r = R_max` (bounded compute), **or**
- a **red-flag** ("can't-miss" diagnosis, e.g., aortic dissection, PE, sepsis, malignancy) is raised by any agent with confidence above `τ_flag` — this forces immediate escalation regardless of consensus.

### 8.4 Why debate beats voting

| Property | Majority vote | MedJar debate |
|---|---|---|
| Uses *reasons*, not just answers | ✗ | ✓ (critique/rebuttal are grounded) |
| Adapts retrieval to conflict | ✗ | ✓ |
| Surfaces minority "can't-miss" dx | ✗ (outvoted) | ✓ (red-flag override) |
| Produces calibrated uncertainty | Weak | ✓ (disagreement → uncertainty) |
| Auditable rationale | ✗ | ✓ (full transcript) |

---

## 9. Orchestration: The Chief-of-Service State Machine

The orchestrator is intentionally **deterministic** (not an LLM making free-form control decisions) so that control flow is predictable, testable, and auditable.

```
        ┌─────────┐
        │  INTAKE │
        └────┬────┘
             ▼
      ┌─────────────┐      each agent retrieves + proposes
      │  PROPOSE    │─────────────────────────────┐
      └──────┬──────┘                              │
             ▼                                      │
      ┌─────────────┐                               │
      │  CRITIQUE   │  agents attack each other's   │
      └──────┬──────┘  differentials (grounded)     │
             ▼                                      │
      ┌─────────────┐                               │
      │  REBUT      │  revise + targeted retrieval  │
      └──────┬──────┘                               │
             ▼                                      │
      ┌─────────────┐   compute D̄, red-flags        │
      │  ASSESS     │                               │
      └──┬───┬───┬──┘                               │
  conv.  │   │   │  not conv. & r<R_max             │
   ▼     │   │   └─────────────────────────────────┘  (loop)
┌──────┐ │   │  red-flag OR r=R_max & not conv.
│CONSEN│ │   └──────────────┐
│ -SUS │ │                  ▼
└──┬───┘ │           ┌──────────────┐
   │     │           │  ESCALATE     │  → human clinician
   ▼     ▼           │  (open Δ)     │     with full transcript
 ┌───────────┐       └──────────────┘
 │  REPORT   │
 └───────────┘
```

**Orchestrator responsibilities:**
- Turn allocation & anonymization of agent identities during critique.
- Enforcing the reasoning contract (rejecting malformed / ungrounded turns).
- Computing `D̄`, evidence scores, and evaluating the stopping rule.
- Managing the Evidence Ledger and audit log.
- Enforcing latency/compute budgets (`R_max`, per-turn token caps).

---

## 10. Multimodal Case Ingestion

Real cases are heterogeneous. The **Intake** and **Representation** layers normalize everything into the CCO.

| Modality | Source | Processing | CCO field |
|---|---|---|---|
| **Structured EHR** | FHIR/HL7, EHR export | Schema mapping, unit normalization, LOINC/ICD/RxNorm coding | `vitals, labs, problems, meds, allergies` |
| **Clinical notes** | Discharge summaries, H&P, progress notes | De-identification, section parsing, entity + negation extraction | `narrative, extracted_findings` |
| **Imaging** | DICOM (CT, MRI, X-ray, echo) | Vision model → structured findings + report parsing; **no raw pixels leave the enclave** | `imaging_findings` |
| **Pathology** | Reports, (optionally) WSI features | Report parsing, biomarker extraction | `pathology` |
| **Genomics** | VCF, panel reports | Variant annotation, actionable-mutation flags | `genomics` |
| **Waveforms** | ECG, telemetry | Feature extraction (intervals, morphology) | `ecg_features` |

**De-identification** (Safe Harbor / expert determination) runs at the boundary; the reasoning layer never sees direct identifiers. A reversible token map is held only in a separate, access-controlled service to re-attach identity to the final report for the treating clinician.

---

## 11. The Unified Diagnostic Report

The output is a single artifact designed for a clinician to act on in minutes.

**Report structure:**

1. **Header** — case ID, timestamp, model/guideline versions, participating agents.
2. **One-line synthesis** — the ensemble's leading impression in a sentence.
3. **Ranked differential** — each hypothesis with:
   - Calibrated probability `S*(h)` and a plain-language confidence band.
   - **Supporting evidence** (with citations to the Evidence Ledger).
   - **Refuting / caveat evidence.**
   - **Discriminating next test** (what would most change the probabilities).
4. **Red-flag panel** — can't-miss diagnoses and their status (excluded / needs work-up).
5. **Points of disagreement** — where and why the specialists diverged (never hidden).
6. **Recommended next steps** — investigations, referrals, and their rationale.
7. **Confidence & escalation status** — converged vs. escalated-to-human.
8. **Full audit trail** — the debate transcript and evidence, available on expand.

**Design principle:** the report leads with uncertainty and disagreement rather than burying them, because the clinical value is in knowing *what MedJar is unsure about*.

---

## 12. Evaluation Methodology

MedJar must be evaluated as a **clinical decision-support tool**, not merely as a QA model.

### 12.1 Datasets & benchmarks

- **Structured medical reasoning:** MedQA (USMLE), MedMCQA, PubMedQA — sanity checks on medical knowledge.
- **Case-based:** curated de-identified complex cases (e.g., clinicopathological conference-style cases with known final diagnoses), NEJM-style diagnostic cases, MIMIC-derived scenarios.
- **Prospective silent trials:** run alongside real workups without influencing care; compare MedJar's differential to the eventual confirmed diagnosis.

### 12.2 Metrics

| Dimension | Metric |
|---|---|
| **Accuracy** | Top-1 / Top-3 differential hit rate vs. gold diagnosis |
| **Calibration** | Expected Calibration Error (ECE), reliability diagrams, Brier score |
| **Safety** | Can't-miss recall (sensitivity for red-flag diagnoses); false-reassurance rate |
| **Groundedness** | % of claims entailed by their citation; hallucination rate |
| **Utility** | Blinded clinician ratings of usefulness, novelty of surfaced hypotheses |
| **Efficiency** | Latency, token/compute cost per case, rounds-to-converge |
| **Fairness** | Accuracy & calibration parity across demographic strata |

### 12.3 Ablations

- Single agent vs. ensemble (isolate the value of multiple specialists).
- Voting vs. structured debate (isolate the value of the protocol).
- With vs. without RAG (isolate grounding's effect on hallucination & accuracy).
- Uncalibrated vs. calibrated confidence (isolate the calibration layer).

### 12.4 Human evaluation

Board-certified specialists blind-review a sample of reports for **correctness, completeness, safety, and actionability** on a Likert scale, with adjudication of disagreements. The primary safety endpoint is the **false-reassurance rate** — how often MedJar down-ranks a can't-miss diagnosis that was in fact present.

---

## 13. Safety, Ethics & Regulatory Compliance

> **MedJar is assistive.** It produces recommendations for a licensed clinician who remains the decision-maker and is accountable for care. It is not a substitute for professional medical judgment, and it does not autonomously diagnose or treat.

### 13.1 Regulatory posture

- **FDA (US):** Clinical decision-support that drives diagnosis is likely a **Software as a Medical Device (SaMD)**. MedJar targets the "clinician can independently review the basis" exemption criteria by making all evidence and reasoning transparent — but any real deployment requires a formal regulatory strategy (predetermined change-control plan for the model, clinical validation, post-market surveillance).
- **CE / MDR (EU):** analogous conformity assessment.
- **Good Machine Learning Practice (GMLP):** followed for data management, training, and monitoring.

### 13.2 Privacy & security

- **HIPAA / GDPR:** de-identification at intake; PHI held in an access-controlled enclave; audit logging of every access; encryption in transit and at rest.
- **Data residency & minimization:** only the fields needed for reasoning enter the CCO.
- **No training on patient data** without explicit governance and consent.

### 13.3 Bias & equity

- Corpus and evaluation stratified by demographics; calibration checked per subgroup.
- Guardrails against propagating historical inequities encoded in guidelines or notes.
- Continuous fairness monitoring in production.

### 13.4 Accountability & the human gate

- **Mandatory human sign-off** before any recommendation informs care.
- **Escalation over confidence:** when uncertain or when a red-flag fires, MedJar escalates rather than closing the case.
- **Full auditability:** every report is reproducible from its logged inputs, retrieved evidence, and debate transcript.

---

## 14. Limitations & Failure Modes

Honest accounting of where MedJar can fail:

- **Garbage-in:** incomplete or erroneous case files degrade every downstream step; MedJar cannot order the physical exam or history it lacks.
- **Correlated errors:** if all agents share a base model, they may share blind spots; mitigation = heterogeneous base models + a devil's-advocate agent + RAG grounding.
- **Corpus staleness / gaps:** RAG is only as good as its corpus; requires disciplined curation and versioning.
- **Persuasive-but-wrong debate:** an eloquent agent can win a debate on rhetoric; mitigation = groundedness verification and evidence-weighted (not rhetoric-weighted) aggregation.
- **Automation bias in clinicians:** users may over-trust the report; mitigation = leading with uncertainty/disagreement and never showing a bare answer.
- **Distribution shift:** rare diseases and novel presentations are under-represented; the escalation gate is the safety net.
- **Compute & latency:** multi-round, multi-agent, multi-retrieval is expensive; bounded by `R_max` and budget caps, with a fast single-pass "triage mode" for time-critical settings.

---

## 15. Implementation Stack

*Reference architecture — components are swappable.*

| Layer | Technology choices |
|---|---|
| **Agent runtime / orchestration** | Deterministic Python orchestrator; agent framework (e.g., LangGraph-style state machine) with typed message passing |
| **LLMs** | Heterogeneous foundation models per agent (frontier + medical-tuned); temperature low for factual turns, higher for hypothesis generation |
| **RAG** | Vector DB (e.g., pgvector / FAISS / Qdrant) + BM25 (e.g., OpenSearch) + cross-encoder re-ranker; RRF fusion |
| **Embeddings** | Medical-domain text embeddings; image encoder for DICOM findings |
| **Data** | FHIR ingestion; ICD-10 / SNOMED CT / LOINC / RxNorm ontology services |
| **Verification** | NLI-based groundedness checker; calibration (temperature/Platt scaling) |
| **Storage / audit** | Append-only Evidence Ledger; immutable audit log; PHI enclave |
| **Serving** | Async task queue; per-case budget & timeout enforcement; observability/tracing |
| **Presentation** | This report (Markdown), the animated HTML deck, and the PPTX are the communication layer |

---

## 16. Roadmap

- **Phase 0 — Prototype:** three agents (Radiologist, Cardiologist, Oncologist) + generalist, text-only cases, single corpus. Validate the debate protocol on retrospective cases.
- **Phase 1 — Multimodal & calibrated:** add imaging/ECG ingestion, calibration layer, groundedness verifier, expanded corpus.
- **Phase 2 — Prospective silent trial:** deploy read-only alongside clinicians; measure top-k accuracy, calibration, and false-reassurance.
- **Phase 3 — Regulated pilot:** IRB-approved, human-in-the-loop deployment in a narrow indication; post-market monitoring; regulatory submission.
- **Phase 4 — Scale:** additional specialties, institution-local protocol overlays, continuous learning under change-control.

---

## 17. References

*Indicative sources spanning the four research families in §4. Full bibliographic details to be finalized for publication.*

1. Multi-agent debate improves reasoning and factuality in large language models — *society-of-minds / multi-agent debate literature.*
2. Self-refinement and reflection in LLMs — *iterative critique improves output quality.*
3. Lewis et al. — *Retrieval-Augmented Generation for knowledge-intensive NLP tasks.*
4. Cross-encoder re-ranking and hybrid dense/sparse retrieval — *RRF fusion.*
5. Jin et al. — *MedQA / USMLE-style medical question answering benchmark.*
6. Pal et al. — *MedMCQA multi-subject medical QA benchmark.*
7. Jin et al. — *PubMedQA biomedical question answering.*
8. Singhal et al. — *Large language models encode clinical knowledge (Med-PaLM line of work).*
9. Institute of Medicine / National Academies — *Improving Diagnosis in Health Care (diagnostic error).*
10. Guo et al. — *On calibration of modern neural networks (temperature scaling).*
11. Multidisciplinary tumor board / M&M conference literature — *team review improves complex-case outcomes.*
12. FDA — *Clinical Decision Support Software guidance & Good Machine Learning Practice principles.*

> **Note:** References are provided as research-family pointers for a seminar setting. Verify and complete citations against primary sources before any formal publication or clinical claim.

---

## Appendix A — Agent System Prompts

*Abbreviated templates. Each is parameterized by the CCO and retrieval results.*

**Radiologist (excerpt):**
```
You are a board-certified radiologist participating in a multidisciplinary case review.
Reason from the images and imaging reports FIRST, independent of the referral question.
Describe findings by morphology and localization, then build an imaging-based differential.
Every clinical claim MUST cite a retrieved passage by its citation_id.
Return ONLY the structured reasoning contract. Flag any can't-miss imaging finding.
```

**Cardiologist (excerpt):**
```
You are a board-certified cardiologist. Prioritize ruling out life-threatening cardiac
etiologies (ACS, dissection, PE, tamponade, malignant arrhythmia). Integrate ECG, biomarkers,
imaging, and hemodynamics. Cite guideline passages (ESC/ACC) for every recommendation.
Return ONLY the structured reasoning contract.
```

**Oncologist (excerpt):**
```
You are a board-certified oncologist. Assess whether findings are neoplastic; if so, identify
tissue of origin, stage-defining evidence, and actionable biomarkers. Distinguish confirmed
from suspected malignancy. Cite staging manuals / oncology guidelines for every claim.
Return ONLY the structured reasoning contract.
```

**Chief-of-Service Orchestrator (control policy, not free-form LLM):**
```
Deterministic controller. Enforce reasoning contract. Run PROPOSE→CRITIQUE→REBUT→ASSESS.
Compute weighted disagreement D̄ and evidence scores. Apply stopping rule
(D̄≤τ_agree | r=R_max | red-flag>τ_flag → ESCALATE). Never let an ungrounded claim
enter aggregation. Log everything to the Evidence Ledger and audit trail.
```

---

## Appendix B — Data Schemas

**Case Context Object (CCO):**
```json
{
  "case_id": "uuid",
  "demographics": {"age": 0, "sex": "…", "flags": []},
  "vitals": {"…": "…"},
  "labs": [{"loinc": "…", "value": 0, "unit": "…", "ref_range": "…", "flag": "H/L/N"}],
  "problems": [{"icd10": "…", "text": "…"}],
  "meds": [{"rxnorm": "…", "name": "…"}],
  "allergies": ["…"],
  "narrative": "de-identified free text",
  "imaging_findings": [{"modality": "CT", "region": "…", "finding": "…", "impression": "…"}],
  "pathology": [{"specimen": "…", "result": "…", "biomarkers": ["…"]}],
  "genomics": [{"gene": "…", "variant": "…", "actionable": true}],
  "ecg_features": {"rate": 0, "rhythm": "…", "intervals": {"…": 0}}
}
```

**Agent turn (reasoning contract):** see §6.3.

**Evidence Ledger entry:**
```json
{
  "citation_id": "uuid",
  "case_id": "uuid",
  "source": "ESC Guidelines 2023, §5.2",
  "publish_date": "2023-08-25",
  "evidence_grade": "Class I / Level A",
  "passage": "verbatim retrieved text",
  "retrieval_scores": {"dense": 0.0, "sparse": 0.0, "rerank": 0.0},
  "used_by_agent": "cardiologist",
  "supports_or_refutes": {"hypothesis": "…", "polarity": "support"}
}
```

---

## Appendix C — Worked Case Walkthrough

**Case (synthetic, illustrative):** 58-year-old with progressive dyspnea, unintentional weight loss, a spiculated right-upper-lobe pulmonary nodule on CT, mildly elevated troponin, and a small pericardial effusion.

1. **Propose (independent):**
   - *Radiologist:* spiculated RUL nodule → primary lung malignancy high on differential; recommends PET-CT and biopsy; notes pericardial effusion.
   - *Cardiologist:* elevated troponin + effusion → must exclude ACS and malignant pericardial involvement / tamponade physiology; recommends echo, serial troponin.
   - *Oncologist:* weight loss + spiculated nodule → suspected primary lung cancer; effusion raises concern for metastatic pericardial disease → would upstage.

2. **Critique:** Cardiologist challenges Oncologist's assumption the effusion is malignant without cytology; Radiologist notes the troponin could be demand ischemia, not ACS. Oncologist critiques closing the case before tissue diagnosis.

3. **Rebut + retrieve:** targeted retrieval on "malignant pericardial effusion staging implications" and "troponin elevation in malignancy vs ACS." Positions revised: consensus that **tissue + effusion cytology are the discriminating tests**, and that **tamponade physiology is the can't-miss** to exclude now.

4. **Assess:** moderate disagreement on *stage*, high agreement on *next steps*; red-flag (tamponade) raised → **escalate with explicit open question** (is there hemodynamic compromise?).

5. **Report:** leading impression = probable primary lung malignancy with possible pericardial involvement; ranked differential with citations; red-flag panel flags tamponade to exclude urgently; discriminating tests = biopsy + effusion cytology + echo; **status: escalated to human** for urgent cardiac assessment.

*This is exactly the multidisciplinary reasoning a tumor board performs — made explicit, grounded, and auditable.*

---

*End of document. Companion deliverables: `presentation.html` (animated deck) and `MedJar.pptx` (PowerPoint).*

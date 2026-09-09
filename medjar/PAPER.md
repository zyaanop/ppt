# MedJar: Consensus Diagnosis by Debating Specialist Agents

**A multi-agent architecture with retrieval grounding, calibrated aggregation, and explicit human escalation for complex medical diagnosis**

MedJar Working Group · Clinical Machine Learning / Decision-Support Systems
Technical report · research prototype

> **Scope and status.** This is a research report describing an architecture and a
> working prototype evaluated on **three synthetic cases**. It is not a clinical
> study, not a validated medical device, and produces no clinical advice. Numeric
> results characterise the prototype's mechanics, not diagnostic performance.

---

## Abstract

Diagnostic error affects an estimated 5% of adults in outpatient care annually and
concentrates in complex presentations that cross specialty boundaries. Such cases
require the integration of expertise no single clinician — and no single language
model — fully possesses. We present **MedJar**, an architecture that operationalises
the multidisciplinary case conference as a computational protocol. Persona-conditioned
language-model agents act as specialists (radiologist, cardiologist, oncologist, plus a
generalist), each with a distinct reasoning prior and a *private, specialty-scoped*
retrieval channel over a versioned, evidence-graded corpus. Agents first produce
independent differentials in isolation, then engage in a structured
propose → critique → rebut → assess protocol moderated by a deterministic orchestrator.

Three properties distinguish MedJar from majority-vote ensembling. First, the protocol
operates on *grounded reasons*: every clinical claim must be entailed by a cited
passage before it can influence aggregation. Second, disagreement is a **control
signal** — we define a confidence-weighted variance over the shared hypothesis space
and use it, together with a can't-miss override, as the stopping rule. Third, the
system is designed to escalate rather than conclude: unresolved disagreement and
can't-miss diagnoses route to a clinician with the open question stated explicitly.

We implement the full pipeline as a dependency-free, deterministic prototype
(§5) and report its behaviour on three synthetic cases (§6): the leading hypothesis
matched the reference diagnosis in 3/3 cases, all 130 emitted claims passed the
groundedness gate, and the three cases exercised all three stopping paths
(convergence, plateau-with-escalation, can't-miss override). Calibration was poor
(ECE 0.243), which we report as a negative result: the aggregation weights are
hand-set rather than fitted, and §6.4 documents four failure modes the
implementation exposed — including one, *incompetent critique*, in which
out-of-domain agents voted down a correct can't-miss diagnosis, producing exactly
the false reassurance the system exists to prevent.

**Keywords:** multi-agent systems, retrieval-augmented generation, clinical decision
support, uncertainty calibration, diagnostic reasoning

---

## Contents

1. [Introduction](#1-introduction)
2. [Related work](#2-related-work)
3. [Problem formulation](#3-problem-formulation)
4. [System design](#4-system-design)
5. [Implementation](#5-implementation)
6. [Evaluation](#6-evaluation)
7. [Safety, ethics, and regulatory posture](#7-safety-ethics-and-regulatory-posture)
8. [Limitations and threats to validity](#8-limitations-and-threats-to-validity)
9. [Conclusion](#9-conclusion)
· [References](#references) · [Appendix A](#appendix-a--algorithms)
· [Appendix B](#appendix-b--schemas) · [Appendix C](#appendix-c--worked-case)

---

## 1. Introduction

### 1.1 Diagnostic error is a systems problem

Diagnostic error is not primarily a deficit of individual knowledge; it is a
property of how diagnostic work is organised. The National Academies' review
[[1]](#references) identifies recurring structural contributors: **anchoring**, in which
an initial impression suppresses competing hypotheses; **premature closure**, in
which the search terminates once a plausible answer appears; **specialty siloing**,
in which the experts whose priors would resolve the case never reason on it
simultaneously; and **knowledge drift**, as guidelines evolve faster than any
individual tracks them.

Clinical practice already has a countermeasure: the tumour board and the morbidity
and mortality conference, where independent specialists are compelled to state
positions, attack each other's reasoning, and reconcile against evidence. The
mechanism that makes these effective is not consensus but *structured
disagreement*. MedJar asks whether that mechanism can be made computational.

### 1.2 Why a single model is insufficient

Conditioning one model with *"you are an expert physician"* collapses the diversity
of clinical reasoning into a single distribution. Three consequences follow.

- **Correlated failure.** One prior yields one blind spot, with no internal
  adversary to surface the missed diagnosis.
- **Miscalibrated confidence.** Fluent assertion is weakly related to correctness;
  single-model chain-of-thought produces self-consistent but wrong trajectories at
  high stated confidence [[9]](#references).
- **Unverifiable grounding.** Claims not bound to a citable source cannot be
  checked, audited, or contested.

Naive ensembling addresses the first only partially and the others not at all:
majority voting over one-shot answers discards *why* agents differ and
systematically silences the minority can't-miss diagnosis — the single most
consequential error mode in acute care.

### 1.3 Contributions

1. **A specialist multi-agent formulation** (§4.4) in which agents carry distinct
   reasoning priors and *private, specialty-scoped* retrieval, so that perspective
   diversity — the resource debate consumes — is preserved rather than averaged away.
2. **A structured debate protocol** (§4.5) that operates on grounded reasons and
   converts disagreement into targeted retrieval.
3. **A consensus formalism** (§4.6) with confidence-weighted aggregation, an
   evidence adjustment term, and a disagreement metric that drives an explicit
   stopping and escalation rule.
4. **A competence-scoped critique rule** (§6.4) which we show is *necessary*: without
   it, agents lacking a prior in the relevant domain vote down correct in-domain
   diagnoses.
5. **A complete, deterministic, dependency-free prototype** (§5) and an evaluation
   protocol for the system as decision support (§6), with negative results reported.

---

## 2. Related work

**Multi-agent debate.** Multiple LLM instances that critique and revise each other's
reasoning improve factuality over single-model inference [[2]](#references), and
iterative self-critique improves output quality within a single model
[[3]](#references). This literature is largely evaluated on general reasoning and
factual QA; MedJar specialises it in three ways — heterogeneous *domain* personas
rather than identical debaters, per-agent retrieval scopes, and an aggregation rule
that weights by competence rather than counting votes.

**Retrieval-augmented generation.** Grounding generation in retrieved documents
reduces hallucination and enables citation [[4]](#references). Hybrid dense/sparse
retrieval with rank-level fusion [[5]](#references) is standard practice. MedJar's
departure is that retrieval is *per-agent and scoped*: global retrieval would return
the same passages to every agent and homogenise the ensemble.

**Clinical LLMs and medical QA.** Benchmarks such as MedQA [[6]](#references),
MedMCQA [[7]](#references), and PubMedQA measure medical knowledge, and
domain-adapted models score highly on them [[8]](#references). High benchmark
accuracy does not establish safety in complex, multi-system cases; our evaluation
protocol (§6.1) therefore treats false reassurance on can't-miss diagnoses as the
primary endpoint rather than accuracy.

**Calibration.** Modern networks are systematically overconfident; post-hoc
temperature and Platt scaling substantially reduce calibration error
[[9]](#references). Because MedJar weights agents by their stated confidence,
calibration is not cosmetic but load-bearing — a point our negative result in §6.2
makes concrete.

**Multidisciplinary review.** The clinical evidence that team review improves
complex-case outcomes motivates the architecture; MedJar makes the reasoning of such
a review explicit, grounded, and replayable.

---

## 3. Problem formulation

**Task.** Given a de-identified case representation $x$, produce a ranked
differential over a hypothesis space $\mathcal{H}$, a calibrated score for each
hypothesis, the evidence for and against it, the investigation that would most
change the ranking, and a *disposition*: either report a converged assessment or
escalate to a clinician with the unresolved question stated.

**Notation.** Table 1 fixes the symbols used throughout.

**Table 1 — Notation.**

| Symbol | Meaning |
|---|---|
| $x$ | Case Context Object (CCO): de-identified, coded case representation |
| $\mathcal{H}$ | shared hypothesis space (union of all agents' differentials) |
| $A_i$ | agent $i$, a triple $\langle$persona, tools, retrieval scope$\rangle$ |
| $p_i(h)$ | likelihood agent $i$ assigns to hypothesis $h$ |
| $c_i$ | agent $i$'s calibrated confidence |
| $w_i(h)$ | specialty weight of agent $i$ on $h$ (soft mixture of experts) |
| $E(h)$ | net grounded evidence for $h$ (grade- and recency-weighted) |
| $S(h)$, $S^*(h)$ | ensemble score, evidence-adjusted score |
| $\bar{D}$ | case-level disagreement (mean over top-$k$ hypotheses) |
| $r$, $R_{\max}$ | debate round index, round budget |
| $\tau_{\text{agree}}$, $\tau_{\text{flag}}$ | convergence and can't-miss thresholds |

**Design requirements.** We hold the system to five requirements, each of which maps
to a mechanism and a measurement:

| Req. | Statement | Mechanism | Measured by |
|---|---|---|---|
| **R1** | No clinical claim without a citation | groundedness gate (§4.3) | % claims entailed |
| **R2** | Conclusions traceable to inputs and evidence | Evidence Ledger (§4.3) | audit replay |
| **R3** | Stated confidence matches empirical accuracy | calibration (§4.6) | ECE, Brier |
| **R4** | Uncertainty and can't-miss findings reach a human | stopping rule (§4.7) | false-reassurance rate |
| **R5** | Control flow predictable and testable | deterministic FSM (§4.7) | replay determinism |

---

## 4. System design

### 4.1 Overview

MedJar is a six-stage pipeline (Figure 1). Data flows downward; control circulates
within the reasoning stage, which is the only stochastic component in deployment.

![Layered system architecture](figures/fig01_architecture.svg)

**Figure 1.** Layered architecture. Stages 0–2 are deterministic preprocessing;
stage 3 hosts the debate; stages 4–5 are deterministic aggregation and reporting.
Escalation returns control to the clinician.

Figure 2 expands the same system into its end-to-end workflow, showing every step,
the trust boundary at which identifiers are removed, and the loop that repeats until
the stopping rule fires.

![End-to-end workflow](figures/fig02_workflow.svg)

**Figure 2.** End-to-end workflow (steps 1–16) across eight lanes. De-identification
occurs in the intake lane; nothing below the horizontal boundary carries a patient
identifier. Agents (lane 5) retrieve privately from the knowledge lane and never
observe one another during proposal. The debate loop (steps 10–12) repeats while
$\bar{D} > \tau_{\text{agree}}$ and $r < R_{\max}$. Both dispositions terminate in
mandatory clinician sign-off.

### 4.2 Intake and the Case Context Object

Heterogeneous inputs are normalised into a single coded representation (Figure 3).
De-identification occurs at the boundary; the reasoning layer never receives direct
identifiers, and raw imaging pixels never leave the enclave. Explicit **negations**
are carried in the CCO so that agents can distinguish *absent* from *not assessed* —
a distinction that materially changes a differential and is routinely lost when notes
are flattened into text.

![Multimodal intake into the CCO](figures/fig07_cco.svg)

**Figure 3.** Six input modalities normalised into the Case Context Object, coded
against ICD-10, SNOMED CT, LOINC and RxNorm.

### 4.3 Knowledge layer and grounding

Retrieval is hybrid (Figure 4): dense vector search for semantic recall, Okapi BM25
for exact clinical terms, drug names and gene symbols, merged by reciprocal rank
fusion

$$\text{RRF}(d) = \sum_{s \in \{\text{dense},\,\text{sparse}\}} \frac{1}{k + \text{rank}_s(d)}, \qquad k \approx 60$$

then re-ranked by a cross-encoder for precision, and boosted by specialty scope and
recency. Every passage carries `{source, section, publish_year, evidence_grade,
specialty_tags}`.

![Retrieval pipeline](figures/fig03_rag_pipeline.svg)

**Figure 4.** Hybrid retrieval, RRF fusion, re-ranking, and the groundedness gate.

**Groundedness gate (R1).** Each claim is tested for entailment against the passage
it cites; claims below threshold are marked ungrounded and **excluded from
aggregation**. Surviving citations are written to the append-only **Evidence
Ledger**, which records the passage, its provenance and grade, the retrieval scores,
the citing agent, and the hypothesis and polarity it was used for. The ledger is what
makes R2 achievable: a report is reproducible from its logged inputs.

### 4.4 The specialist ensemble

Each agent is a triple $\langle$persona, tools, scope$\rangle$. The persona encodes a
specialty-specific prior over $\mathcal{H}$ — operationally, *what this specialist
worries about first*.

**Table 2 — The launch ensemble.**

| Agent | Reasoning prior | Retrieval scope | Characteristic question |
|---|---|---|---|
| Radiologist | morphology → localisation → imaging differential | imaging atlases, appropriateness criteria | *What does the image show, independent of the referral question?* |
| Cardiologist | exclude life-threatening cardiac aetiology first | cardiology guidelines, risk scores, ECG libraries | *Is there a cardiac cause or cardiac consequence we must not miss?* |
| Oncologist | tissue of origin, staging, biomarkers, tempo | staging manuals, oncology guidelines | *Is this neoplastic, and what is the stage-defining evidence?* |
| Generalist | whole-patient coherence; guards against over-specialisation | general, infectious, cardiology | *Does this explain the entire presentation?* |

**Reasoning contract.** Every turn returns a structured object — never free prose —
containing, per hypothesis: likelihood, supporting and refuting claims each bound to
a `citation_id`, and the discriminating next test; plus red flags, calibrated
confidence, and requests. Structure is what makes positions comparable, aggregable
and auditable (Appendix B).

**Shared hypothesis space.** Agents never abstain. After proposal the orchestrator
completes the opinion matrix: an agent with no persona prior for $h$ still registers
a low *cautionary floor*, lifted slightly for can't-miss diagnoses. Floors
participate in $S(h)$ with reduced weight but are **excluded from the disagreement
metric** — absence of an opinion is not dissent. §6.4 shows both halves of this rule
are necessary.

### 4.5 The debate protocol

![Debate protocol as a message sequence](figures/fig04_debate_sequence.svg)

**Figure 5.** The protocol as a message sequence, with labels abridged from the
prototype's CASE-001 transcript.

**Phase 1 — Propose (isolated).** Each agent reads the CCO, retrieves privately, and
emits an independent differential. Isolation is deliberate: it prevents early
anchoring and preserves the diversity later phases consume.

**Phase 2 — Critique (adversarial, anonymised).** Agents see each other's
differentials with authorship withheld, and raise grounded objections of three kinds:
*missing confirmation* (asserted without the confirmatory finding the critic's prior
requires), *overcall* (the critic's prior is materially lower), and *alternative* (the
hypothesis fails to explain the whole patient — reserved to the generalist).

**Critique admissibility.** An overcall critique is admissible **only if the critic
holds a genuine prior for that diagnosis**, and every critique's severity is scaled by
the critic's specialty weight $w_i(h)$. This is not a detail: §6.4 shows that without
it, three agents with no cardiology competence suppressed a correct acute coronary
syndrome diagnosis below the escalation threshold.

**Phase 3 — Rebut.** Agents concede, defend, or revise. Defence strength scales with
the count of grounded supporting citations, so well-evidenced positions resist
rhetorical pressure. Points of contention seed **targeted re-retrieval** — this is
the mechanism by which disagreement does work.

**Phase 4 — Assess.** The orchestrator recomputes $S^*$, $\bar{D}$ and red flags and
applies the stopping rule. At least one critique round always runs
($r_{\min} = 1$): independent impressions are never accepted without
cross-examination, even when they happen to coincide.

### 4.6 Consensus formalism

![Consensus dataflow](figures/fig06_consensus_dataflow.svg)

**Figure 6.** How agent opinions become $S^*(h)$ and $\bar{D}$. Values shown are the
prototype's actual round-0 likelihoods for *primary lung malignancy* in CASE-001.

**Ensemble score.** Confidence- and competence-weighted mean:

$$S(h) = \frac{\sum_i w_i(h)\, c_i\, p_i(h)}{\sum_i w_i(h)\, c_i} \tag{1}$$

$w_i(h)$ is a *soft* mixture-of-experts weight — 1.00 in-domain, 0.58–0.82 for
adjacent domains, 0.45 otherwise, 0.72 for the generalist — not a hard router: every
agent votes on every hypothesis.

**Evidence adjustment.** Net grounded evidence $E(h) \in (-1,1)$ aggregates
supporting minus refuting citations, each weighted by evidence grade, recency
(exponential decay, 8-year half-life) and entailment score:

$$S^*(h) = \sigma\big(\alpha\,\operatorname{logit} S(h) + \beta\, E(h)\big) \tag{2}$$

This separates hypotheses that merely look plausible from those the corpus actually
supports.

**Disagreement.** A confidence-weighted variance, computed over *substantive*
opinions only:

$$\operatorname{Disagree}(h) = \frac{\sum_{i \in \mathcal{S}(h)} w_i(h)\, c_i\,\big(p_i(h) - S(h)\big)^2}{\sum_{i \in \mathcal{S}(h)} w_i(h)\, c_i} \tag{3}$$

where $\mathcal{S}(h)$ is the set of agents holding a genuine prior for $h$, and
$\operatorname{Disagree}(h) := 0$ when $|\mathcal{S}(h)| < 2$. The case-level signal
$\bar{D}$ is the mean of (3) over the top-$k$ hypotheses ranked by $S^*$ ($k=3$).

### 4.7 Orchestration and the stopping rule

The orchestrator is a **deterministic finite-state machine** (Figure 7), not a
free-form model: control flow must be predictable, testable, and auditable (R5). It
allocates turns, anonymises critiques, enforces the reasoning contract, rejects
malformed or ungrounded turns, owns the Evidence Ledger, and enforces compute budgets.

![Orchestrator state machine](figures/fig05_state_machine.svg)

**Figure 7.** States and guards. τ_agree = 0.010, τ_flag = 0.30, R_max = 4, r_min = 1.

**Stopping rule.** The debate halts when any condition holds:

| Condition | Guard | Disposition |
|---|---|---|
| Converged | $\bar{D} \le \tau_{\text{agree}}$ and $r \ge r_{\min}$ | aggregate and report |
| Budget exhausted | $r = R_{\max}$ | **escalate** with open disagreement stated |
| Can't-miss | any $h$ with $h \in \text{RedFlag}$ and $S^*(h) \ge \tau_{\text{flag}}$ | **escalate**, overriding consensus |

The can't-miss override is asymmetric by design: it can force escalation but never
suppress it. Aggregation rewards grounded evidence, not rhetoric, so an eloquent but
unsupported argument cannot win.

### 4.8 The unified report

![Anatomy of the report](figures/fig08_report_anatomy.svg)

**Figure 8.** Report structure. Status, can't-miss panel and disagreement precede the
differential.

The ordering is a safety decision, not a stylistic one: the clinically valuable
content is *what the system is uncertain about*, so uncertainty is placed first.
Points of disagreement are reported, never suppressed — they identify precisely where
clinician judgement is most needed. A worked report appears in Appendix C.

### 4.9 Deployment and trust boundaries

![Deployment topology](figures/fig09_deployment.svg)

**Figure 9.** Three zones. Identifiers and raw pixels remain in the PHI enclave; the
reasoning zone sees only the de-identified CCO; re-identification happens solely at
the point of care, through a restricted token service, and is logged.

---

## 5. Implementation

The prototype implements every layer of §4 with **no third-party dependencies**, and
is fully deterministic so that the debate and consensus mathematics can be verified
independently of a language model's variability.

**Table 3 — Prototype modules** (`prototype/medjar/`).

| Module | Responsibility | Notes |
|---|---|---|
| `schemas.py` | CCO, hypotheses, claims, turns, ledger entries | diagnosis registry with domains; can't-miss set |
| `corpus.py` | 24-passage versioned corpus | paraphrased, evidence-graded, specialty-tagged |
| `retrieval.py` | BM25 + hashed dense index + RRF + re-ranker | swap two methods for a real embedding model |
| `verify.py` | groundedness gate | lexical-coverage entailment surrogate |
| `agents.py` | personas as `DxRule` sets; `RuleBasedEngine`, `LLMEngine` | four agents, competence-scoped critique |
| `consensus.py` | Eqs. (1)–(3), specialty weights, ECE/Brier | |
| `debate.py` | `ChiefOfService` FSM | alignment step, stopping rule |
| `report.py` | report and transcript renderers | |
| `cases.py` | three synthetic cases with reference diagnoses | |

**Reasoning back-ends.** Two interchangeable engines satisfy one interface —
`hypotheses(cco, passages)` and `prior_for(dx)`:

- `RuleBasedEngine` scores hypotheses from persona-specific `DxRule`s (positive
  features, contraindicating features, required confirmation, discriminating test)
  via a logistic form. It is a *stand-in for a language model*, not a claim about
  clinical reasoning; its purpose is reproducibility, so that the debate and
  consensus mathematics can be verified without model variability.
- `LLMEngine` is the production path (`medjar/llm.py`, `medjar/personas.py`). It
  renders the persona and the retrieved passages into a prompt, calls an injected
  adapter, and parses the reasoning contract. Adapters ship for any
  OpenAI-compatible `/chat/completions` endpoint, for Anthropic `/v1/messages`, and
  for local servers (e.g. Ollama) via `base_url` — all over `urllib`, preserving the
  zero-dependency property.

`prior_for` is not incidental: the existence of a prior is what licenses an agent to
raise an *overcall* critique (§4.5). Under the LLM engine, a prior exists if the model
actually reasoned about that diagnosis or if the diagnosis falls in the agent's own
domain, so the competence rule of §6.4b survives the swap.

**Three invariants are enforced in code rather than trusted to the model:**

1. **Citations must be real.** A `citation_id` not among the passages offered in the
   prompt is discarded, so a hallucinated reference cannot enter the Evidence Ledger.
   Surviving citations are additionally required to pass the entailment gate.
2. **Failure is not silence.** A malformed response costs one agent its turn. But a
   *configuration* failure (missing credentials, rejected auth) is raised immediately,
   and if the ensemble produces no substantive hypothesis at all the orchestrator
   refuses to emit a report and escalates: an empty differential must never be
   presented as a negative finding. `run_demo.py` exits non-zero in that case.
3. **Likelihoods are clamped and coerced**, and diagnoses are reconciled against the
   registry so the hypothesis space stays comparable across agents.

**Reproducing the results.**

```bash
cd prototype  && python3 run_demo.py        # writes output/report_*.md, trace.json
                 python3 verify_llm_path.py # exercises the LLM path offline
cd ../figures && python3 make_figures.py    # regenerates all 14 figures
                 python3 check_layout.py    # geometric validation of the figures
```

To run the specialists on a real model:

```bash
OPENAI_API_KEY=…    python3 run_demo.py --engine llm --provider openai --model gpt-4o-mini
ANTHROPIC_API_KEY=… python3 run_demo.py --engine llm --provider anthropic
                    python3 run_demo.py --engine llm --provider ollama --model llama3.1
```

Result figures are computed from `prototype/output/trace.json`, so the paper's
numbers and its plots cannot drift apart.

**Verification of the LLM path.** The reported results use the rule engine, so the
LLM path would otherwise ship unexecuted. `verify_llm_path.py` drives it end to end
with a scripted adapter substituted for the provider: prompt construction, the adapter
boundary, contract parsing (including fenced JSON, leading prose and trailing-comma
repair), citation validation, grounding, debate, consensus and report rendering all
run for real — only the HTTP hop is replaced. It asserts the safety guards explicitly:
a never-offered citation id is dropped and never reaches the ledger; a diagnosis the
model ignored grants no competence to critique; malformed output degrades to an empty
differential rather than aborting; and every reported claim is entailed by its
citation. All 19 checks pass. **No live provider call was made in preparing this
report**, so the adapters are verified structurally, not against a live endpoint.

---

## 6. Evaluation

### 6.1 Protocol

MedJar must be evaluated as decision support, not as a quiz-taker.

**Data.** (i) knowledge probes — MedQA, MedMCQA, PubMedQA; (ii) case-based —
clinicopathological-conference cases with confirmed diagnoses, MIMIC-derived
scenarios; (iii) prospective **silent trial** — read-only alongside real workups,
never influencing care.

**Metrics.** Top-1/top-3 differential hit rate; ECE, Brier, reliability diagrams;
**can't-miss recall and false-reassurance rate (primary safety endpoint)**;
groundedness (% of claims entailed by their citation); blinded specialist ratings of
usefulness; latency, tokens, and rounds-to-converge; and accuracy/calibration parity
across demographic strata.

**Baselines and ablations.** Single agent; majority-vote ensemble; debate without
RAG; debate without calibration; full system.

**What follows is not that study.** §6.2 reports what the prototype actually does on
three synthetic cases — a mechanism check, with $n$ far too small for performance
claims.

### 6.2 Prototype results

**Table 4 — Run summary** (3 synthetic cases, deterministic).

| Metric | Value |
|---|---|
| Top-1 hit rate | 3/3 |
| Top-3 hit rate | 3/3 |
| Claims checked / passing groundedness gate | 130 / 130 (100%) |
| Evidence Ledger citations | 91 |
| Expected calibration error (ECE) | **0.243** |
| Brier score | 0.077 |

**Table 5 — Per-case behaviour.**

| Case | Reference diagnosis | Leading $S^*$ | Rounds | $\bar{D}$ trajectory | Disposition |
|---|---|---|---|---|---|
| CASE-001 | Primary lung malignancy | 0.79 ✓ | 4 | 0.0384 → 0.0345 (plateau) → 0.0357 | **escalated** — can't-miss |
| CASE-002 | Benign pulmonary granuloma | 0.59 ✓ | 2 | 0.0112 → 0.0104 → 0.0093 | **converged** |
| CASE-003 | Acute coronary syndrome | 0.55 ✓ | 1 | 0.0037 → 0.0034 | **escalated** — can't-miss |

The three cases exercise all three stopping paths. Figure 10 shows the trajectories.

![Disagreement trajectories](figures/fig10_convergence.svg)

**Figure 10.** CASE-002 falls below $\tau_{\text{agree}}$ and converges. CASE-001
plateaus above it — the specialists cannot reconcile, so the case escalates with its
open disagreement stated. CASE-003 agrees almost immediately yet still escalates,
because a can't-miss diagnosis overrides consensus. Real run data.

**Cross-specialty divergence.** Figure 11 shows why competence weighting matters. On
CASE-001's leading hypothesis the agents split 0.83 / 0.17 / 0.90 / 0.79
(radiologist / cardiologist / oncologist / generalist). The cardiologist's 0.17 is a
cautionary floor, not a considered dissent; specialty weighting prevents it from
dominating $S^*$, and it is excluded from $\bar{D}$ entirely.

![Cross-specialty divergence](figures/fig11_divergence.svg)

**Figure 11.** Per-agent likelihoods for CASE-001's top hypotheses, with $S^*(h)$
marked. Real run data.

**Evidence adjustment.** Figure 12 shows the ranked differential with $S$ (before
adjustment) marked against $S^*$. The gap is the contribution of grounded evidence:
*primary lung malignancy* gains ($E=+0.72$, $S\,0.72 \rightarrow S^*\,0.79$) while
*malignant pericardial effusion* loses ($E=-0.34$, $0.37 \rightarrow 0.33$) because
the retrieved guidance states that cytological confirmation is required before that
classification — the corpus actively argues against asserting it.

![Ranked differential](figures/fig12_differential.svg)

**Figure 12.** CASE-001 differential. Real run data.

**Calibration: a negative result.** ECE is 0.243 over 19 hypothesis-level
predictions (Figure 13) — poor. This is expected and worth stating plainly: the
prototype's temperatures and the coefficients $\alpha,\beta$ are hand-set, not fitted
on held-out data, so $S^*$ carries no calibration guarantee. Since Eq. (1) weights
agents *by* their confidence, R3 is currently unmet, and fitting the calibration layer
is the first prerequisite for any performance claim.

![Reliability diagram](figures/fig13_calibration.svg)

**Figure 13.** Reliability diagram with bin counts, and the run summary. Real run
data; small-sample, not a validation result.

### 6.3 Planned ablation

Figure 14 states the *expected* direction of effect for the ablation in §6.1. These
are hypotheses to be tested, not measurements, and are labelled as such.

![Planned ablation](figures/fig14_ablation.svg)

**Figure 14.** Expected ablation effects. Illustrative.

### 6.4 Failure modes discovered during implementation

Building the system exposed four failure modes that the architecture as specified did
not prevent. We record them because three are, we believe, general to multi-agent
debate in high-stakes domains — and one is a direct safety failure.

**(a) Hypotheses floating on their prior.** A diagnosis whose supporting features
were *entirely absent* from the case still scored ≈0.33, because the persona's prior
intercept dominated when no feature matched. On CASE-003 this put *primary lung
malignancy* at the top of the differential for a patient with no nodule and no weight
loss. **Fix:** a diagnosis with zero matched positive features is penalised out of
contention; a hypothesis must earn its place from case evidence, not from its prior.

**(b) Incompetent critique → false reassurance.** *The most serious finding.* Agents
holding no prior for a diagnosis were nonetheless permitted to raise *overcall*
critiques using their own cautionary floor as the comparison. On CASE-003, three
agents with no cardiology competence each critiqued the cardiologist's correct
*acute coronary syndrome* position; the cumulative penalty drove $S^*$ from 0.84 to
0.27, below $\tau_{\text{flag}}$, and the case **converged instead of escalating** —
manufacturing precisely the false reassurance on a can't-miss diagnosis that the
system exists to prevent. **Fix:** overcall critiques are admissible only from agents
holding a genuine prior in the diagnosis's domain, and all critique severities scale
with $w_i(h)$. An agent's ignorance is not evidence.

**(c) Unbounded reinforcement → echo chamber.** Uncontested, well-cited hypotheses
were reinforced every round without limit, so confident positions inflated
monotonically and apparent disagreement *drifted upward* across rounds — the
opposite of the intended dynamic. **Fix:** reinforcement is capped at the level the
agent's own prior supports. Consolidation may restore a position; it may not inflate
it.

**(d) Ignorance floors counted as dissent.** Including out-of-domain floors in Eq. (3)
created disagreement that no amount of debate could resolve, since a floor never
moves: benign CASE-002 exhausted its round budget instead of converging. **Fix:**
restrict Eq. (3) to substantive opinions, as formalised in §4.6.

Failure (b) is the one we would emphasise to anyone building a debate-based clinical
system: **debate is only safe if the right to object is tied to competence.** An
unweighted debate among heterogeneous agents is not merely noisy — it can be
systematically more dangerous than a single competent agent, because it provides a
mechanism for confident non-experts to overrule a correct specialist. All four fixes
are present in the code and reflected in the reported results.

---

## 7. Safety, ethics, and regulatory posture

**MedJar is assistive.** It produces recommendations for a licensed clinician who
remains the decision-maker and is accountable for care. It does not autonomously
diagnose or treat.

- **Human gate (R4).** Mandatory sign-off before any recommendation informs care.
  Uncertainty and can't-miss findings escalate rather than closing a case.
- **Privacy.** De-identification at intake; PHI enclave; encryption in transit and at
  rest; per-access audit logging; no training on patient data absent explicit
  governance and consent.
- **Regulatory.** Decision support that drives diagnosis is likely **Software as a
  Medical Device**. The transparency of the evidence and the debate transcript is
  intended to support the "clinician can independently review the basis" pathway
  [[10]](#references), but any deployment requires a formal regulatory strategy:
  clinical validation, a predetermined change-control plan for model updates, and
  post-market surveillance under Good Machine Learning Practice.
- **Equity.** Corpus and evaluation stratified by demographic subgroup, with
  calibration checked per stratum and monitored continuously; guardrails against
  propagating inequities encoded in historical notes or guidelines.
- **Accountability.** Every report is reproducible from its logged inputs, retrieved
  evidence, and transcript.

---

## 8. Limitations and threats to validity

**Evaluation.** Three synthetic cases, authored by us, with a deterministic
rule-based reasoner. This validates *mechanism*, not diagnostic performance; the
100% top-1 rate carries no clinical weight. No LLM was in the loop, no real patient
data was used, and no clinician reviewed the outputs.

**Calibration unmet.** ECE 0.243 (§6.2). Confidence-weighted aggregation is only
sound once $c_i$ is fitted; until then $S^*$ should be read ordinally, not as a
probability.

**Surrogates.** The dense index is a hashed bag-of-words rather than a learned
medical embedding; the groundedness verifier is lexical coverage rather than a
trained NLI model; the cross-encoder is a term-overlap heuristic. Each is an
interface-compatible placeholder, and each would change absolute numbers.

**Polarity classification is crude.** Support-versus-refute is decided by cue phrases
in the retrieved passage. This misfires: in CASE-003 the correct ACS hypothesis
received $E = -0.41$ because passages *defining* the diagnostic criteria contain
cautionary language ("not specific for", "lowers the probability"). The hypothesis
still led on $S$, but the adjustment moved in the wrong direction — a clear target
for a trained stance classifier.

**Correlated agent failure.** If deployed agents share a base model they may share
blind spots, weakening the diversity the protocol depends on; heterogeneous models
and a devil's-advocate agent are mitigations we have not evaluated.

**Corpus.** 24 paraphrased passages. Real deployment depends on licensed, curated,
versioned guideline text, and the system inherits every gap and staleness in it.

**Automation bias.** Leading with uncertainty is intended to counter over-trust, but
whether it does so is an empirical question about clinicians, not about software, and
requires a human-factors study.

**Compute.** Multi-round, multi-agent, multi-retrieval inference is expensive; the
round budget bounds it, and a single-pass triage mode would be needed for
time-critical settings.

---

## 9. Conclusion

MedJar recasts the multidisciplinary case conference as a computational protocol:
specialist agents reason independently, ground every claim in citable evidence,
debate their differences under rules that tie the right to object to competence, and
converge on a calibrated, auditable assessment — escalating to a human precisely when
they should. The prototype demonstrates that the full pipeline runs end to end,
deterministically, and that the disagreement metric functions as a usable control
signal across all three stopping paths.

The implementation also produced the report's most transferable result, and it is a
cautionary one. Naive multi-agent debate is not automatically safer than a single
model: we observed a correct can't-miss diagnosis suppressed below the escalation
threshold by agents with no competence in the relevant domain. **Aggregation rules,
not agent count, determine whether an ensemble is safe.** Calibration is the next
prerequisite; a prospective silent trial is the only way to learn whether any of this
helps a clinician.

---

## References

1. National Academies of Sciences, Engineering, and Medicine. *Improving Diagnosis in Health Care.* National Academies Press, 2015.
2. Du, Y., Li, S., Torralba, A., Tenenbaum, J. B., Mordatch, I. "Improving Factuality and Reasoning in Language Models through Multiagent Debate." 2023.
3. Madaan, A., et al. "Self-Refine: Iterative Refinement with Self-Feedback." *NeurIPS*, 2023.
4. Lewis, P., et al. "Retrieval-Augmented Generation for Knowledge-Intensive NLP Tasks." *NeurIPS*, 2020.
5. Cormack, G. V., Clarke, C. L. A., Buettcher, S. "Reciprocal Rank Fusion Outperforms Condorcet and Individual Rank Learning Methods." *SIGIR*, 2009.
6. Jin, D., et al. "What Disease Does This Patient Have? A Large-Scale Open Domain Question Answering Dataset from Medical Exams." *Applied Sciences*, 2021.
7. Pal, A., Umapathi, L. K., Sankarasubbu, M. "MedMCQA: A Large-Scale Multi-Subject Multi-Choice Dataset for Medical Domain Question Answering." *CHIL*, 2022.
8. Singhal, K., et al. "Large Language Models Encode Clinical Knowledge." *Nature*, 2023.
9. Guo, C., Pleiss, G., Sun, Y., Weinberger, K. Q. "On Calibration of Modern Neural Networks." *ICML*, 2017.
10. U.S. Food and Drug Administration. *Clinical Decision Support Software — Guidance for Industry and FDA Staff*, and *Good Machine Learning Practice for Medical Device Development: Guiding Principles*.

> Citations are provided at the level of identification. Verify against primary
> sources before any formal publication or clinical claim.

---

## Appendix A — Algorithms

**Algorithm 1 — Debate protocol (orchestrator).**

```
input : CCO x, agents A₁..Aₙ, thresholds τ_agree, τ_flag, budget R_max, r_min
output: consensus items, disposition, evidence ledger

ledger ← ∅
for each Aᵢ:  Tᵢ ← Aᵢ.propose(x)                 # isolated; private retrieval
align(T)                                          # every agent scores every h ∈ H
items ← aggregate(T, ledger);  D̄ ← disagreement(items)

r ← 1
while r ≤ R_max:
    C ← ⋃ᵢ Aᵢ.critique(x, T)                      # anonymised, competence-scoped
    for each Aᵢ: Tᵢ ← Aᵢ.rebut(x, C)              # concede / defend / revise
    align(T)                                       # re-complete the matrix
    items ← aggregate(T, ledger);  D̄ ← disagreement(items)
    if D̄ ≤ τ_agree and r ≥ r_min:
        status ← CONVERGED;  break
    r ← r + 1
if status ≠ CONVERGED: status ← ESCALATED  (reason: budget exhausted)

# can't-miss override — can force escalation, never suppress it
if ∃ h ∈ RedFlag with S*(h) ≥ τ_flag:
    status ← ESCALATED  (reason: can't-miss diagnosis h)

return items, status, ledger
```

**Algorithm 2 — Aggregation and disagreement.**

```
input : turns T, ledger L
for each h ∈ H = ⋃ᵢ dom(Tᵢ):
    d ← domain(h)
    S(h)  ← Σᵢ wᵢ(d)·cᵢ·pᵢ(h)  /  Σᵢ wᵢ(d)·cᵢ                       # Eq. 1
    E(h)  ← tanh( [Σ_support g·ρ·e − Σ_refute g·ρ·e] / 2.2 )         # grade g,
                                                                      # recency ρ,
                                                                      # entailment e
    S*(h) ← σ( α·logit S(h) + β·E(h) )                                # Eq. 2
    𝒮(h)  ← { i : Aᵢ holds a genuine prior for h }                    # exclude floors
    if |𝒮(h)| ≥ 2:
        Disagree(h) ← Σ_{i∈𝒮} wᵢcᵢ(pᵢ(h) − S(h))² / Σ_{i∈𝒮} wᵢcᵢ     # Eq. 3
    else:
        Disagree(h) ← 0
D̄ ← mean of Disagree(h) over the top-k hypotheses by S*
```

**Algorithm 3 — Grounded evidence attachment.**

```
input : hypothesis h, agent scope, query seed q
hits ← retrieve(q, scope, top_k)                    # dense ⊕ sparse → RRF → rerank
for each hit:
    claim ← form_claim(hit.passage)
    claim.entailment ← verify(claim, hit.passage)
    if claim.entailment < threshold:  discard        # groundedness gate (R1)
    attach claim to h as support or refute
    append provenance record to ledger              # R2
```

---

## Appendix B — Schemas

**Reasoning contract** (returned by every agent turn):

```json
{
  "differential": [
    {"dx": "…", "icd10": "…", "likelihood": 0.0,
     "supporting_evidence": [{"claim": "…", "citation_id": "…"}],
     "refuting_evidence":   [{"claim": "…", "citation_id": "…"}],
     "discriminating_test": "…"}
  ],
  "red_flags": ["…"],
  "confidence": 0.0,
  "requests": ["retrieve:…", "ask-human:…"]
}
```

**Case Context Object:**

```json
{
  "case_id": "uuid", "age": 0, "sex": "…",
  "presentation": "de-identified narrative",
  "findings": ["canonical feature keys"],
  "absent":   ["explicitly negated features"],
  "vitals": {}, "labs": [{"loinc": "…", "value": 0, "unit": "…", "flag": "H|L|N"}],
  "imaging": [{"modality": "…", "finding": "…", "impression": "…"}],
  "pathology": [], "genomics": [], "ecg_features": {}
}
```

**Evidence Ledger entry:**

```json
{
  "citation_id": "RAD-001#001", "case_id": "…", "pid": "RAD-001",
  "source": "…", "section": "…", "publish_year": 2023, "evidence_grade": "I-A",
  "passage": "verbatim retrieved text",
  "used_by_agent": "Radiologist", "hypothesis": "…", "polarity": "support",
  "scores": {"dense": 0.0, "sparse": 0.0, "rrf": 0.0, "rerank": 0.0}
}
```

---

## Appendix C — Worked case

**CASE-001** (synthetic). 58-year-old: progressive dyspnoea over three months,
7 kg unintentional weight loss, 2.4 cm spiculated right-upper-lobe nodule, small
pericardial effusion, mildly elevated and *stable* high-sensitivity troponin, sinus
tachycardia without dynamic ECG change, no chest pain.

**Round 0 — independent proposals.**

| Agent | Leading position | Reasoning prior at work |
|---|---|---|
| Radiologist | primary lung malignancy 0.83 | spiculated margin + upper lobe + weight loss |
| Oncologist | primary lung malignancy 0.90 | constitutional symptoms + smoking history |
| Cardiologist | demand ischemia 0.79 | troponin elevated **with** stable ECG and no chest pain |
| Generalist | primary lung malignancy 0.79 | whole-patient coherence |

Note the cardiologist's reasoning: ACS scored 0.03 and was dropped, because
*no chest pain* and *static ECG* are contraindicating features. The troponin is
attributed to supply–demand mismatch — the clinically correct reading, reached
because the persona encodes it.

**Rounds 1–4 — critique and rebuttal.** The cardiologist challenges the oncologist's
malignant-effusion staging as unconfirmed (no cytology); the oncologist and
radiologist exchange overcall critiques on nodule specificity. Targeted re-retrieval
returns the guidance that cytological confirmation is required for the M1a
classification, which is recorded as **refuting** evidence for that hypothesis
($E = -0.34$).

**Outcome.** $\bar{D}$ falls 0.0384 → 0.0345 and then plateaus: the specialists
narrow but do not reconcile. Disposition **ESCALATED**, reason *can't-miss diagnosis
'primary lung malignancy' at $S^* = 0.79 \ge \tau_{\text{flag}}$*. The report states
the leading impression, the two red-flag hypotheses, the residual disagreement on
*demand ischemia* (variance 0.085), and the discriminating tests: FDG PET-CT then
tissue biopsy, pericardial fluid cytology, and a serial troponin trend.

Full artefacts: [`prototype/output/report_CASE-001.md`](prototype/output/report_CASE-001.md)
and [`prototype/output/transcript_CASE-001.md`](prototype/output/transcript_CASE-001.md).

---

*MedJar — research prototype. Decision support only; not a medical device, and not a
substitute for professional medical judgement.*

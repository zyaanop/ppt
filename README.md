# MedJar — Presentation Suite

A multi-agent consensus system for complex medical diagnosis: specialist LLM agents
(Radiologist, Cardiologist, Oncologist, …) **debate** a patient's case, ground their
reasoning in medical literature via **RAG**, and converge on a single, provenance-linked
**diagnostic report**. Assistive, human-in-the-loop — **not** an autonomous diagnostician.

## Deliverables

| File | What it is | How to open |
|------|-----------|-------------|
| **`presentation.html`** | Fully self-contained **animated deck** (18 slides). No external dependencies, works offline. | Double-click → opens in any browser. |
| **`MedJar_Research.md`** | **Seminar-grade research report** — architecture, agent ensemble, RAG pipeline, consensus math, orchestration, evaluation, safety/ethics, limitations, appendices. | Any Markdown viewer / GitHub. |
| **`MedJar.pptx`** | **PowerPoint** version of the deck (18 slides), generated from scratch. | PowerPoint / Keynote / Google Slides / LibreOffice. |
| **`build_pptx.py`** | The generator that builds `MedJar.pptx` using only Python's standard library. | `python3 build_pptx.py` |

## Using the animated HTML deck

- **Navigate:** `→` / `Space` next · `←` back · `Home` / `End` jump · click right/left of screen.
- **Auto-play:** click **▶ Auto** (or press `A`) — advances fragments and slides automatically.
- **Fullscreen:** press `F`.
- **Jump:** click the dots at the bottom; deep-links via `#s7` in the URL.
- Content reveals **fragment-by-fragment** with animated transitions and an ambient background.

## Rebuilding the PPTX

```bash
python3 build_pptx.py     # writes MedJar.pptx (no pip install needed)
```

## Deck outline (18 slides)

1. Title  2. The Problem  3. Core Insight  4. Architecture (6 layers)
5. Agent Ensemble  6. Reasoning Contract  7. RAG Pipeline  8. Debate Protocol
9. Consensus Mathematics  10. Orchestrator  11. State Machine  12. Multimodal Intake
13. Diagnostic Report  14. Worked Case  15. Evaluation  16. Safety / Ethics / Regulatory
17. Limitations  18. Roadmap & Takeaway

---
*MedJar is decision-support. It does not autonomously diagnose or treat and is not a
substitute for professional medical judgment.*

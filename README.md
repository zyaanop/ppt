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

## Deck outline (23 slides, figure-driven)

**Title** · **I — System:** motivation, why single-model is insufficient, contributions,
architecture figure, the Case Context Object · **II — Method:** specialist agents,
RAG pipeline figure, debate-protocol figure, consensus formalism (Eqs. 1–3),
disagreement & stopping rule, orchestration state machine · **III — Evaluation:**
experimental protocol, ablation bar chart, calibration reliability diagram, disagreement-
convergence plot, worked case · **Discussion:** safety & limitations · **Conclusion** · **References**

The deck uses an austere academic style — serif display type, a single scholarly-crimson
accent, engineered SVG diagrams, and real (clearly labelled *illustrative*) charts — with no
decorative gradients, glow, emoji, or badges. Section dividers separate the three parts.

---
*MedJar is decision-support. It does not autonomously diagnose or treat and is not a
substitute for professional medical judgment.*

#!/usr/bin/env python3
"""
make_figures.py — generate the complete MedJar figure set as vector SVG.

Structural figures (1-9) are drawn from the system specification.
Result figures (10-14) are computed from real prototype output, read from
../prototype/output/trace.json, so the paper's numbers and its plots cannot
drift apart. Run the prototype first:

    cd ../prototype && python3 run_demo.py
    cd ../figures  && python3 make_figures.py
"""
from __future__ import annotations

import json
import os
from typing import Dict, List, Optional, Sequence, Tuple

from svgkit import (
    ACCENT, FAINT, GREEN, GREY, INK, INK2, INK3, MONO, OCHRE, PAPER, PAPER2,
    RULE, SANS, SERIF, SLATE, Axes, SVG,
)

HERE = os.path.dirname(os.path.abspath(__file__))
TRACE = os.path.join(HERE, "..", "prototype", "output", "trace.json")
OUT = HERE

CASE_COLORS = {"CASE-001": ACCENT, "CASE-002": GREEN, "CASE-003": SLATE}
AGENT_COLORS = {"Radiologist": SLATE, "Cardiologist": ACCENT,
                "Oncologist": OCHRE, "Generalist": GREY}


def load_trace() -> Optional[dict]:
    if not os.path.exists(TRACE):
        return None
    with open(TRACE, "r", encoding="utf-8") as f:
        return json.load(f)


# ==========================================================================
# Fig. 1 — layered system architecture
# ==========================================================================
def fig01_architecture() -> SVG:
    s = SVG(940, 660)
    layers = [
        ("0", "Intake", "De-identification · normalisation · coding", PAPER2, INK),
        ("1", "Representation", "Multimodal encoders → Case Context Object", PAPER2, INK),
        ("2", "Knowledge (RAG)", "Hybrid retrieval · per-specialty scopes", PAPER2, INK),
        ("3", "Reasoning", "Specialist agents ⟷ debate loop", "#F3E4E6", ACCENT),
        ("4", "Consensus & calibration", "Eqs. (1)–(3) · stopping rule · escalation gate", PAPER2, INK),
        ("5", "Reporting", "Ranked differential · provenance · audit trail", PAPER2, INK),
    ]
    x, w, h, gap = 60, 520, 74, 22
    y = 34
    for n, title, sub, fill, stroke in layers:
        s.rect(x, y, w, h, fill=fill, stroke=stroke, sw=1.5, rx=5)
        s.circle(x + 26, y + h / 2, 13, fill=stroke)
        s.text(x + 26, y + h / 2 + 4.2, n, size=13, anchor="middle", fill="#FFFFFF",
               weight="bold", family=MONO)
        s.text(x + 52, y + h / 2 - 3, title, size=15, fill=INK, weight="bold")
        s.text(x + 52, y + h / 2 + 15, sub, size=11, fill=INK3)
        if y + h + gap < 34 + len(layers) * (h + gap):
            s.arrow(x + w / 2, y + h, x + w / 2, y + h + gap - 2, color="ink3")
        y += h + gap

    # side annotations
    notes = [
        (34 + h / 2, "PHI never leaves the enclave", FAINT),
        (34 + (h + gap) * 2 + h / 2, "versioned, evidence-graded corpus", FAINT),
        (34 + (h + gap) * 3 + h / 2, "the only stochastic component", ACCENT),
        (34 + (h + gap) * 4 + h / 2, "deterministic, testable", FAINT),
    ]
    for ny, txt, col in notes:
        s.line(x + w + 8, ny, x + w + 26, ny, stroke=col, sw=1.1, dash="3 3")
        s.text(x + w + 32, ny + 3.6, txt, size=10.5, fill=col)

    # feedback: escalation returns to the clinician, routed clear of the stack
    esc_x = x - 30
    s.path(f"M{x:.1f},{34 + (h + gap) * 4 + h / 2:.1f} "
           f"L{esc_x:.1f},{34 + (h + gap) * 4 + h / 2:.1f} "
           f"L{esc_x:.1f},{34 + h / 2:.1f} L{x - 2:.1f},{34 + h / 2:.1f}",
           stroke=ACCENT, sw=1.4, dash="5 4", marker="accent")
    s.vtext(esc_x - 9, 330, "escalation to clinician", size=10, fill=ACCENT)
    return s


# ==========================================================================
# Fig. 2 — end-to-end workflow (swimlane)
# ==========================================================================
def fig02_workflow() -> SVG:
    W, H = 1400, 890
    s = SVG(W, H)
    LX, LW = 18, 1364          # lane x, lane width
    LABW = 116                 # lane label column
    CX0 = LX + LABW + 16       # content left edge
    lanes = [
        "Source systems", "Intake", "Representation", "Knowledge & retrieval",
        "Specialist agents", "Orchestrator", "Consensus", "Output & human review",
    ]
    LH = 104
    ys: Dict[str, float] = {}
    y = 22
    for name in lanes:
        s.lane(LX, y, LW, LH, name, label_w=LABW)
        ys[name] = y
        y += LH

    def mid(lane: str) -> float:
        return ys[lane] + LH / 2

    def bx(lane: str, x: float, w: float, num: str, title: str,
           sub: Optional[str] = None, fill: str = PAPER2, stroke: str = INK,
           h: float = 58) -> Tuple[float, float, float, float]:
        yy = ys[lane] + (LH - h) / 2
        if num:
            s.numbox(x, yy, w, h, num, title, sub, fill=fill, stroke=stroke)
        else:
            s.box(x, yy, w, h, title, sub, fill=fill, stroke=stroke,
                  title_size=12.5, sub_size=10.2)
        return (x, yy, w, h)

    # ---- lane 1: sources ----
    srcs = [("EHR / FHIR", "vitals · labs · meds"), ("Imaging / PACS", "DICOM series"),
            ("Laboratory", "LOINC-coded results"), ("Notes & reports", "H&P · discharge")]
    sw_, sgap = 236, 24
    sx = CX0
    src_centres: List[float] = []
    for t, sub in srcs:
        bx("Source systems", sx, sw_, "", t, sub)
        src_centres.append(sx + sw_ / 2)
        sx += sw_ + sgap

    # ---- lane 2: intake ----
    a = bx("Intake", CX0, 300, "1", "Ingest & normalise",
           "schema mapping, unit conversion, ontology coding")
    b = bx("Intake", CX0 + 330, 300, "2", "De-identify",
           "Safe Harbor / expert determination")
    tok = bx("Intake", CX0 + 700, 250, "", "Token map",
             "restricted re-identification service", fill="#FBF3F4", stroke=ACCENT)
    # trust boundary: de-identification happens in the Intake lane, so the
    # boundary is horizontal — everything below it is de-identified.
    tby = ys["Representation"]
    s.line(LX, tby, LX + LW, tby, stroke=ACCENT, sw=1.8, dash="7 5")
    s.rect(LX + LW - 372, tby - 11, 366, 22, fill="#FBF3F4", stroke=ACCENT,
           sw=1.0, rx=3)
    s.text(LX + LW - 189, tby + 4, "PHI TRUST BOUNDARY — NO IDENTIFIER CROSSES",
           size=9.5, anchor="middle", fill=ACCENT, weight="bold", spacing="0.06em")

    for cxp in src_centres:
        s.arrow(cxp, ys["Source systems"] + LH - 23, cxp,
                ys["Intake"] + (LH - 58) / 2 - 2, color="faint", sw=1.1)
    s.arrow(a[0] + a[2], mid("Intake"), b[0], mid("Intake"), color="ink3")
    s.arrow(b[0] + b[2], mid("Intake") - 10, tok[0], mid("Intake") - 10,
            color="accent", dash="4 3")

    # ---- lane 3: representation ----
    c = bx("Representation", CX0, 290, "3", "Encode modalities",
           "vision findings, note entities, waveform features")
    d = bx("Representation", CX0 + 320, 320, "4", "Case Context Object",
           "single shared, coded case representation")
    s.box(CX0 + 672, ys["Representation"] + 26, 278, 52, "Coded vocabularies",
          "ICD-10 · SNOMED CT · LOINC · RxNorm", fill="#FFFFFF", stroke=RULE,
          title_size=11.5, sub_size=10)
    s.arrow(b[0] + b[2] / 2, ys["Intake"] + LH - 23, c[0] + 60,
            ys["Representation"] + (LH - 58) / 2 - 2, color="ink3")
    s.arrow(c[0] + c[2], mid("Representation"), d[0], mid("Representation"), color="ink3")

    # ---- lane 4: knowledge ----
    e = bx("Knowledge & retrieval", CX0, 300, "5", "Corpus index",
           "dense vectors + BM25, versioned & graded")
    f = bx("Knowledge & retrieval", CX0 + 330, 270, "6", "Fuse & re-rank",
           "RRF then cross-encoder")
    g = bx("Knowledge & retrieval", CX0 + 630, 250, "7", "Groundedness gate",
           "claim must be entailed")
    led = bx("Knowledge & retrieval", CX0 + 910, 240, "", "Evidence Ledger",
             "append-only provenance", fill="#F2F6F3", stroke=GREEN)
    s.arrow(e[0] + e[2], mid("Knowledge & retrieval"), f[0],
            mid("Knowledge & retrieval"), color="ink3")
    s.arrow(f[0] + f[2], mid("Knowledge & retrieval"), g[0],
            mid("Knowledge & retrieval"), color="ink3")
    s.arrow(g[0] + g[2], mid("Knowledge & retrieval"), led[0],
            mid("Knowledge & retrieval"), color="green")

    # ---- lane 5: agents ----
    s.text(CX0, ys["Specialist agents"] + 17, "8 · Independent proposal — agents "
           "retrieve privately and do not see one another", size=10.5, fill=ACCENT)
    agents = ["Radiologist", "Cardiologist", "Oncologist", "Generalist"]
    aw, agap = 232, 24
    ax = CX0
    a_centres: List[float] = []
    for nm in agents:
        yy = ys["Specialist agents"] + 30
        s.box(ax, yy, aw, 52, nm, "persona · scoped RAG", fill=PAPER2, stroke=INK,
              title_size=12.5, sub_size=10, accent_bar=AGENT_COLORS[nm])
        a_centres.append(ax + aw / 2)
        ax += aw + agap

    # CCO feeds agents; agents query retrieval (bidirectional)
    # CCO → agents: drop into the empty band below the representation boxes,
    # then run down the left margin, clearing every retrieval box
    margin_x = LX + LABW + 2
    agent_row_y = ys["Specialist agents"] + 56
    band_y = ys["Representation"] + LH - 14
    s.path(f"M{d[0] + d[2] / 2:.1f},{d[1] + d[3]:.1f} "
           f"L{d[0] + d[2] / 2:.1f},{band_y:.1f} L{margin_x:.1f},{band_y:.1f} "
           f"L{margin_x:.1f},{agent_row_y:.1f} L{CX0 - 2:.1f},{agent_row_y:.1f}",
           stroke=INK3, sw=1.4, marker="ink3")
    s.add(f'<text x="{margin_x - 6:.1f}" y="{ys["Knowledge & retrieval"] + 52:.1f}" '
          f'font-family="{SANS}" font-size="9.5" fill="{INK3}" text-anchor="middle" '
          f'transform="rotate(-90 {margin_x - 6:.1f} '
          f'{ys["Knowledge & retrieval"] + 52:.1f})">CCO</text>')
    s.arrow(a_centres[1], ys["Specialist agents"] + 30 - 2,
            a_centres[1], ys["Knowledge & retrieval"] + LH - 24,
            color="slate", sw=1.2, dash="4 3")
    s.arrow(a_centres[2] + 40, ys["Knowledge & retrieval"] + LH - 24,
            a_centres[2] + 40, ys["Specialist agents"] + 28, color="slate", sw=1.2)
    s.text(a_centres[1] + 8, ys["Specialist agents"] + 6, "query", size=9.5, fill=SLATE)
    s.text(a_centres[2] + 48, ys["Specialist agents"] + 6, "passages", size=9.5, fill=SLATE)

    # ---- lane 6: orchestrator ----
    o1 = bx("Orchestrator", CX0, 252, "9", "Align hypotheses",
            "every agent scores every dx")
    o2 = bx("Orchestrator", CX0 + 276, 242, "10", "Critique",
            "anonymised, grounded")
    o3 = bx("Orchestrator", CX0 + 542, 242, "11", "Rebut",
            "revise + re-retrieve")
    o4 = bx("Orchestrator", CX0 + 808, 262, "12", "Assess",
            "compute D̄, detect red flags", fill="#F3E4E6", stroke=ACCENT)
    for u, v in ((o1, o2), (o2, o3), (o3, o4)):
        s.arrow(u[0] + u[2], mid("Orchestrator"), v[0], mid("Orchestrator"), color="ink3")
    for cxp in a_centres:
        s.arrow(cxp, ys["Specialist agents"] + LH - 22, cxp,
                ys["Orchestrator"] + (LH - 58) / 2 - 2, color="faint", sw=1.1)
    # debate loop back — drops from the left of Assess so it clears the
    # hand-off into the consensus lane on the right
    loop_y = ys["Orchestrator"] + LH - 9
    loop_x = o4[0] + 50
    s.path(f"M{loop_x:.1f},{o4[1] + o4[3]:.1f} L{loop_x:.1f},{loop_y:.1f} "
           f"L{o2[0] + o2[2] / 2:.1f},{loop_y:.1f} "
           f"L{o2[0] + o2[2] / 2:.1f},{o2[1] + o2[3]:.1f}",
           stroke=ACCENT, sw=1.5, marker="accent")
    s.text((o2[0] + loop_x) / 2 + 40, loop_y - 5,
           "loop while  D̄ > τ_agree  and  r < R_max", size=10.5, anchor="middle",
           fill=ACCENT)

    # ---- lane 7: consensus ----
    q1 = bx("Consensus", CX0, 224, "13", "Eq. 1 — S(h)", "confidence-weighted score")
    q2 = bx("Consensus", CX0 + 248, 214, "", "Eq. 2 — S*(h)", "evidence-adjusted")
    q3 = bx("Consensus", CX0 + 486, 200, "", "Eq. 3 — D̄", "weighted variance")
    q4 = bx("Consensus", CX0 + 710, 268, "14", "Stopping rule",
            "converge | bound | red-flag", fill="#F3E4E6", stroke=ACCENT)
    for u, v in ((q1, q2), (q2, q3), (q3, q4)):
        s.arrow(u[0] + u[2], mid("Consensus"), v[0], mid("Consensus"), color="ink3")
    # Eq. 1–3 are computed from the aligned agent turns; Assess consumes D̄ and
    # hands control to the stopping rule.
    s.arrow(o1[0] + o1[2] / 2, o1[1] + o1[3], q1[0] + q1[2] / 2, q1[1],
            color="faint", sw=1.2)
    s.arrow(o4[0] + o4[2] - 40, o4[1] + o4[3], q4[0] + q4[2] - 40, q4[1],
            color="ink3")

    # ---- lane 8: output ----
    r1 = bx("Output & human review", CX0, 268, "15", "Diagnostic report",
            "differential · evidence · disagreement")
    r2 = bx("Output & human review", CX0 + 296, 300, "16", "Clinician review",
            "mandatory sign-off before any action", fill="#F2F6F3", stroke=GREEN)
    r3 = bx("Output & human review", CX0 + 700, 330, "", "ESCALATE",
            "open disagreement or can't-miss diagnosis → urgent human review",
            fill="#F3E4E6", stroke=ACCENT)
    # branch out of the stopping rule, routed through the empty band at the top
    # of the output lane so neither arrow crosses a box
    band_a = ys["Output & human review"] + 7
    band_b = ys["Output & human review"] + 15
    s.path(f"M{q4[0] + 60:.1f},{q4[1] + q4[3]:.1f} L{q4[0] + 60:.1f},{band_a:.1f} "
           f"L{r1[0] + r1[2] / 2:.1f},{band_a:.1f} "
           f"L{r1[0] + r1[2] / 2:.1f},{r1[1]:.1f}",
           stroke=GREEN, sw=1.5, marker="green")
    s.text(q4[0] + 66, band_a - 5, "converged", size=9.5, fill=GREEN)
    s.path(f"M{q4[0] + q4[2] - 60:.1f},{q4[1] + q4[3]:.1f} "
           f"L{q4[0] + q4[2] - 60:.1f},{band_b:.1f} "
           f"L{r3[0] + r3[2] / 2:.1f},{band_b:.1f} "
           f"L{r3[0] + r3[2] / 2:.1f},{r3[1]:.1f}",
           stroke=ACCENT, sw=1.5, marker="accent")
    s.text(r3[0] + r3[2] / 2 + 8, band_b - 5, "escalate", size=9.5, fill=ACCENT)
    s.arrow(r1[0] + r1[2], mid("Output & human review"), r2[0],
            mid("Output & human review"), color="ink3")

    s.caption_tag(LX + 2, H - 10,
                  "STEPS 1–16 · THE DEBATE LOOP (10–12) REPEATS UNTIL THE STOPPING "
                  "RULE FIRES · NO OUTPUT REACHES CARE WITHOUT CLINICIAN SIGN-OFF")
    return s


# ==========================================================================
# Fig. 3 — retrieval pipeline
# ==========================================================================
def fig03_rag() -> SVG:
    s = SVG(1180, 470)
    y0 = 96
    q = (40, y0 + 52, 190, 74)
    s.box(q[0], q[1], q[2], q[3], "Agent sub-query", "persona intent + CCO fields",
          fill=PAPER2, stroke=INK, wrap_chars=22)
    s.box(280, 40, 210, 66, "Dense retrieval", "embedding cosine", fill=PAPER2, stroke=SLATE)
    s.box(280, 236, 210, 66, "Sparse retrieval", "Okapi BM25", fill=PAPER2, stroke=OCHRE)
    s.box(548, 138, 180, 66, "RRF fusion", "rank-level merge", fill="#F3E4E6", stroke=ACCENT)
    s.box(786, 138, 180, 66, "Cross-encoder", "precision re-rank", fill=PAPER2, stroke=INK)
    s.box(786, 300, 180, 66, "Scope boost", "specialty + recency", fill=PAPER2, stroke=INK)
    s.box(1010, 138, 140, 66, "Grounding", "entailment gate", fill="#F2F6F3", stroke=GREEN)

    s.arrow(230, y0 + 62, 278, 78, color="slate")
    s.arrow(230, y0 + 100, 278, 262, color="ochre")
    s.arrow(490, 74, 546, 158, color="slate")
    s.arrow(490, 268, 546, 186, color="ochre")
    s.arrow(728, 171, 784, 171, color="accent")
    s.arrow(876, 300, 876, 208, color="ink3", dash="4 3")
    s.arrow(966, 171, 1008, 171, color="ink3")

    s.text(590, 246, "RRF(d) = Σ", size=14, fill=INK, family=SERIF)
    s.text(660, 236, "1", size=13, anchor="middle", fill=INK, family=SERIF)
    s.line(646, 241, 676, 241, stroke=INK, sw=1.1)
    s.text(661, 256, "k + rank", size=12, anchor="middle", fill=INK, family=SERIF)
    s.text(700, 246, "r (d)", size=11, fill=INK, family=SERIF)
    s.text(748, 246, ",   k ≈ 60", size=13, fill=INK, family=SERIF)

    s.text(40, 40, "Corpus: versioned passages carrying source, section, publication "
           "year, evidence grade and specialty tags", size=11, fill=INK3)
    s.text(40, 420, "Only claims whose cited passage entails them may enter the debate; "
           "every surviving citation is written to the Evidence Ledger.",
           size=11, fill=INK2)
    s.caption_tag(40, 444, "PROTOTYPE USES A HASHED BAG-OF-WORDS VECTOR SPACE AS A "
                  "STAND-IN FOR A LEARNED MEDICAL EMBEDDING MODEL")
    return s


# ==========================================================================
# Fig. 4 — debate sequence diagram
# ==========================================================================
def fig04_sequence() -> SVG:
    s = SVG(1080, 800)
    actors = [("Orchestrator", 130, ACCENT), ("Radiologist", 400, SLATE),
              ("Cardiologist", 640, ACCENT), ("Oncologist", 880, OCHRE)]
    top, bottom = 74, 470          # lifelines terminate before the assess phase

    # Phase bands are filled, so they must be painted BEFORE the lifelines,
    # otherwise they would hide them.
    phases = [("PROPOSE", 96, 168, "independent · isolated"),
              ("CRITIQUE", 208, 300, "anonymised · grounded"),
              ("REBUT", 340, 452, "revise · re-retrieve"),
              ("ASSESS", 492, 584, "D̄, red flags, stopping rule"),
              ("OUTCOME", 624, 706, "consensus or escalation")]
    for label, y1, y2, note in phases:
        s.rect(28, y1 - 18, 1024, y2 - y1 + 30, fill="#FBFAF7", stroke=RULE,
               sw=1.0, rx=3)
        s.text(38, y1 - 4, label, size=10.5, fill=ACCENT, weight="bold",
               spacing="0.14em")
        s.text(38, y1 + 11, note, size=9.5, fill=FAINT)

    for name, x, col in actors:
        s.line(x, top, x, bottom, stroke=RULE, sw=1.2, dash="3 4")
        s.line(x - 9, bottom, x + 9, bottom, stroke=RULE, sw=1.6)
        s.rect(x - 82, 38, 164, 34, fill=PAPER2, stroke=INK, sw=1.3, rx=4)
        s.text(x, 60, name, size=12.5, anchor="middle", fill=INK, weight="bold")

    def msg(x1: float, x2: float, y: float, label: str, color: str = "ink3",
            dash: Optional[str] = None) -> None:
        s.arrow(x1, y, x2, y, color=color, dash=dash, sw=1.4)
        mx = (x1 + x2) / 2
        s.text(mx, y - 6, label, size=10, anchor="middle", fill=INK2)

    # propose
    msg(130, 400, 118, "CCO + scope", "ink3")
    msg(130, 640, 136, "CCO + scope", "ink3")
    msg(130, 880, 154, "CCO + scope", "ink3")
    s.text(400, 186, "p=0.91 malignancy", size=9.5, anchor="middle", fill=SLATE)
    s.text(640, 186, "p=0.79 demand isch.", size=9.5, anchor="middle", fill=ACCENT)
    s.text(880, 186, "p=0.95 malignancy", size=9.5, anchor="middle", fill=OCHRE)

    # critique (cross arrows)
    msg(640, 880, 232, "missing cytology → M1a unproven", "accent")
    msg(880, 400, 262, "nodule morphology non-specific alone", "ochre", dash="4 3")
    msg(400, 640, 290, "effusion not haemodynamic on CT", "slate", dash="4 3")

    # rebut
    msg(880, 130, 364, "concede: stage unproven, p 0.95→0.88", "ochre")
    msg(400, 130, 394, "defend: grounded RAD-001, p held", "slate")
    msg(640, 130, 424, "hold: tamponade needs echo", "accent")

    # assess
    s.rect(48, 508, 164, 62, fill="#F3E4E6", stroke=ACCENT, sw=1.4, rx=4)
    s.text(130, 530, "compute D̄", size=11.5, anchor="middle", fill=INK, weight="bold")
    s.text(130, 546, "check red flags", size=10, anchor="middle", fill=INK3)
    s.text(130, 561, "apply stopping rule", size=10, anchor="middle", fill=INK3)

    # outcome
    s.rect(300, 640, 300, 56, fill="#F2F6F3", stroke=GREEN, sw=1.4, rx=4)
    s.text(450, 662, "CONVERGED", size=12, anchor="middle", fill=GREEN, weight="bold")
    s.text(450, 679, "D̄ ≤ τ_agree → aggregate & report", size=10,
           anchor="middle", fill=INK3)
    s.rect(650, 640, 380, 56, fill="#F3E4E6", stroke=ACCENT, sw=1.4, rx=4)
    s.text(840, 662, "ESCALATED", size=12, anchor="middle", fill=ACCENT, weight="bold")
    s.text(840, 679, "can't-miss dx or unresolved disagreement → human",
           size=10, anchor="middle", fill=INK3)
    s.arrow(212, 539, 298, 650, color="green")
    s.arrow(212, 552, 648, 650, color="accent")

    s.caption_tag(28, 770, "MESSAGE LABELS ARE ABRIDGED FROM THE ACTUAL CASE-001 "
                  "TRANSCRIPT PRODUCED BY THE PROTOTYPE")
    return s


# ==========================================================================
# Fig. 5 — orchestrator state machine
# ==========================================================================
def fig05_fsm() -> SVG:
    s = SVG(1120, 430)
    nodes = {
        "INTAKE": (60, 150, 130, 56), "PROPOSE": (232, 150, 140, 56),
        "CRITIQUE": (414, 150, 140, 56), "REBUT": (596, 150, 130, 56),
        "ASSESS": (768, 150, 140, 56),
        "CONSENSUS": (946, 56, 150, 56), "ESCALATE": (946, 250, 150, 56),
    }
    for name, (x, y, w, h) in nodes.items():
        if name == "ASSESS":
            fill, stroke = "#F3E4E6", ACCENT
        elif name == "CONSENSUS":
            fill, stroke = "#F2F6F3", GREEN
        elif name == "ESCALATE":
            fill, stroke = "#F3E4E6", ACCENT
        else:
            fill, stroke = PAPER2, INK
        s.rect(x, y, w, h, fill=fill, stroke=stroke, sw=1.5, rx=6)
        col = GREEN if name == "CONSENSUS" else (ACCENT if name in ("ESCALATE", "ASSESS") else INK)
        s.text(x + w / 2, y + h / 2 + 4.5, name, size=12.5, anchor="middle",
               fill=col, weight="bold")

    def edge(a: str, b: str, label: str = "", color: str = "ink3") -> None:
        ax, ay, aw, ah = nodes[a]
        bx_, by_, bw, bh = nodes[b]
        s.arrow(ax + aw, ay + ah / 2, bx_, by_ + bh / 2, color=color,
                label=label, label_size=9.5)

    edge("INTAKE", "PROPOSE")
    edge("PROPOSE", "CRITIQUE")
    edge("CRITIQUE", "REBUT")
    edge("REBUT", "ASSESS")
    s.arrow(908, 168, 944, 96, color="green", label="D̄ ≤ τ", label_size=10)
    s.arrow(908, 190, 944, 268, color="accent", label="red flag ∨ r=R_max",
            label_size=10, label_dy=12)
    # loop back
    s.path("M838,206 L838,350 L302,350 L302,206", stroke=ACCENT, sw=1.5,
           marker="accent")
    s.text(570, 366, "D̄ > τ_agree  ∧  r < R_max   (re-enter critique with new evidence)",
           size=10.5, anchor="middle", fill=ACCENT)
    s.arrow(1021, 112, 1021, 248, color="accent", dash="4 3")
    s.text(1032, 184, "red-flag override", size=9.5, fill=ACCENT)
    s.text(60, 60, "Guards are evaluated by a deterministic controller; no free-form "
           "model decides control flow.", size=11, fill=INK3)
    s.text(60, 398, "τ_agree = 0.010    τ_flag = 0.30    R_max = 4    r_min = 1",
           size=10.5, fill=INK2, family=MONO)
    return s



# ==========================================================================
# Fig. 6 — consensus dataflow
# ==========================================================================
def fig06_consensus() -> SVG:
    s = SVG(1140, 560)
    # agent inputs
    inputs = [("Radiologist", "p₁ = 0.91", SLATE, 58),
              ("Cardiologist", "p₂ = 0.17", ACCENT, 148),
              ("Oncologist", "p₃ = 0.95", OCHRE, 238),
              ("Generalist", "p₄ = 0.88", GREY, 328)]
    for nm, val, col, y in inputs:
        s.rect(40, y, 196, 62, fill=PAPER2, stroke=INK, sw=1.3, rx=4)
        s.add(f'<path d="M41,{y + 3:.0f} L41,{y + 59:.0f}" stroke="{col}" stroke-width="3.2"/>')
        s.text(56, y + 25, nm, size=12, fill=INK, weight="bold")
        s.text(56, y + 43, val, size=11.5, fill=col, family=MONO)
        s.text(150, y + 43, "cᵢ, wᵢ(h)", size=10.5, fill=INK3, family=MONO)

    # weighting stage
    s.rect(300, 96, 200, 250, fill="#FBFAF7", stroke=RULE, sw=1.2, rx=5)
    s.text(400, 118, "weighting", size=11.5, anchor="middle", fill=ACCENT, weight="bold")
    s.text(400, 146, "cᵢ = calibrated", size=11, anchor="middle", fill=INK2)
    s.text(400, 164, "confidence", size=11, anchor="middle", fill=INK2)
    s.text(400, 194, "wᵢ(h) = specialty", size=11, anchor="middle", fill=INK2)
    s.text(400, 212, "weight (soft MoE)", size=11, anchor="middle", fill=INK2)
    s.rect(318, 236, 164, 92, fill="#FFFFFF", stroke=RULE, sw=1.0, rx=3)
    s.text(400, 256, "floors excluded", size=10.5, anchor="middle", fill=ACCENT,
           weight="bold")
    s.wrap(400, 272, "an out-of-domain agent's caution floor is absence of opinion, "
           "not dissent", 26, size=9.5, anchor="middle", fill=INK3)
    for _, _, _, y in inputs:
        s.arrow(236, y + 31, 298, 221, color="faint", sw=1.1)

    # equations
    s.rect(548, 60, 250, 84, fill="#F3E4E6", stroke=ACCENT, sw=1.4, rx=5)
    s.text(673, 86, "Eq. 1   S(h)", size=13, anchor="middle", fill=INK, weight="bold")
    s.text(673, 108, "Σ wᵢcᵢpᵢ ⁄ Σ wᵢcᵢ", size=12, anchor="middle", fill=INK2,
           family=SERIF)
    s.text(673, 128, "confidence-weighted mean", size=9.5, anchor="middle", fill=INK3)

    s.rect(548, 186, 250, 84, fill="#F3E4E6", stroke=ACCENT, sw=1.4, rx=5)
    s.text(673, 212, "Eq. 3   D̄", size=13, anchor="middle", fill=INK, weight="bold")
    s.text(673, 234, "Σ wᵢcᵢ(pᵢ − S)² ⁄ Σ wᵢcᵢ", size=12, anchor="middle", fill=INK2,
           family=SERIF)
    s.text(673, 254, "weighted variance", size=9.5, anchor="middle", fill=INK3)

    s.rect(548, 312, 250, 84, fill=PAPER2, stroke=INK, sw=1.3, rx=5)
    s.text(673, 338, "E(h)", size=13, anchor="middle", fill=INK, weight="bold")
    s.text(673, 358, "grade × recency × entailment", size=10.5, anchor="middle",
           fill=INK2)
    s.text(673, 376, "support − refute", size=10, anchor="middle", fill=INK3)

    s.arrow(500, 200, 546, 102, color="ink3")
    s.arrow(500, 221, 546, 228, color="ink3")
    s.arrow(500, 242, 546, 354, color="ink3")

    # S*
    s.rect(852, 128, 246, 96, fill="#F3E4E6", stroke=ACCENT, sw=1.6, rx=5)
    s.text(975, 156, "Eq. 2   S*(h)", size=14, anchor="middle", fill=INK, weight="bold")
    s.text(975, 180, "σ( α·logit S + β·E )", size=13, anchor="middle", fill=INK2,
           family=SERIF)
    s.text(975, 202, "evidence-adjusted score", size=9.5, anchor="middle", fill=INK3)
    s.arrow(798, 102, 850, 160, color="accent")
    s.arrow(798, 354, 850, 200, color="accent")

    # outputs
    s.rect(852, 266, 246, 62, fill=PAPER2, stroke=INK, sw=1.3, rx=5)
    s.text(975, 290, "ranked differential", size=12, anchor="middle", fill=INK,
           weight="bold")
    s.text(975, 308, "sorted by S*(h)", size=10, anchor="middle", fill=INK3)
    s.rect(852, 348, 246, 62, fill="#F2F6F3", stroke=GREEN, sw=1.3, rx=5)
    s.text(975, 372, "stopping rule", size=12, anchor="middle", fill=GREEN,
           weight="bold")
    s.text(975, 390, "converge · bound · red flag", size=10, anchor="middle", fill=INK3)
    s.arrow(975, 224, 975, 264, color="accent")
    s.arrow(798, 228, 850, 372, color="accent")

    s.text(40, 452, "Values shown are the actual round-0 likelihoods for “Primary lung "
           "malignancy” in CASE-001. The cardiologist's 0.17 is a cautionary floor "
           "(no persona prior for an", size=11, fill=INK2)
    s.text(40, 470, "oncological diagnosis): it participates in S(h) with reduced "
           "weight but is excluded from the disagreement metric.", size=11, fill=INK2)
    s.caption_tag(40, 502, "α = 1.0    β = 0.55    TOP-k = 3 FOR THE CASE-LEVEL MEAN D̄")
    return s


# ==========================================================================
# Fig. 7 — intake modalities → CCO
# ==========================================================================
def fig07_cco() -> SVG:
    s = SVG(1080, 560)
    mods = [
        ("Structured EHR", "FHIR / HL7", "schema map · unit normalise", "labs, meds, problems"),
        ("Clinical notes", "H&P, discharge", "de-id · section · negation", "narrative, entities"),
        ("Imaging", "DICOM CT/MRI/echo", "vision model → findings", "imaging_findings"),
        ("Pathology", "reports, WSI", "biomarker extraction", "pathology"),
        ("Genomics", "VCF, panels", "variant annotation", "genomics"),
        ("Waveforms", "ECG, telemetry", "interval & morphology", "ecg_features"),
    ]
    y = 58
    for name, src, proc, out in mods:
        s.rect(36, y, 170, 56, fill=PAPER2, stroke=INK, sw=1.2, rx=4)
        s.text(46, y + 24, name, size=12, fill=INK, weight="bold")
        s.text(46, y + 41, src, size=10, fill=INK3)
        s.rect(240, y, 236, 56, fill="#FFFFFF", stroke=RULE, sw=1.1, rx=4)
        s.wrap(252, y + 27, proc, 32, size=10.5, fill=INK2)
        s.text(516, y + 34, out, size=10.5, fill=SLATE, family=MONO)
        s.arrow(206, y + 28, 238, y + 28, color="faint", sw=1.1)
        s.arrow(476, y + 28, 512, y + 28, color="faint", sw=1.1)
        y += 74

    s.rect(700, 58, 340, 440, fill="#FBFAF7", stroke=ACCENT, sw=1.5, rx=6)
    s.text(870, 86, "Case Context Object", size=14, anchor="middle", fill=INK,
           weight="bold")
    s.text(870, 104, "single shared representation", size=10.5, anchor="middle",
           fill=INK3)
    fields = ["case_id", "demographics", "vitals", "labs[]  (LOINC)",
              "problems[]  (ICD-10)", "meds[]  (RxNorm)", "narrative",
              "imaging_findings[]", "pathology[]", "genomics[]", "ecg_features",
              "absent[]  — explicit negations"]
    fy = 132
    for f in fields:
        s.text(724, fy, "·", size=12, fill=ACCENT)
        s.text(738, fy, f, size=11, fill=INK2, family=MONO)
        fy += 26
    s.rect(720, 450, 300, 34, fill="#F3E4E6", stroke=ACCENT, sw=1.2, rx=3)
    s.text(870, 471, "no direct identifiers cross this boundary", size=10.5,
           anchor="middle", fill=ACCENT)
    for i in range(len(mods)):
        s.arrow(612, 58 + i * 74 + 28, 698, 240 + (i - 2.5) * 8, color="faint", sw=1.0)
    s.caption_tag(36, 534, "EXPLICIT NEGATIONS ARE CARRIED SO AGENTS CAN DISTINGUISH "
                  "“ABSENT” FROM “NOT ASSESSED”")
    return s


# ==========================================================================
# Fig. 8 — anatomy of the report
# ==========================================================================
def fig08_report() -> SVG:
    s = SVG(1000, 640)
    s.rect(60, 40, 520, 560, fill="#FFFFFF", stroke=INK, sw=1.4, rx=5)
    secs = [
        ("Status banner", "converged / escalated + reason", ACCENT, 52),
        ("1 · Synthesis", "one-line leading impression", INK, 116),
        ("2 · Can't-miss panel", "red-flag dx and work-up status", ACCENT, 180),
        ("3 · Ranked differential", "S*, S, E, disagreement, next test", INK, 244),
        ("4 · Evidence by hypothesis", "cited support and refutation", INK, 328),
        ("5 · Points of disagreement", "where specialists diverged", ACCENT, 412),
        ("6 · Debate trajectory", "D̄ per round, retrieval count", INK, 476),
        ("7 · Next steps", "discriminating investigations", INK, 524),
        ("8 · Audit trail", "Evidence Ledger, replayable", GREEN, 572),
    ]
    for title, sub, col, y in secs:
        s.line(76, y, 564, y, stroke=RULE, sw=1.0)
        s.text(80, y + 18, title, size=12, fill=col, weight="bold")
        s.text(80, y + 34, sub, size=10.2, fill=INK3)

    notes = [
        (52, "leads with status, not an answer"),
        (180, "can't-miss diagnoses are never buried"),
        (412, "disagreement is surfaced, not suppressed"),
        (572, "every claim traceable to a passage"),
    ]
    for y, txt in notes:
        s.line(584, y + 16, 626, y + 16, stroke=ACCENT, sw=1.1, dash="3 3")
        s.wrap(634, y + 20, txt, 30, size=10.5, fill=ACCENT)

    s.text(60, 626, "Design principle: the clinically valuable content is what the "
           "system is uncertain about — so uncertainty is placed first, not last.",
           size=11, fill=INK2)
    return s


# ==========================================================================
# Fig. 9 — deployment and trust boundaries
# ==========================================================================
def fig09_deployment() -> SVG:
    s = SVG(1080, 520)
    # PHI enclave
    s.rect(40, 60, 420, 400, fill="#FBF3F4", stroke=ACCENT, sw=1.6, rx=8, dash="7 5")
    s.text(56, 84, "PHI ENCLAVE", size=11, fill=ACCENT, weight="bold", spacing="0.14em")
    s.box(70, 104, 360, 58, "Source systems", "EHR · PACS · LIS", fill="#FFFFFF",
          stroke=INK)
    s.box(70, 182, 360, 58, "De-identification service", "Safe Harbor / expert determination",
          fill="#FFFFFF", stroke=INK)
    s.box(70, 260, 170, 58, "Token map", "restricted", fill="#FFFFFF", stroke=ACCENT)
    s.box(260, 260, 170, 58, "Raw pixels", "never exported", fill="#FFFFFF", stroke=ACCENT)
    s.box(70, 340, 360, 58, "Access audit log", "immutable, per-access records",
          fill="#FFFFFF", stroke=GREEN)
    s.arrow(250, 162, 250, 180, color="ink3")
    s.arrow(250, 240, 250, 258, color="ink3")

    # reasoning zone
    s.rect(520, 60, 520, 260, fill="#FBFAF7", stroke=INK, sw=1.5, rx=8)
    s.text(536, 84, "REASONING ZONE — DE-IDENTIFIED ONLY", size=11, fill=INK2,
           weight="bold", spacing="0.1em")
    s.box(544, 104, 226, 58, "Agent runtime", "specialist LLM calls", fill="#FFFFFF",
          stroke=INK)
    s.box(790, 104, 226, 58, "Orchestrator", "deterministic FSM", fill="#FFFFFF",
          stroke=ACCENT)
    s.box(544, 182, 226, 58, "Retrieval service", "vector + BM25 index",
          fill="#FFFFFF", stroke=SLATE)
    s.box(790, 182, 226, 58, "Evidence Ledger", "append-only provenance",
          fill="#FFFFFF", stroke=GREEN)
    s.box(544, 252, 472, 52, "Consensus & calibration", "Eqs. (1)–(3), stopping rule",
          fill="#FFFFFF", stroke=INK)

    # clinician zone
    s.rect(520, 350, 520, 130, fill="#F2F6F3", stroke=GREEN, sw=1.5, rx=8)
    s.text(536, 374, "CLINICAL REVIEW", size=11, fill=GREEN, weight="bold",
           spacing="0.14em")
    s.box(544, 390, 226, 58, "Report + re-identify", "via token map, on demand",
          fill="#FFFFFF", stroke=INK)
    s.box(790, 390, 226, 58, "Clinician sign-off", "mandatory before any action",
          fill="#FFFFFF", stroke=GREEN)
    s.arrow(770, 419, 788, 419, color="green")

    s.arrow(460, 210, 542, 133, color="ink3", label="CCO (de-identified)",
            label_size=9.5, label_dy=-8)
    s.arrow(780, 304, 700, 388, color="ink3")
    s.arrow(560, 448, 250, 400, color="accent", dash="5 4")
    s.text(360, 470, "re-identification only at the point of care, logged",
           size=10, anchor="middle", fill=ACCENT)
    s.caption_tag(40, 500, "NO PATIENT IDENTIFIER CROSSES INTO THE REASONING ZONE; "
                  "EVERY ACCESS IS AUDITED")
    return s


# ==========================================================================
# Fig. 10 — DATA: disagreement trajectories
# ==========================================================================
def fig10_convergence(trace: dict) -> SVG:
    s = SVG(880, 520)
    cases = trace["cases"]
    max_r = max(len(c["rounds"]) - 1 for c in cases)
    ymax = max(0.05, max(r["D_bar"] for c in cases for r in c["rounds"]) * 1.18)
    ax = Axes(s, 88, 46, 620, 350, (0, max_r), (0, ymax),
              xlabel="debate round  r", ylabel="mean disagreement  D̄",
              xticks=list(range(max_r + 1)),
              yticks=[i * ymax / 4 for i in range(5)], ytick_fmt="{:.3f}")
    ax.hline(0.010, color=GREEN, dash="6 4", label="τ_agree = 0.010")
    for c in cases:
        col = CASE_COLORS.get(c["case_id"], INK)
        pts = [(r["round"], r["D_bar"]) for r in c["rounds"]]
        dash = None if c["status"] == "escalated" else "6 4"
        ax.plot(pts, color=col, dash=dash)
        last = pts[-1]
        tag = "escalated" if c["status"] == "escalated" else "converged"
        ax.annotate(last[0], last[1], f"  {c['case_id']} · {tag}", size=10.5,
                    color=col, dy=-9)
    s.legend(740, 70, [(CASE_COLORS[c["case_id"]],
                        f"{c['case_id']} ({c['status']})") for c in cases], gap=17)
    s.text(88, 448, "CASE-002 falls below τ_agree and converges. CASE-001 plateaus "
           "above it: the specialists cannot reconcile, so the case escalates with",
           size=11, fill=INK2)
    s.text(88, 466, "its open disagreement stated. CASE-003 agrees early but still "
           "escalates — a can't-miss diagnosis overrides consensus.", size=11, fill=INK2)
    s.caption_tag(88, 496, "COMPUTED FROM prototype/output/trace.json — REAL RUN DATA")
    return s


# ==========================================================================
# Fig. 11 — DATA: cross-specialty divergence
# ==========================================================================
def fig11_divergence(trace: dict) -> SVG:
    s = SVG(940, 540)
    case = next(c for c in trace["cases"] if c["case_id"] == "CASE-001")
    items = [i for i in case["consensus"] if i["per_agent"]][:4]
    agents = ["Radiologist", "Cardiologist", "Oncologist", "Generalist"]

    ax = Axes(s, 96, 46, 700, 330, (0, len(items)), (0, 1.0),
              xlabel="", ylabel="agent likelihood  pᵢ(h)",
              yticks=[0, 0.25, 0.5, 0.75, 1.0], ytick_fmt="{:.2f}")
    group_w = 700 / len(items)
    bar_w = group_w / (len(agents) + 1.6)
    for gi, item in enumerate(items):
        gx = gi + 0.5
        for ai, agent in enumerate(agents):
            p = item["per_agent"].get(agent)
            if p is None:
                continue
            offset = (ai - (len(agents) - 1) / 2) * (bar_w / group_w * 1.0)
            ax.vbar(gx + offset, p, bar_w * 0.86, AGENT_COLORS[agent])
        # S* marker
        sx = ax.px(gx)
        sy = ax.py(item["S_star"])
        s.line(sx - group_w * 0.36, sy, sx + group_w * 0.36, sy, stroke=INK,
               sw=1.8, dash="4 3")
        s.text(sx, sy - 7, f"S* {item['S_star']:.2f}", size=10, anchor="middle",
               fill=INK, weight="bold")
        # x label
        label = item["dx"]
        if len(label) > 26:
            label = label[:24] + "…"
        s.wrap(sx, 396, label, 20, size=10, anchor="middle", fill=INK2)
        if item["red_flag"]:
            s.text(sx, 434, "can't-miss", size=9.5, anchor="middle", fill=ACCENT)

    s.legend(812, 70, [(AGENT_COLORS[a], a) for a in agents], gap=18, swatch="box")
    s.line(812, 158, 830, 158, stroke=INK, sw=1.8, dash="4 3")
    s.text(836, 161.5, "S*(h)", size=10.5, fill=INK2)
    s.text(96, 480, "The cardiologist's low value on the oncological hypotheses is a "
           "cautionary floor, not a considered dissent; specialty weighting keeps it "
           "from", size=11, fill=INK2)
    s.text(96, 498, "dominating S*(h), and it is excluded from D̄ entirely.",
           size=11, fill=INK2)
    s.caption_tag(96, 524, "CASE-001, FINAL ROUND — REAL RUN DATA")
    return s


# ==========================================================================
# Fig. 12 — DATA: ranked differential
# ==========================================================================
def fig12_differential(trace: dict) -> SVG:
    s = SVG(940, 500)
    case = next(c for c in trace["cases"] if c["case_id"] == "CASE-001")
    items = case["consensus"][:6]
    n = len(items)
    ax = Axes(s, 300, 46, 470, 300, (0, 1.0), (0, n),
              xlabel="score", ylabel="",
              xticks=[0, 0.25, 0.5, 0.75, 1.0], yticks=[])
    for i, item in enumerate(items):
        yv = n - i - 0.5
        col = ACCENT if item["red_flag"] else SLATE
        ax.hbar(yv, item["S_star"], 22, col)
        py = ax.py(yv)
        s.text(292, py + 4, item["dx"], size=11, anchor="end", fill=INK)
        s.text(ax.px(item["S_star"]) + 8, py + 4, f"{item['S_star']:.2f}", size=10.5,
               fill=INK, weight="bold")
        # S marker (pre-evidence adjustment)
        sx = ax.px(item["S"])
        s.line(sx, py - 13, sx, py + 13, stroke=INK, sw=1.6)
        # E annotation
        s.text(786, py + 4, f"E {item['E']:+.2f}", size=10, fill=INK3, family=MONO)
        if item["red_flag"]:
            s.text(862, py + 4, "can't-miss", size=9.5, fill=ACCENT)

    s.legend(300, 386, [(SLATE, "S*(h) — evidence-adjusted"),
                        (ACCENT, "S*(h), can't-miss diagnosis")], gap=17, swatch="box")
    s.line(620, 386, 620, 396, stroke=INK, sw=1.6)
    s.text(632, 394, "S(h) before evidence adjustment", size=10.5, fill=INK2)
    s.text(300, 440, "Evidence adjustment separates hypotheses that merely look "
           "plausible from those the corpus actually supports:", size=11, fill=INK2)
    s.text(300, 458, "note where S* moves away from S.", size=11, fill=INK2)
    s.caption_tag(300, 484, "CASE-001 — REAL RUN DATA")
    return s


# ==========================================================================
# Fig. 13 — DATA: reliability diagram
# ==========================================================================
def fig13_calibration(trace: dict) -> SVG:
    s = SVG(880, 540)
    pairs = [(float(p), int(y)) for p, y in trace["calibration_pairs"]]
    nb = 5
    bins: List[Tuple[float, float, int]] = []
    for b in range(nb):
        lo, hi = b / nb, (b + 1) / nb
        bucket = [(p, y) for p, y in pairs if (p > lo or b == 0) and p <= hi]
        if not bucket:
            continue
        conf = sum(p for p, _ in bucket) / len(bucket)
        acc = sum(y for _, y in bucket) / len(bucket)
        bins.append((conf, acc, len(bucket)))

    ax = Axes(s, 96, 46, 400, 400, (0, 1), (0, 1),
              xlabel="predicted probability  S*(h)",
              ylabel="observed frequency (gold diagnosis)",
              xticks=[0, 0.25, 0.5, 0.75, 1.0], yticks=[0, 0.25, 0.5, 0.75, 1.0],
              ytick_fmt="{:.2f}")
    ax.diagonal()
    s.text(ax.px(0.80), ax.py(0.86), "perfect calibration", size=10, fill=INK3)
    ax.plot([(c, a) for c, a, _ in bins], color=ACCENT, marker=False, sw=2.2)
    for c, a, cnt in bins:
        r = 3.4 + min(6.0, cnt ** 0.5 * 1.5)
        s.circle(ax.px(c), ax.py(a), r, fill=ACCENT)
        s.text(ax.px(c) + r + 5, ax.py(a) + 4, f"n={cnt}", size=9.5, fill=INK3)

    summ = trace["summary"]
    s.rect(548, 60, 300, 168, fill=PAPER2, stroke=INK, sw=1.3, rx=5)
    s.text(568, 88, "Run summary", size=13, fill=INK, weight="bold")
    rows = [("cases", f"{summ['n_cases']}"),
            ("top-1 accuracy", f"{summ['top1']:.0%}"),
            ("top-3 accuracy", f"{summ['top3']:.0%}"),
            ("ECE", f"{summ['ece']:.3f}"),
            ("Brier", f"{summ['brier']:.3f}"),
            ("groundedness", f"{summ['groundedness']:.0%}")]
    ry = 114
    for k, v in rows:
        s.text(568, ry, k, size=11, fill=INK3)
        s.text(828, ry, v, size=11.5, anchor="end", fill=INK, family=MONO,
               weight="bold")
        ry += 20

    s.text(96, 480, "Marker area is proportional to bin count. With only three "
           "demonstration cases these bins are small: the figure shows the analysis "
           "format and the", size=11, fill=INK2)
    s.text(96, 498, "prototype's genuine (uncalibrated) behaviour, not a validated "
           "calibration claim.", size=11, fill=INK2)
    s.caption_tag(96, 524, "REAL RUN DATA · SMALL-SAMPLE, NOT A VALIDATION RESULT")
    return s


# ==========================================================================
# Fig. 14 — ablation (illustrative / hypothesis)
# ==========================================================================
def fig14_ablation() -> SVG:
    s = SVG(880, 500)
    conds = [("Single\nagent", 0.61, GREY), ("Majority\nvote", 0.68, SLATE),
             ("Debate,\nno RAG", 0.74, OCHRE), ("MedJar\n(full)", 0.83, ACCENT)]
    ax = Axes(s, 96, 46, 600, 320, (0, len(conds)), (0, 1.0),
              xlabel="", ylabel="expected top-3 accuracy",
              yticks=[0, 0.25, 0.5, 0.75, 1.0], ytick_fmt="{:.2f}")
    for i, (label, val, col) in enumerate(conds):
        ax.vbar(i + 0.5, val, 78, col, label=f"{val:.2f}")
        px = ax.px(i + 0.5)
        for j, ln in enumerate(label.split("\n")):
            s.text(px, 392 + j * 15, ln, size=11, anchor="middle", fill=INK2)
    # deltas
    for i in range(len(conds) - 1):
        x1, x2 = ax.px(i + 0.5), ax.px(i + 1.5)
        y = ax.py(conds[i + 1][1]) - 22
        s.arrow(x1 + 42, y, x2 - 42, y, color="faint", sw=1.1)
        d = conds[i + 1][1] - conds[i][1]
        s.text((x1 + x2) / 2, y - 6, f"+{d:.2f}", size=10, anchor="middle", fill=INK3)

    s.text(96, 442, "Predicted direction of effect for the planned ablation: "
           "ensembling helps, structured debate helps more, and grounding "
           "contributes the", size=11, fill=INK2)
    s.text(96, 460, "largest single increment. These are hypotheses to be tested, "
           "not measurements.", size=11, fill=INK2)
    s.caption_tag(96, 486, "ILLUSTRATIVE — EXPECTED EFFECTS, NOT MEASURED RESULTS")
    return s


# ==========================================================================
FIGURES = [
    ("fig01_architecture", "Layered system architecture.", fig01_architecture, False),
    ("fig02_workflow", "End-to-end workflow across trust boundaries and layers "
     "(steps 1–16).", fig02_workflow, False),
    ("fig03_rag_pipeline", "Hybrid retrieval, fusion, re-ranking and the "
     "groundedness gate.", fig03_rag, False),
    ("fig04_debate_sequence", "Debate protocol as a message sequence.", fig04_sequence, False),
    ("fig05_state_machine", "Orchestrator finite-state machine with guards.", fig05_fsm, False),
    ("fig06_consensus_dataflow", "How agent opinions become S*(h) and D̄.",
     fig06_consensus, False),
    ("fig07_cco", "Multimodal intake normalised into the Case Context Object.",
     fig07_cco, False),
    ("fig08_report_anatomy", "Anatomy of the unified diagnostic report.", fig08_report, False),
    ("fig09_deployment", "Deployment topology and trust boundaries.", fig09_deployment, False),
    ("fig10_convergence", "Disagreement trajectories: convergence versus escalation.",
     fig10_convergence, True),
    ("fig11_divergence", "Cross-specialty divergence on CASE-001 hypotheses.",
     fig11_divergence, True),
    ("fig12_differential", "Ranked differential for CASE-001 with evidence adjustment.",
     fig12_differential, True),
    ("fig13_calibration", "Reliability diagram and run summary.", fig13_calibration, True),
    ("fig14_ablation", "Planned ablation (illustrative).", fig14_ablation, False),
]


def main() -> int:
    trace = load_trace()
    if trace is None:
        print("! trace.json not found — run prototype/run_demo.py first.")
        print("  Structural figures will still be generated.")

    written: List[Tuple[str, str]] = []
    for name, caption, fn, needs_data in FIGURES:
        if needs_data and trace is None:
            print(f"  skip  {name} (needs run data)")
            continue
        svg = fn(trace) if needs_data else fn()
        path = os.path.join(OUT, name + ".svg")
        svg.save(path)
        written.append((name, caption))
        print(f"  wrote {name}.svg  ({os.path.getsize(path):,} bytes)")

    # figure index
    idx = ["# MedJar — figure set", "",
           "Vector figures generated by `make_figures.py`. Structural figures are "
           "drawn from the system specification; result figures are computed from "
           "`../prototype/output/trace.json`, so they cannot drift from the "
           "prototype's actual behaviour.", ""]
    for i, (name, caption) in enumerate(written, 1):
        idx += [f"### Figure {i} — {caption}", "",
                f"![{caption}]({name}.svg)", ""]
    with open(os.path.join(OUT, "README.md"), "w", encoding="utf-8") as f:
        f.write("\n".join(idx))
    print(f"\n{len(written)} figures + README.md index written to {OUT}/")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

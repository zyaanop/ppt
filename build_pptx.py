#!/usr/bin/env python3
"""
build_pptx.py — Generate MedJar.pptx from scratch using ONLY the Python
standard library (zipfile + raw Office Open XML). No python-pptx needed.

A .pptx is a ZIP (OPC package) of XML parts. We emit a minimal-but-valid
presentation: theme + master + layout + N dark-themed content slides.
"""
import zipfile, html, datetime, os

EMU = 914400                      # EMU per inch
W, H = 12192000, 6858000          # 16:9 slide (13.333 x 7.5 in)

# ---- palette (hex, no #) — austere academic light theme ------------------
BG     = "F6F4EE"   # warm paper background
CARD   = "EFECE3"
INK    = "1B1B22"   # near-black ink (titles, emphasis)
DIM    = "3F3F4A"   # body text
FAINT  = "8A8A96"   # footer / captions
ACCENT = "8A1524"   # scholarly crimson (kicker, rule)
SLATE  = "2F4B6E"   # secondary figure colour
# legacy aliases kept so existing references resolve
TEAL = ACCENT
BLUE = SLATE
VIOL = "6B6B76"
AMB  = "B08322"

def esc(t): return html.escape(str(t), quote=True)

# ---- slide content model -------------------------------------------------
# each slide: (kicker, title, [bullets]) ; bullets may be "" for spacing
SLIDES = [
    ("MULTI-AGENT CLINICAL REASONING  ·  RESEARCH SEMINAR",
     "MedJar: Consensus Diagnosis by Debating Specialist Agents",
     ["Persona-conditioned language-model specialists reason independently over a",
      "patient case, ground every claim in retrieved literature, and are driven toward",
      "a calibrated, auditable diagnosis through structured debate.",
      "",
      "Radiologist   ·   Cardiologist   ·   Oncologist   ·   extensible ensemble",
      "Assistive   ·   human-in-the-loop   ·   not an autonomous diagnostic device"]),
    ("THE PROBLEM",
     "Complex diagnosis fails for structural reasons",
     ["~1 in 20 adults hit a diagnostic error — concentrated in complex cases",
      "Anchoring bias & premature closure shut down the differential early",
      "Specialty silos: cardiologist & oncologist rarely reason together",
      "Guidelines go stale; a lone LLM asserts false facts fluently",
      "A single 'expert' model collapses the field into one distribution"]),
    ("CORE INSIGHT",
     "Disagreeing experts, forced to reconcile evidence",
     ["No single mind holds the whole of medicine",
      "Debate  >  Vote     — use the reasons, not just the answers",
      "Disagreement = Signal — it drives retrieval & escalation",
      "Ground everything   — no clinical claim without a citation"]),
    ("SYSTEM ARCHITECTURE",
     "Six layers, one control loop",
     ["0 · Intake — case files -> de-identification -> normalization",
      "1 · Representation — multimodal encoders -> Case Context Object (CCO)",
      "2 · Knowledge / RAG — hybrid retrieval, per-specialty scopes",
      "3 · Reasoning — the debate loop (specialists + orchestrator)",
      "4 · Consensus & Calibration — weighting, uncertainty, red-flags",
      "5 · Reporting — unified report + provenance + replayable audit log"]),
    ("THE AGENT ENSEMBLE",
     "Each specialist = <persona, tools, retrieval scope>",
     ["Radiologist — morphology -> localization -> imaging differential",
      "Cardiologist — rhythm, ischemia, hemodynamics, structure",
      "Oncologist — tissue of origin, staging, biomarkers",
      "Generalist — guards the 'whole patient'",
      "Scoped retrieval preserves diversity; plug-in registry for new specialties"]),
    ("REASONING CONTRACT",
     "Every turn is structured, never free prose",
     ["Agents return: differential[] with likelihood + cited evidence",
      "supporting_evidence / refuting_evidence -> citation_id",
      "discriminating_test — what most changes the probabilities",
      "red_flags[], calibrated confidence, requests[] (retrieve / ask-human)",
      "Groundedness verifier rejects ungrounded claims before the debate"]),
    ("KNOWLEDGE GROUNDING · RAG",
     "Hybrid retrieval -> re-rank -> cite",
     ["Dense (vector, cosine) + Sparse (BM25 exact terms, drugs, genes)",
      "Reciprocal Rank Fusion:  RRF(d) = Sum 1 / (k + rank_r(d)),  k ~ 60",
      "Cross-encoder re-ranking for precision on top-N",
      "NLI groundedness check; provenance -> Evidence Ledger",
      "Versioned corpus + ICD-10 / SNOMED CT / LOINC / RxNorm"]),
    ("THE DEBATE PROTOCOL",
     "Propose -> Critique -> Rebut -> Converge",
     ["1 Propose — no cross-talk; independent differentials prevent anchoring",
      "2 Critique — anonymized, adversarial, grounded attacks",
      "3 Rebut — revise; disagreement triggers targeted retrieval",
      "4 Converge — aggregate, loop, or escalate to a human",
      "Red-flag override: a minority can't-miss dx forces escalation"]),
    ("CONSENSUS MATHEMATICS",
     "Confidence-weighted, evidence-adjusted aggregation",
     ["Ensemble score:  S(h) = Sum w_i(h) c_i p_i(h) / Sum w_i(h) c_i",
      "w_i(h): soft specialty weight   c_i: calibrated confidence",
      "Disagreement (weighted variance) D-bar is the control signal",
      "Evidence adjust:  S*(h) = sigma( a·logit S(h) + b·E(h) )",
      "Stop when: D-bar <= t_agree  |  r = R_max  |  red-flag > t_flag"]),
    ("ORCHESTRATION · CHIEF-OF-SERVICE",
     "A deterministic controller convenes the room",
     ["Allocates turns & anonymizes identities during critique",
      "Enforces the contract; rejects malformed / ungrounded turns",
      "Computes D-bar, evidence scores, applies the stopping rule",
      "Manages the Evidence Ledger & immutable audit log",
      "Deterministic (not free-form LLM) -> predictable, testable, auditable"]),
    ("CONTROL FLOW",
     "The state machine",
     ["INTAKE -> PROPOSE -> CRITIQUE -> REBUT -> ASSESS",
      "ASSESS: converged        -> CONSENSUS -> REPORT",
      "ASSESS: not converged    -> loop PROPOSE (while r < R_max)",
      "ASSESS: red-flag / R_max  -> ESCALATE to human + full transcript",
      "Bounded compute; every transition logged and replayable"]),
    ("MULTIMODAL INTAKE",
     "Everything normalizes into the CCO",
     ["Structured EHR (FHIR/HL7) -> labs, meds, problems (coded)",
      "Clinical notes -> de-id, section parse, negation extraction",
      "Imaging (DICOM) -> vision findings; raw pixels stay in enclave",
      "Pathology, genomics (VCF), ECG/waveform features",
      "De-identification at the boundary; reasoning never sees identifiers"]),
    ("THE UNIFIED DIAGNOSTIC REPORT",
     "Leads with uncertainty, not a bare answer",
     ["Ranked differential: calibrated S*(h) + cited for/against evidence",
      "Discriminating next test per hypothesis",
      "Red-flag panel: excluded / needs work-up",
      "Points of disagreement — never hidden",
      "Confidence & status (converged vs escalated) + full audit trail"]),
    ("WORKED CASE (synthetic)",
     "58 y/o: dyspnea, weight loss, RUL nodule, up-troponin, effusion",
     ["Radiologist: spiculated nodule -> primary lung malignancy; PET-CT+biopsy",
      "Cardiologist: up-troponin + effusion -> exclude ACS & tamponade",
      "Oncologist: malignant effusion would upstage — needs cytology",
      "Resolves: tissue + effusion cytology are the discriminating tests",
      "RED-FLAG: tamponade -> escalate with explicit open question"]),
    ("EVALUATION",
     "Judged as decision-support, not a quiz-taker",
     ["Accuracy: Top-1 / Top-3 differential hit rate vs gold diagnosis",
      "Calibration: ECE, Brier score, reliability diagrams",
      "Safety: can't-miss recall + FALSE-REASSURANCE rate (primary endpoint)",
      "Groundedness: % of claims entailed by their citation",
      "Ablations: single vs ensemble, vote vs debate, +/- RAG; silent trial"]),
    ("SAFETY · ETHICS · REGULATORY",
     "Assistive by design — the clinician decides",
     ["Mandatory human sign-off before any recommendation informs care",
      "Uncertainty & red-flags escalate rather than closing the case",
      "HIPAA/GDPR de-id, PHI enclave, encryption, full access audit",
      "Likely SaMD (FDA) / MDR (EU); follows Good ML Practice",
      "Bias & equity: stratified corpus, per-subgroup calibration monitoring"]),
    ("LIMITATIONS",
     "Where it can fail — and the mitigation",
     ["Garbage-in case files -> escalation gate (can't order missing exam)",
      "Correlated errors -> heterogeneous models + devil's-advocate + RAG",
      "Corpus staleness -> versioned, evidence-graded curation",
      "Persuasive-but-wrong -> evidence-weighted, not rhetoric-weighted",
      "Automation bias -> lead with uncertainty; compute -> bounded triage mode"]),
    ("ROADMAP & TAKEAWAY",
     "From disagreeing experts to one grounded, auditable report",
     ["Phase 0: 3 agents, text cases, retrospective validation",
      "Phase 1: multimodal + calibration + groundedness verifier",
      "Phase 2: prospective silent trial (read-only)",
      "Phase 3-4: regulated pilot -> scale specialties",
      "Grounded · Transparent · Calibrated · Safe · Auditable"]),
]

# ---- XML builders --------------------------------------------------------
def solid(hexc):  return f'<a:solidFill><a:srgbClr val="{hexc}"/></a:solidFill>'

def run(text, size, color, bold=False, mono=False, serif=False):
    face = "Consolas" if mono else ("Georgia" if serif else "Calibri")
    b = ' b="1"' if bold else ''
    return (f'<a:r><a:rPr lang="en-US" sz="{size}"{b} dirty="0">'
            f'{solid(color)}<a:latin typeface="{face}"/></a:rPr>'
            f'<a:t>{esc(text)}</a:t></a:r>')

def para(runs_xml, bullet=False, color=DIM, size=1600, spc=600):
    if bullet:
        pr = (f'<a:pPr marL="342900" indent="-342900"><a:spcBef><a:spcPts val="{spc}"/></a:spcBef>'
              f'<a:buClr><a:srgbClr val="{ACCENT}"/></a:buClr>'
              f'<a:buFont typeface="Arial"/><a:buChar char="&#8211;"/></a:pPr>')
    else:
        pr = f'<a:pPr><a:spcBef><a:spcPts val="{spc}"/></a:spcBef></a:pPr>'
    return f'<a:p>{pr}{runs_xml}</a:p>'

def txbody(paras):  # wrap paragraphs in a txBody
    return ('<p:txBody><a:bodyPr wrap="square" rtlCol="0"><a:normAutofit/></a:bodyPr>'
            '<a:lstStyle/>' + ''.join(paras) + '</p:txBody>')

def shape(sid, name, x, y, cx, cy, body):
    return (f'<p:sp><p:nvSpPr><p:cNvPr id="{sid}" name="{esc(name)}"/>'
            f'<p:cNvSpPr><a:spLocks noGrp="1"/></p:cNvSpPr><p:nvPr/></p:nvSpPr>'
            f'<p:spPr><a:xfrm><a:off x="{x}" y="{y}"/><a:ext cx="{cx}" cy="{cy}"/></a:xfrm>'
            f'<a:prstGeom prst="rect"><a:avLst/></a:prstGeom></p:spPr>{body}</p:sp>')

def rect(sid, name, x, y, cx, cy, fill, line=None):
    ln = (f'<a:ln w="12700">{solid(line)}</a:ln>') if line else '<a:ln><a:noFill/></a:ln>'
    return (f'<p:sp><p:nvSpPr><p:cNvPr id="{sid}" name="{esc(name)}"/>'
            f'<p:cNvSpPr/><p:nvPr/></p:nvSpPr>'
            f'<p:spPr><a:xfrm><a:off x="{x}" y="{y}"/><a:ext cx="{cx}" cy="{cy}"/></a:xfrm>'
            f'<a:prstGeom prst="roundRect"><a:avLst><a:gd name="adj" fmla="val 6000"/></a:avLst></a:prstGeom>'
            f'{solid(fill)}{ln}</p:spPr>'
            f'<p:txBody><a:bodyPr/><a:lstStyle/><a:p/></p:txBody></p:sp>')

def slide_xml(idx, kicker, title, bullets):
    is_title = (idx == 0)
    shapes = []
    sid = 10
    # background
    bg = f'<p:bg><p:bgPr>{solid(BG)}<a:effectLst/></p:bgPr></p:bg>'
    # thin crimson rule under the header region
    shapes.append(rect(sid, "rule", 640000, 1030000, 620000, 34000, ACCENT)); sid+=1
    # kicker (running section label)
    shapes.append(shape(sid, "kicker", 640000, 540000, 10000000, 460000,
        txbody([para(run(kicker, 1150, ACCENT, bold=True, mono=True), size=1150, spc=0)]))); sid+=1
    # title (serif)
    tsize = 5000 if is_title else 3000
    shapes.append(shape(sid, "title", 630000, 1120000 if not is_title else 1600000,
        10800000, 1500000 if is_title else 1200000,
        txbody([para(run(title, tsize, INK, bold=True, serif=True), size=0)]))); sid+=1
    # body
    paras = []
    for b in bullets:
        if b == "":
            paras.append(para('', size=800, spc=200))
        else:
            is_bullet = not is_title
            paras.append(para(run(b, 1600 if is_title else 1500, DIM, serif=True),
                              bullet=is_bullet, spc=760))
    by = 2900000 if is_title else 2650000
    shapes.append(shape(sid, "body", 700000, by, 10600000, 3400000, txbody(paras))); sid+=1
    # footer
    shapes.append(shape(sid, "footer", 640000, 6420000, 10000000, 360000,
        txbody([para(run(f"MedJar   ·   {idx+1:02d} / {len(SLIDES)}   ·   assistive decision-support, not an autonomous device",
                         950, FAINT, mono=True), size=0)]))); sid+=1

    return ('<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
            '<p:sld xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main" '
            'xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships" '
            'xmlns:p="http://schemas.openxmlformats.org/presentationml/2006/main">'
            f'<p:cSld>{bg}<p:spTree>'
            '<p:nvGrpSpPr><p:cNvPr id="1" name=""/><p:cNvGrpSpPr/><p:nvPr/></p:nvGrpSpPr>'
            '<p:grpSpPr><a:xfrm><a:off x="0" y="0"/><a:ext cx="0" cy="0"/>'
            '<a:chOff x="0" y="0"/><a:chExt cx="0" cy="0"/></a:xfrm></p:grpSpPr>'
            + ''.join(shapes) +
            '</p:spTree></p:cSld><p:clrMapOvr><a:overrideClrMapping '
            'bg1="lt1" tx1="dk1" bg2="lt2" tx2="dk2" accent1="accent1" accent2="accent2" '
            'accent3="accent3" accent4="accent4" accent5="accent5" accent6="accent6" '
            'hlink="hlink" folHlink="folHlink"/></p:clrMapOvr></p:sld>')

# ---- static parts --------------------------------------------------------
THEME = ('<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
 '<a:theme xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main" name="MedJar">'
 '<a:themeElements><a:clrScheme name="MedJar">'
 '<a:dk1><a:srgbClr val="070B14"/></a:dk1><a:lt1><a:srgbClr val="E9F1FF"/></a:lt1>'
 '<a:dk2><a:srgbClr val="101C33"/></a:dk2><a:lt2><a:srgbClr val="9FB2CF"/></a:lt2>'
 '<a:accent1><a:srgbClr val="2FE0C8"/></a:accent1><a:accent2><a:srgbClr val="4C8DFF"/></a:accent2>'
 '<a:accent3><a:srgbClr val="9B7BFF"/></a:accent3><a:accent4><a:srgbClr val="FFB547"/></a:accent4>'
 '<a:accent5><a:srgbClr val="42D98A"/></a:accent5><a:accent6><a:srgbClr val="FF5D6C"/></a:accent6>'
 '<a:hlink><a:srgbClr val="4C8DFF"/></a:hlink><a:folHlink><a:srgbClr val="9B7BFF"/></a:folHlink>'
 '</a:clrScheme><a:fontScheme name="MedJar">'
 '<a:majorFont><a:latin typeface="Segoe UI"/><a:ea typeface=""/><a:cs typeface=""/></a:majorFont>'
 '<a:minorFont><a:latin typeface="Segoe UI"/><a:ea typeface=""/><a:cs typeface=""/></a:minorFont>'
 '</a:fontScheme><a:fmtScheme name="MedJar">'
 '<a:fillStyleLst><a:solidFill><a:schemeClr val="phClr"/></a:solidFill>'
 '<a:solidFill><a:schemeClr val="phClr"/></a:solidFill>'
 '<a:solidFill><a:schemeClr val="phClr"/></a:solidFill></a:fillStyleLst>'
 '<a:lnStyleLst><a:ln w="6350"><a:solidFill><a:schemeClr val="phClr"/></a:solidFill></a:ln>'
 '<a:ln w="12700"><a:solidFill><a:schemeClr val="phClr"/></a:solidFill></a:ln>'
 '<a:ln w="19050"><a:solidFill><a:schemeClr val="phClr"/></a:solidFill></a:ln></a:lnStyleLst>'
 '<a:effectStyleLst><a:effectStyle><a:effectLst/></a:effectStyle>'
 '<a:effectStyle><a:effectLst/></a:effectStyle>'
 '<a:effectStyle><a:effectLst/></a:effectStyle></a:effectStyleLst>'
 '<a:bgFillStyleLst><a:solidFill><a:schemeClr val="phClr"/></a:solidFill>'
 '<a:solidFill><a:schemeClr val="phClr"/></a:solidFill>'
 '<a:solidFill><a:schemeClr val="phClr"/></a:solidFill></a:bgFillStyleLst>'
 '</a:fmtScheme></a:themeElements></a:theme>')

SLIDE_LAYOUT = ('<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
 '<p:sldLayout xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main" '
 'xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships" '
 'xmlns:p="http://schemas.openxmlformats.org/presentationml/2006/main" type="blank" preserve="1">'
 '<p:cSld name="Blank"><p:spTree><p:nvGrpSpPr><p:cNvPr id="1" name=""/><p:cNvGrpSpPr/><p:nvPr/>'
 '</p:nvGrpSpPr><p:grpSpPr><a:xfrm><a:off x="0" y="0"/><a:ext cx="0" cy="0"/>'
 '<a:chOff x="0" y="0"/><a:chExt cx="0" cy="0"/></a:xfrm></p:grpSpPr></p:spTree></p:cSld>'
 '<p:clrMapOvr><a:masterClrMapping/></p:clrMapOvr></p:sldLayout>')

SLIDE_MASTER = ('<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
 '<p:sldMaster xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main" '
 'xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships" '
 'xmlns:p="http://schemas.openxmlformats.org/presentationml/2006/main">'
 f'<p:cSld><p:bg><p:bgPr>{solid(BG)}<a:effectLst/></p:bgPr></p:bg>'
 '<p:spTree><p:nvGrpSpPr><p:cNvPr id="1" name=""/><p:cNvGrpSpPr/><p:nvPr/></p:nvGrpSpPr>'
 '<p:grpSpPr><a:xfrm><a:off x="0" y="0"/><a:ext cx="0" cy="0"/>'
 '<a:chOff x="0" y="0"/><a:chExt cx="0" cy="0"/></a:xfrm></p:grpSpPr></p:spTree></p:cSld>'
 '<p:clrMap bg1="dk1" tx1="lt1" bg2="dk2" tx2="lt2" accent1="accent1" accent2="accent2" '
 'accent3="accent3" accent4="accent4" accent5="accent5" accent6="accent6" hlink="hlink" '
 'folHlink="folHlink"/><p:sldLayoutIdLst><p:sldLayoutId id="2147483649" r:id="rId1"/>'
 '</p:sldLayoutIdLst></p:sldMaster>')

def presentation_xml(n):
    sldids = ''.join(f'<p:sldId id="{256+i}" r:id="rId{i+2}"/>' for i in range(n))
    return ('<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
     '<p:presentation xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main" '
     'xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships" '
     'xmlns:p="http://schemas.openxmlformats.org/presentationml/2006/main">'
     '<p:sldMasterIdLst><p:sldMasterId id="2147483648" r:id="rId1"/></p:sldMasterIdLst>'
     f'<p:sldIdLst>{sldids}</p:sldIdLst>'
     f'<p:sldSz cx="{W}" cy="{H}" type="screen16x9"/>'
     '<p:notesSz cx="6858000" cy="9144000"/></p:presentation>')

def presentation_rels(n):
    rels = ['<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/slideMaster" Target="slideMasters/slideMaster1.xml"/>']
    for i in range(n):
        rels.append(f'<Relationship Id="rId{i+2}" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/slide" Target="slides/slide{i+1}.xml"/>')
    rels.append(f'<Relationship Id="rId{n+2}" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/theme" Target="theme/theme1.xml"/>')
    return ('<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
            '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
            + ''.join(rels) + '</Relationships>')

def content_types(n):
    over = ''.join(f'<Override PartName="/ppt/slides/slide{i+1}.xml" ContentType="application/vnd.openxmlformats-officedocument.presentationml.slide+xml"/>' for i in range(n))
    return ('<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
     '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">'
     '<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>'
     '<Default Extension="xml" ContentType="application/xml"/>'
     '<Override PartName="/ppt/presentation.xml" ContentType="application/vnd.openxmlformats-officedocument.presentationml.presentation.main+xml"/>'
     '<Override PartName="/ppt/slideMasters/slideMaster1.xml" ContentType="application/vnd.openxmlformats-officedocument.presentationml.slideMaster+xml"/>'
     '<Override PartName="/ppt/slideLayouts/slideLayout1.xml" ContentType="application/vnd.openxmlformats-officedocument.presentationml.slideLayout+xml"/>'
     '<Override PartName="/ppt/theme/theme1.xml" ContentType="application/vnd.openxmlformats-officedocument.theme+xml"/>'
     '<Override PartName="/docProps/core.xml" ContentType="application/vnd.openxmlformats-package.core-properties+xml"/>'
     '<Override PartName="/docProps/app.xml" ContentType="application/vnd.openxmlformats-officedocument.extended-properties+xml"/>'
     + over + '</Types>')

ROOT_RELS = ('<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
 '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
 '<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="ppt/presentation.xml"/>'
 '<Relationship Id="rId2" Type="http://schemas.openxmlformats.org/package/2006/relationships/metadata/core-properties" Target="docProps/core.xml"/>'
 '<Relationship Id="rId3" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/extended-properties" Target="docProps/app.xml"/>'
 '</Relationships>')

MASTER_RELS = ('<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
 '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
 '<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/slideLayout" Target="../slideLayouts/slideLayout1.xml"/>'
 '<Relationship Id="rId2" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/theme" Target="../theme/theme1.xml"/>'
 '</Relationships>')

LAYOUT_RELS = ('<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
 '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
 '<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/slideMaster" Target="../slideMasters/slideMaster1.xml"/>'
 '</Relationships>')

def slide_rels():
    return ('<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
     '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
     '<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/slideLayout" Target="../slideLayouts/slideLayout1.xml"/>'
     '</Relationships>')

now = datetime.datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")
CORE = ('<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
 '<cp:coreProperties xmlns:cp="http://schemas.openxmlformats.org/package/2006/metadata/core-properties" '
 'xmlns:dc="http://purl.org/dc/elements/1.1/" xmlns:dcterms="http://purl.org/dc/terms/" '
 'xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">'
 '<dc:title>MedJar — Multi-Agent Consensus for Medical Diagnosis</dc:title>'
 '<dc:creator>MedJar</dc:creator><cp:lastModifiedBy>MedJar</cp:lastModifiedBy>'
 f'<dcterms:created xsi:type="dcterms:W3CDTF">{now}</dcterms:created>'
 f'<dcterms:modified xsi:type="dcterms:W3CDTF">{now}</dcterms:modified></cp:coreProperties>')

APP = ('<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
 '<Properties xmlns="http://schemas.openxmlformats.org/officeDocument/2006/extended-properties" '
 'xmlns:vt="http://schemas.openxmlformats.org/officeDocument/2006/docPropsVTypes">'
 '<Application>MedJar Deck Generator</Application><Company>MedJar</Company>'
 f'<Slides>{len(SLIDES)}</Slides></Properties>')

# ---- assemble the package ------------------------------------------------
def build(out="MedJar.pptx"):
    n = len(SLIDES)
    with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as z:
        z.writestr("[Content_Types].xml", content_types(n))
        z.writestr("_rels/.rels", ROOT_RELS)
        z.writestr("docProps/core.xml", CORE)
        z.writestr("docProps/app.xml", APP)
        z.writestr("ppt/presentation.xml", presentation_xml(n))
        z.writestr("ppt/_rels/presentation.xml.rels", presentation_rels(n))
        z.writestr("ppt/theme/theme1.xml", THEME)
        z.writestr("ppt/slideMasters/slideMaster1.xml", SLIDE_MASTER)
        z.writestr("ppt/slideMasters/_rels/slideMaster1.xml.rels", MASTER_RELS)
        z.writestr("ppt/slideLayouts/slideLayout1.xml", SLIDE_LAYOUT)
        z.writestr("ppt/slideLayouts/_rels/slideLayout1.xml.rels", LAYOUT_RELS)
        for i, (k, t, b) in enumerate(SLIDES):
            z.writestr(f"ppt/slides/slide{i+1}.xml", slide_xml(i, k, t, b))
            z.writestr(f"ppt/slides/_rels/slide{i+1}.xml.rels", slide_rels())
    print(f"Wrote {out} with {n} slides ({os.path.getsize(out)} bytes)")

if __name__ == "__main__":
    build(os.path.join(os.path.dirname(__file__), "MedJar.pptx"))

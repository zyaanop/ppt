#!/usr/bin/env python3
"""
build_deck.py — assemble presentation.html from the generated figures.

The figures in figures/*.svg are inlined into a single self-contained HTML file,
so the deck can be opened anywhere with no external assets and no network. Run
after regenerating the figures:

    cd figures && python3 make_figures.py
    cd ..      && python3 build_deck.py
"""
from __future__ import annotations

import json
import os
import re
from typing import Dict, List, Optional, Sequence

HERE = os.path.dirname(os.path.abspath(__file__))
FIGDIR = os.path.join(HERE, "figures")
TRACE = os.path.join(HERE, "prototype", "output", "trace.json")
OUTFILE = os.path.join(HERE, "presentation.html")

FIGS = {
    "arch": "fig01_architecture", "flow": "fig02_workflow",
    "rag": "fig03_rag_pipeline", "seq": "fig04_debate_sequence",
    "fsm": "fig05_state_machine", "cons": "fig06_consensus_dataflow",
    "cco": "fig07_cco", "report": "fig08_report_anatomy",
    "deploy": "fig09_deployment", "conv": "fig10_convergence",
    "diverge": "fig11_divergence", "diff": "fig12_differential",
    "calib": "fig13_calibration", "abl": "fig14_ablation",
}


# --------------------------------------------------------------------------
def load_svg(key: str) -> str:
    """Inline an SVG, namespacing its marker ids so multiple figures coexist."""
    name = FIGS[key]
    with open(os.path.join(FIGDIR, name + ".svg"), "r", encoding="utf-8") as f:
        text = f.read()
    # duplicate ids across inlined SVGs would collide in one document
    text = re.sub(r'id="arrow-(\w+)"', lambda m: f'id="ar-{m.group(1)}-{key}"', text)
    text = re.sub(r'url\(#arrow-(\w+)\)',
                  lambda m: f'url(#ar-{m.group(1)}-{key})', text)
    # drop fixed width/height from the root so CSS controls scaling
    m = re.match(r"(<svg[^>]*>)", text)
    if m:
        root = m.group(1)
        text = re.sub(r'\s(?:width|height)="[^"]*"', "", root) + text[len(root):]
    return text


# --------------------------------------------------------------------------
CSS = """
:root{
  --paper:#fbfaf8; --ink:#1b1b22; --ink2:#3f3f4a; --ink3:#6b6b76;
  --faint:#a9a69c; --rule:#d8d4c8; --accent:#8a1524; --slate:#2f4b6e;
  --green:#2f6b3f; --ochre:#b08322;
  --serif:'Iowan Old Style','Palatino Linotype',Palatino,'Book Antiqua',Georgia,serif;
  --sans:'Helvetica Neue',Helvetica,Arial,system-ui,sans-serif;
  --mono:'SF Mono',ui-monospace,'Cascadia Mono',Menlo,Consolas,monospace;
}
*{margin:0;padding:0;box-sizing:border-box}
html,body{height:100%;overflow:hidden;background:#c9c6bd;color:var(--ink);font-family:var(--sans)}
#deck{position:relative;height:100%;width:100%}
.slide{position:absolute;inset:0;display:none;flex-direction:column;background:var(--paper);
  padding:5.6vh 5.2vw 5.4vh;opacity:0;transform:translateY(8px);
  transition:opacity .34s ease,transform .34s ease}
.slide.active{display:flex;opacity:1;transform:none}
.rh{display:flex;justify-content:space-between;align-items:baseline;font-size:11.5px;
  letter-spacing:.04em;color:var(--ink3);border-bottom:1px solid var(--rule);
  padding-bottom:7px;margin-bottom:2.4vh;flex:none}
.rh .sec{text-transform:uppercase;letter-spacing:.14em;font-size:10.5px;
  color:var(--accent);font-weight:700}
.rh .pg{font-variant-numeric:tabular-nums;color:var(--faint)}
.body{flex:1;display:flex;flex-direction:column;justify-content:center;min-height:0}
h1{font-family:var(--serif);font-weight:600;font-size:clamp(26px,3.9vw,52px);line-height:1.07}
h2{font-family:var(--serif);font-weight:600;font-size:clamp(21px,2.55vw,35px);line-height:1.12;
  margin-bottom:.1em}
h2:after{content:"";display:block;width:58px;height:3px;background:var(--accent);margin-top:.38em}
h3{font-size:clamp(12px,1.16vw,16px);font-weight:700;color:var(--ink);letter-spacing:.01em}
p,li{font-family:var(--serif);font-size:clamp(13px,1.24vw,19px);line-height:1.5;color:var(--ink2)}
.sub{font-family:var(--serif);font-style:italic;color:var(--ink3)}
.small{font-size:clamp(11px,1.03vw,15px)}
.tiny{font-size:clamp(10px,.92vw,13px)}
strong{font-weight:700;color:var(--ink)}
.mono{font-family:var(--mono);font-size:.92em}
.accent{color:var(--accent)}.green{color:var(--green)}
.lead{max-width:66ch}
.cols{display:grid;gap:2.4vw}
.c2{grid-template-columns:1fr 1fr}
.c2f{grid-template-columns:1.5fr 1fr}
.c3{grid-template-columns:repeat(3,1fr)}
.c4{grid-template-columns:repeat(4,1fr)}
ul.pts{list-style:none}
ul.pts>li{position:relative;padding-left:1.35em;margin:.46em 0}
ul.pts>li:before{content:"\\2014";position:absolute;left:0;color:var(--accent);font-family:var(--sans)}
ol.num{list-style:none;counter-reset:c}
ol.num>li{counter-increment:c;position:relative;padding-left:2.2em;margin:.55em 0}
ol.num>li:before{content:counter(c);position:absolute;left:0;top:.02em;width:1.45em;height:1.45em;
  border:1.5px solid var(--accent);color:var(--accent);border-radius:50%;display:grid;
  place-items:center;font-family:var(--sans);font-weight:700;font-size:.6em}
.block{border:1px solid var(--rule);background:#f4f2ec;padding:14px 16px}
.block.al{border-left:3px solid var(--accent)}
.block.gl{border-left:3px solid var(--green)}
table{width:100%;border-collapse:collapse;font-family:var(--sans)}
th{text-align:left;font-size:10.5px;letter-spacing:.06em;text-transform:uppercase;
  color:var(--accent);border-bottom:1.5px solid var(--ink);padding:7px 10px;font-weight:700}
td{font-family:var(--serif);font-size:clamp(11px,1.06vw,16px);color:var(--ink2);
  border-bottom:1px solid var(--rule);padding:7px 10px}
tr:last-child td{border-bottom:none}
td.num{font-family:var(--mono);font-size:.92em}
.figwrap{flex:1;display:flex;align-items:center;justify-content:center;min-height:0;margin:.4vh 0}
.figwrap svg{max-width:100%;max-height:100%;width:auto;height:auto;
  border:1px solid var(--rule);background:#fff;padding:6px}
.figwrap.big svg{max-height:70vh}
.cap{flex:none;font-size:clamp(10.5px,1vw,13.5px);color:var(--ink3);margin-top:1vh;
  text-align:center;font-family:var(--sans);line-height:1.45}
.cap b{color:var(--ink)}
.illus{font-size:9.5px;letter-spacing:.12em;text-transform:uppercase;color:var(--faint)}
.eq{font-family:var(--serif);font-size:clamp(15px,1.8vw,25px);color:var(--ink);
  display:flex;align-items:center;gap:.3em;flex-wrap:wrap}
.frac{display:inline-flex;flex-direction:column;text-align:center;margin:0 .12em}
.frac .n{border-bottom:1.4px solid var(--ink);padding:0 .45em .04em}
.frac .d{padding:.04em .45em 0}
.eqlab{margin-left:auto;font-family:var(--sans);font-size:11px;color:var(--ink3)}
.divider{background:var(--ink)}
.divider .rh{color:#9a9aa4;border-color:#33333c}
.divider .rh .sec{color:#c98b95}
.divider .body{justify-content:center}
.divider .no{font-family:var(--serif);font-size:clamp(52px,10vw,128px);line-height:.9;
  color:var(--accent);font-weight:600}
.divider h1{color:var(--paper);margin-top:.08em}
.divider .sub{color:#b9b9c2}
.title .kick{font-size:12px;letter-spacing:.2em;text-transform:uppercase;color:var(--accent);
  font-weight:700;margin-bottom:20px}
.title h1{font-size:clamp(28px,4.6vw,62px);max-width:22ch}
.rule{width:84px;height:4px;background:var(--accent);margin:24px 0}
.byline{margin-top:30px;font-size:13px;color:var(--ink2);line-height:1.7}
.byline .af{color:var(--ink3);font-size:12px}
.progress{position:fixed;top:0;left:0;height:3px;background:var(--accent);z-index:20;
  transition:width .28s ease}
/* per-slide dwell indicator, only advances while auto-play is running */
.dwell{position:fixed;top:3px;left:0;height:2px;width:0;z-index:19;
  background:rgba(138,21,36,.32)}
.chrome{position:fixed;bottom:12px;right:20px;z-index:20;font-family:var(--mono);
  font-size:11px;color:var(--ink3)}
.hint{position:fixed;bottom:12px;left:20px;z-index:20;font-size:10.5px;color:var(--faint)}
.btn{cursor:pointer;user-select:none;border:1px solid var(--rule);background:var(--paper);
  color:var(--ink2);padding:3px 8px;border-radius:3px;font-family:var(--sans);font-size:10.5px}
.btn:hover{border-color:var(--accent);color:var(--accent)}
.dots{position:fixed;bottom:13px;left:50%;transform:translateX(-50%);z-index:20;
  display:flex;gap:5px}
.dots i{width:5px;height:5px;border-radius:50%;background:var(--rule);cursor:pointer;
  transition:.22s}
.dots i.on{background:var(--accent);width:14px;border-radius:3px}
@media(max-width:900px){.c2,.c2f,.c3,.c4{grid-template-columns:1fr}}
"""

JS = """
(function(){
  const slides=[...document.querySelectorAll('.slide')], total=slides.length;
  const pg=document.getElementById('progress'), ct=document.getElementById('counter');
  const dw=document.getElementById('dots'), ab=document.getElementById('autobtn');
  let cur=0, auto=false, timer=null, relaunch=null;
  slides.forEach((_,i)=>{const d=document.createElement('i');d.onclick=()=>go(i);dw.appendChild(d);});
  const dots=[...dw.children];
  function render(){
    slides.forEach((s,i)=>{
      s.classList.toggle('active',i===cur);
      const p=s.querySelector('.rh .pg'); if(p) p.textContent=(i+1)+' / '+total;
    });
    pg.style.width=((cur+1)/total*100)+'%';
    ct.textContent=(cur+1)+' / '+total;
    dots.forEach((d,i)=>d.classList.toggle('on',i===cur));
    location.hash='s'+(cur+1);
  }
  function go(i){cur=Math.max(0,Math.min(total-1,i));render();}
  const next=()=>{ if(cur<total-1) go(cur+1); else stop(); };
  const prev=()=>go(cur-1);
  // Dwell time per slide, in the 20-30s band: long enough to actually read a
  // slide unattended. Denser slides get longer.
  const DWELL={divider:20000, figure:30000, normal:25000};
  function dwell(i){
    const s=slides[i];
    if(s.classList.contains('divider')||s.classList.contains('title')) return DWELL.divider;
    if(s.querySelector('.figwrap')) return DWELL.figure;
    return DWELL.normal;
  }
  const db=document.getElementById('dwell');
  function runBar(ms){
    db.style.transition='none'; db.style.width='0%';
    requestAnimationFrame(()=>{
      db.style.transition='width '+ms+'ms linear'; db.style.width='100%';
    });
  }
  function clearBar(){ db.style.transition='none'; db.style.width='0%'; }
  function sched(){clearTimeout(timer); if(!auto){clearBar();return;}
    if(cur===total-1){stop();return;}
    const ms=dwell(cur); runBar(ms);
    timer=setTimeout(()=>{next();sched();},ms);}
  function start(){auto=true;ab.textContent='Pause';ab.style.color='var(--accent)';sched();}
  function stop(){auto=false;ab.textContent='Auto';ab.style.color='';clearTimeout(timer);clearBar();}
  ab.onclick=()=>auto?stop():start();
  function pause(){if(auto){clearTimeout(timer);clearTimeout(relaunch);
    relaunch=setTimeout(()=>{if(auto)sched();},6000);}}
  document.addEventListener('keydown',e=>{
    if(['ArrowRight',' ','PageDown'].includes(e.key)){e.preventDefault();pause();next();}
    else if(['ArrowLeft','PageUp'].includes(e.key)){e.preventDefault();pause();prev();}
    else if(e.key==='Home')go(0); else if(e.key==='End')go(total-1);
    else if(e.key.toLowerCase()==='f'){document.fullscreenElement?
      document.exitFullscreen():document.documentElement.requestFullscreen?.();}
    else if(e.key.toLowerCase()==='a')auto?stop():start();
  });
  document.getElementById('deck').addEventListener('click',e=>{
    if(e.target.closest('.btn,.dots'))return; pause();
    (e.clientX/innerWidth>0.34)?next():prev();
  });
  let tx=0;
  addEventListener('touchstart',e=>tx=e.touches[0].clientX,{passive:true});
  addEventListener('touchend',e=>{const dx=e.changedTouches[0].clientX-tx;
    if(Math.abs(dx)>50){pause();dx<0?next():prev();}},{passive:true});
  const m=location.hash.match(/s(\\d+)/); if(m)cur=Math.min(total-1,Math.max(0,+m[1]-1));
  render();
})();
"""


# --------------------------------------------------------------------------
def rh(section: str) -> str:
    return f'<div class="rh"><span class="sec">{section}</span><span class="pg"></span></div>'


def slide(section: str, body: str, cls: str = "") -> str:
    return (f'<section class="slide {cls}">{rh(section)}'
            f'<div class="body">{body}</div></section>')


def title_slide() -> str:
    return ('<section class="slide title">'
            '<div class="body">'
            '<div class="kick">Multi-Agent Clinical Reasoning · Research Seminar</div>'
            '<h1>MedJar: Consensus Diagnosis by Debating Specialist Agents</h1>'
            '<div class="rule"></div>'
            '<p class="sub lead">Persona-conditioned language-model specialists reason '
            'independently over a patient case, ground every claim in retrieved '
            'literature, and are driven toward a calibrated, auditable diagnosis '
            'through structured debate.</p>'
            '<div class="byline"><div><strong>MedJar Working Group</strong></div>'
            '<div class="af">Clinical Machine Learning · Decision-Support Systems</div>'
            '<div class="af" style="margin-top:9px">Technical report and working '
            'prototype · assistive, human-in-the-loop · not an autonomous '
            'diagnostic device</div></div>'
            '</div></section>')


def divider(num: str, title: str, sub: str, part: str) -> str:
    return (f'<section class="slide divider">{rh(part)}'
            f'<div class="body"><div class="no">{num}</div><h1>{title}</h1>'
            f'<p class="sub">{sub}</p></div></section>')


def figure_slide(section: str, heading: str, figkey: str, caption: str,
                 big: bool = False) -> str:
    cls = "figwrap big" if big else "figwrap"
    return (f'<section class="slide">{rh(section)}'
            f'<div class="body" style="justify-content:flex-start">'
            f'<h2>{heading}</h2>'
            f'<div class="{cls}">{load_svg(figkey)}</div>'
            f'<div class="cap">{caption}</div>'
            f'</div></section>')


def figure_split(section: str, heading: str, figkey: str, caption: str,
                 points: Sequence[str]) -> str:
    li = "".join(f"<li>{p}</li>" for p in points)
    return (f'<section class="slide">{rh(section)}'
            f'<div class="body" style="justify-content:flex-start">'
            f'<h2>{heading}</h2>'
            f'<div class="cols c2f" style="flex:1;min-height:0;align-items:center">'
            f'<div style="display:flex;flex-direction:column;min-height:0;height:100%">'
            f'<div class="figwrap">{load_svg(figkey)}</div>'
            f'<div class="cap">{caption}</div></div>'
            f'<ul class="pts">{li}</ul>'
            f'</div></div></section>')


# --------------------------------------------------------------------------
def build() -> str:
    with open(TRACE, "r", encoding="utf-8") as f:
        tr = json.load(f)
    S = tr["summary"]
    cases = {c["case_id"]: c for c in tr["cases"]}

    d: List[str] = []
    d.append(title_slide())

    # ---- motivation ----
    d.append(slide("Motivation", (
        '<h2>Diagnostic error is a systems problem</h2>'
        '<p class="lead" style="margin:.5em 0 1em">An estimated <strong>5% of '
        'adults</strong> experience a diagnostic error in outpatient care each year, '
        'concentrated in complex presentations that cross specialty boundaries.</p>'
        '<div class="cols c2">'
        '<ul class="pts">'
        '<li><strong>Anchoring</strong> — an initial impression suppresses competing '
        'hypotheses.</li>'
        '<li><strong>Premature closure</strong> — the search ends once a plausible '
        'answer appears.</li></ul>'
        '<ul class="pts">'
        '<li><strong>Specialty siloing</strong> — the experts who would resolve the '
        'case never reason on it together.</li>'
        '<li><strong>Knowledge drift</strong> — guidelines change faster than anyone '
        'tracks them.</li></ul></div>'
        '<p class="lead sub" style="margin-top:1.3em">Medicine already has a '
        'countermeasure — the tumour board. What makes it work is not consensus but '
        '<strong>structured disagreement</strong>. Can that be made computational?</p>'
    )))

    d.append(slide("Motivation", (
        '<h2>Why a single model is insufficient</h2>'
        '<p class="lead" style="margin:.4em 0 1.1em">Conditioning one model on '
        '<em>“you are an expert physician”</em> collapses the diversity of clinical '
        'reasoning into a single distribution.</p>'
        '<div class="cols c3">'
        '<div class="block al"><h3>Correlated failure</h3><p class="small">One prior, '
        'one blind spot. No internal adversary to surface the missed diagnosis.</p></div>'
        '<div class="block al"><h3>Miscalibrated confidence</h3><p class="small">'
        'Self-consistent but wrong trajectories, asserted at high confidence.</p></div>'
        '<div class="block al"><h3>Unverifiable grounding</h3><p class="small">Claims '
        'not bound to a source cannot be checked, audited, or contested.</p></div></div>'
        '<p class="lead" style="margin-top:1.3em">Majority voting does not fix this: it '
        'discards <em>why</em> agents differ and systematically <strong>silences the '
        'minority can’t-miss diagnosis</strong> — the most consequential error mode in '
        'acute care.</p>'
    )))

    d.append(slide("Contributions", (
        '<h2>Contributions</h2>'
        '<ol class="num" style="margin-top:.6em">'
        '<li><strong>Specialist multi-agent formulation.</strong> Distinct reasoning '
        'priors with <em>private, specialty-scoped</em> retrieval, so the diversity '
        'debate consumes is preserved rather than averaged away.</li>'
        '<li><strong>A structured debate protocol</strong> operating on grounded '
        'reasons, converting disagreement into targeted retrieval.</li>'
        '<li><strong>A consensus formalism</strong> — confidence-weighted aggregation, '
        'evidence adjustment, and a disagreement metric driving an explicit stopping '
        'and escalation rule.</li>'
        '<li><strong>A competence-scoped critique rule</strong> which we show is '
        '<em>necessary</em>: without it, agents lacking domain priors vote down correct '
        'in-domain diagnoses.</li>'
        '<li><strong>A complete deterministic prototype</strong> and an evaluation '
        'protocol for the system as decision support — with negative results '
        'reported.</li></ol>'
    )))

    # ---- Part I ----
    d.append(divider("I", "System", "Architecture, the case representation, and the "
                     "end-to-end workflow.", "Part I"))
    d.append(figure_slide("System · Architecture", "Six layers, one control loop",
                          "arch",
                          "<b>Figure 1.</b> Stages 0–2 are deterministic "
                          "preprocessing; stage 3 hosts the debate and is the only "
                          "stochastic component; stages 4–5 are deterministic "
                          "aggregation and reporting."))
    d.append(figure_slide("System · Workflow", "The complete workflow, end to end",
                          "flow",
                          "<b>Figure 2.</b> Steps 1–16 across eight lanes. "
                          "De-identification happens in the intake lane — nothing "
                          "below the boundary carries an identifier. Agents retrieve "
                          "privately and never observe one another during proposal. "
                          "The debate loop (10–12) repeats while D̄ > τ_agree and "
                          "r &lt; R_max. Both dispositions end in clinician sign-off.",
                          big=True))
    d.append(figure_split("System · Representation", "Everything normalises into the CCO",
                          "cco",
                          "<b>Figure 3.</b> Six modalities, coded against ICD-10, "
                          "SNOMED CT, LOINC and RxNorm.",
                          ["One shared, coded representation for every agent.",
                           "De-identification at the boundary; <strong>raw pixels "
                           "never leave the enclave</strong>.",
                           "Explicit <strong>negations</strong> are carried, so agents "
                           "can distinguish <em>absent</em> from <em>not assessed</em> "
                           "— a distinction routinely lost when notes are flattened.",
                           "Swapping an encoder changes nothing downstream."]))

    # ---- Part II ----
    d.append(divider("II", "Method", "Grounding, the debate protocol, and the "
                     "consensus formalism.", "Part II"))
    d.append(figure_slide("Method · Grounding", "Hybrid retrieval, then a hard "
                          "grounding gate", "rag",
                          "<b>Figure 4.</b> Dense recall and BM25 exact-term matching "
                          "are merged by reciprocal rank fusion, re-ranked for "
                          "precision, then gated: a claim not entailed by its cited "
                          "passage is excluded from aggregation."))

    d.append(slide("Method · Agents", (
        '<h2>The specialist ensemble</h2>'
        '<p class="lead" style="margin:.4em 0 .9em">Each agent is a triple '
        '<span class="mono">⟨persona, tools, retrieval scope⟩</span>. Scoped retrieval '
        'keeps perspectives distinct — global retrieval would homogenise the ensemble.</p>'
        '<table><thead><tr><th>Agent</th><th>Reasoning prior</th>'
        '<th>Characteristic question</th></tr></thead><tbody>'
        '<tr><td><strong>Radiologist</strong></td><td>morphology → localisation → '
        'imaging differential</td><td class="sub">What does the image show, independent '
        'of the referral question?</td></tr>'
        '<tr><td><strong>Cardiologist</strong></td><td>exclude life-threatening cardiac '
        'aetiology first</td><td class="sub">Is there a cardiac cause or consequence we '
        'must not miss?</td></tr>'
        '<tr><td><strong>Oncologist</strong></td><td>tissue of origin, staging, '
        'biomarkers</td><td class="sub">Is this neoplastic, and what is the '
        'stage-defining evidence?</td></tr>'
        '<tr><td><strong>Generalist</strong></td><td>whole-patient coherence</td>'
        '<td class="sub">Does this explain the entire presentation?</td></tr>'
        '</tbody></table>'
        '<div class="block al" style="margin-top:1.2em"><p class="small">'
        '<strong>Reasoning contract.</strong> Every turn returns structured output — '
        'per-hypothesis likelihood, supporting and refuting claims bound to citation '
        'ids, the discriminating test, red flags, confidence — never free prose. '
        '<strong>Agents never abstain:</strong> an agent with no prior for a hypothesis '
        'registers a low cautionary floor, which counts in S(h) but not in D̄.</p></div>'
    )))

    d.append(figure_slide("Method · Debate", "Propose → critique → rebut → assess",
                          "seq",
                          "<b>Figure 5.</b> Proposal is isolated to prevent anchoring; "
                          "critique is anonymised; contested points seed targeted "
                          "re-retrieval. At least one critique round always runs — "
                          "coinciding impressions are still cross-examined. Labels "
                          "abridged from the prototype’s CASE-001 transcript."))

    d.append(slide("Method · Consensus", (
        '<h2>Consensus formalism</h2>'
        '<div style="margin:.5em 0 1em">'
        '<div class="eq">S(h) = <span class="frac"><span class="n">Σᵢ wᵢ(h)·cᵢ·pᵢ(h)'
        '</span><span class="d">Σᵢ wᵢ(h)·cᵢ</span></span>'
        '<span class="eqlab">(1) confidence- and competence-weighted mean</span></div>'
        '</div>'
        '<div style="margin:.9em 0">'
        '<div class="eq">S*(h) = σ( α·logit S(h) + β·E(h) )'
        '<span class="eqlab">(2) evidence adjustment</span></div></div>'
        '<div style="margin:.9em 0">'
        '<div class="eq">Disagree(h) = <span class="frac">'
        '<span class="n">Σ<sub>i∈𝒮</sub> wᵢcᵢ( pᵢ(h) − S(h) )²</span>'
        '<span class="d">Σ<sub>i∈𝒮</sub> wᵢcᵢ</span></span>'
        '<span class="eqlab">(3) weighted variance</span></div></div>'
        '<div class="cols c3" style="margin-top:1.1em">'
        '<div class="block"><h3>wᵢ(h) — soft MoE</h3><p class="small">1.00 in-domain, '
        '0.58–0.82 adjacent, 0.45 otherwise. Not a router: every agent votes on every '
        'hypothesis.</p></div>'
        '<div class="block"><h3>E(h) — evidence</h3><p class="small">Support minus '
        'refutation, weighted by evidence grade, recency and entailment.</p></div>'
        '<div class="block al"><h3>𝒮(h) — substantive only</h3><p class="small">Floors '
        'are excluded from (3): absence of an opinion is not dissent.</p></div></div>'
    )))

    d.append(figure_slide("Method · Consensus", "From agent opinions to S*(h) and D̄",
                          "cons",
                          "<b>Figure 6.</b> Values are the prototype’s actual round-0 "
                          "likelihoods for <em>primary lung malignancy</em> in "
                          "CASE-001. The cardiologist’s 0.17 is a cautionary floor, "
                          "not a considered dissent."))

    d.append(figure_split("Method · Control", "Deterministic orchestration", "fsm",
                          "<b>Figure 7.</b> States and guards. τ_agree = 0.010, "
                          "τ_flag = 0.30, R_max = 4, r_min = 1.",
                          ["Control flow is a <strong>finite-state machine, not a "
                           "model</strong> — predictable, testable, auditable.",
                           "<strong>Converge:</strong> D̄ ≤ τ_agree → aggregate and "
                           "report.",
                           "<strong>Budget:</strong> r = R_max → escalate with the open "
                           "disagreement stated.",
                           "<strong>Can’t-miss:</strong> any red-flag dx with S* ≥ "
                           "τ_flag → escalate, overriding consensus.",
                           "The override is <strong>asymmetric</strong>: it can force "
                           "escalation, never suppress it."]))

    d.append(figure_split("Method · Output", "The report leads with uncertainty",
                          "report",
                          "<b>Figure 8.</b> Status, can’t-miss panel and disagreement "
                          "precede the differential.",
                          ["Ordering is a <strong>safety decision</strong>, not a "
                           "stylistic one.",
                           "The clinically valuable content is what the system is "
                           "<em>unsure</em> about.",
                           "Points of disagreement are surfaced, never suppressed — "
                           "they mark where judgement is needed.",
                           "Every claim carries a citation into the Evidence Ledger; "
                           "the debate is replayable."]))

    d.append(figure_slide("Method · Deployment", "Trust boundaries", "deploy",
                          "<b>Figure 9.</b> Identifiers and raw pixels stay in the PHI "
                          "enclave; the reasoning zone sees only the de-identified CCO; "
                          "re-identification happens solely at the point of care, "
                          "through a restricted token service, and is logged."))

    # ---- Part III ----
    d.append(divider("III", "Prototype &amp; results",
                     "What was built, what it does, and what broke.", "Part III"))

    d.append(slide("Prototype", (
        '<h2>A complete, dependency-free implementation</h2>'
        '<div class="cols c2" style="margin-top:.5em">'
        '<div><table><thead><tr><th>Module</th><th>Responsibility</th></tr></thead>'
        '<tbody>'
        '<tr><td class="mono">schemas.py</td><td>CCO, hypotheses, claims, ledger</td></tr>'
        '<tr><td class="mono">corpus.py</td><td>24-passage graded corpus</td></tr>'
        '<tr><td class="mono">retrieval.py</td><td>BM25 + dense + RRF + re-rank</td></tr>'
        '<tr><td class="mono">verify.py</td><td>groundedness gate</td></tr>'
        '<tr><td class="mono">agents.py</td><td>personas, competence-scoped critique</td></tr>'
        '<tr><td class="mono">consensus.py</td><td>Eqs. (1)–(3), ECE / Brier</td></tr>'
        '<tr><td class="mono">debate.py</td><td>Chief-of-Service FSM</td></tr>'
        '<tr><td class="mono">report.py</td><td>report + transcript renderers</td></tr>'
        '</tbody></table></div>'
        '<div><ul class="pts">'
        '<li><strong>No third-party dependencies</strong>, fully deterministic — the '
        'debate and consensus mathematics can be verified without a model in the '
        'loop.</li>'
        '<li>Two interchangeable reasoning back-ends: <span class="mono">'
        'RuleBasedEngine</span> (offline, reproducible) and <span class="mono">LLMEngine'
        '</span> (production path). Swapping them changes nothing else.</li>'
        '<li>Result figures are computed from the run trace, so the numbers and the '
        'plots cannot drift apart.</li></ul>'
        '<div class="block gl" style="margin-top:1em"><p class="small mono">'
        'cd prototype  &amp;&amp; python3 run_demo.py<br>'
        'cd ../figures &amp;&amp; python3 make_figures.py<br>'
        '&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;'
        '&nbsp;&nbsp;python3 check_layout.py</p></div>'
        '</div></div>'
    )))

    c1, c2, c3 = cases["CASE-001"], cases["CASE-002"], cases["CASE-003"]

    def traj(c: Dict) -> str:
        return " → ".join(f"{r['D_bar']:.4f}" for r in c["rounds"])

    d.append(slide("Results", (
        '<h2>What the prototype does</h2>'
        '<div class="cols c2f" style="margin-top:.5em">'
        '<div><table><thead><tr><th>Case</th><th>Reference dx</th><th>Lead S*</th>'
        '<th>Rounds</th><th>Disposition</th></tr></thead><tbody>'
        f'<tr><td class="mono">CASE-001</td><td>Primary lung malignancy</td>'
        f'<td class="num">0.79 ✓</td><td class="num">4</td>'
        f'<td class="accent"><strong>escalated</strong> — can’t-miss</td></tr>'
        f'<tr><td class="mono">CASE-002</td><td>Benign granuloma</td>'
        f'<td class="num">0.59 ✓</td><td class="num">2</td>'
        f'<td class="green"><strong>converged</strong></td></tr>'
        f'<tr><td class="mono">CASE-003</td><td>Acute coronary syndrome</td>'
        f'<td class="num">0.55 ✓</td><td class="num">1</td>'
        f'<td class="accent"><strong>escalated</strong> — can’t-miss</td></tr>'
        '</tbody></table>'
        '<p class="small sub" style="margin-top:.8em">The three cases exercise all '
        'three stopping paths.</p></div>'
        '<div><table><thead><tr><th>Metric</th><th>Value</th></tr></thead><tbody>'
        f'<tr><td>Top-1 / Top-3</td><td class="num">3/3 · 3/3</td></tr>'
        f'<tr><td>Claims passing grounding gate</td><td class="num">130 / 130</td></tr>'
        f'<tr><td>Ledger citations</td><td class="num">91</td></tr>'
        f'<tr><td>ECE</td><td class="num accent">{S["ece"]:.3f}</td></tr>'
        f'<tr><td>Brier</td><td class="num">{S["brier"]:.3f}</td></tr>'
        '</tbody></table>'
        '<div class="block al" style="margin-top:1em"><p class="small">'
        '<strong>Three synthetic cases with a deterministic reasoner.</strong> This '
        'validates <em>mechanism</em>, not diagnostic performance. The 3/3 hit rate '
        'carries no clinical weight.</p></div></div></div>'
    )))

    d.append(figure_split("Results", "Disagreement as a control signal", "conv",
                          "<b>Figure 10.</b> Real run data.",
                          [f"<strong>CASE-002</strong> falls below τ_agree "
                           f"({traj(c2)}) and <span class='green'>converges</span>.",
                           f"<strong>CASE-001</strong> plateaus above it ({traj(c1)}): "
                           f"the specialists narrow but cannot reconcile, so the case "
                           f"<span class='accent'>escalates with its open disagreement "
                           f"stated</span>.",
                           "<strong>CASE-003</strong> agrees almost immediately yet "
                           "still escalates — a can’t-miss diagnosis overrides "
                           "consensus.",
                           "D̄ gives a principled, compute-bounded criterion for "
                           "<em>“we are not sure — ask a human.”</em>"]))

    d.append(figure_split("Results", "Why competence weighting matters", "diverge",
                          "<b>Figure 11.</b> CASE-001, final round. Real run data.",
                          ["On the leading hypothesis the agents split "
                           "<span class='mono'>0.83 / 0.17 / 0.90 / 0.79</span>.",
                           "The cardiologist’s 0.17 is a <strong>cautionary floor</strong>, "
                           "not a considered dissent — it has no oncology prior.",
                           "Specialty weighting stops it dominating S*(h), and it is "
                           "excluded from D̄ entirely.",
                           "Without both rules, ignorance would masquerade as "
                           "disagreement."]))

    d.append(figure_split("Results", "Evidence adjustment does real work", "diff",
                          "<b>Figure 12.</b> CASE-001 differential. Real run data.",
                          ["The gap between S and S* is the contribution of grounded "
                           "evidence.",
                           "<em>Primary lung malignancy</em> <strong>gains</strong>: "
                           "E = +0.72, S 0.72 → S* 0.79.",
                           "<em>Malignant pericardial effusion</em> <strong>loses</strong>: "
                           "E = −0.34, 0.37 → 0.33 — the retrieved guidance states "
                           "cytological confirmation is required, so the corpus argues "
                           "against asserting it.",
                           "Plausibility and support are separated."]))

    d.append(figure_split("Results", "Calibration: a negative result", "calib",
                          "<b>Figure 13.</b> Real run data; small-sample, not a "
                          "validation result.",
                          [f"ECE = <strong class='accent'>{S['ece']:.3f}</strong> over "
                           f"19 hypothesis-level predictions — <strong>poor</strong>.",
                           "Temperatures and α, β are <strong>hand-set, not fitted</strong> "
                           "on held-out data.",
                           "Eq. (1) weights agents <em>by</em> their confidence, so this "
                           "requirement is currently <strong>unmet</strong>.",
                           "S* should be read <strong>ordinally</strong>, not as a "
                           "probability. Fitting the calibration layer is the first "
                           "prerequisite for any performance claim."]))

    # the key slide
    d.append(slide("Findings", (
        '<h2>Four failure modes the implementation exposed</h2>'
        '<div class="cols c2" style="margin-top:.4em">'
        '<div class="block al"><h3>(a) Hypotheses floating on their prior</h3>'
        '<p class="small">A diagnosis whose supporting features were <em>entirely '
        'absent</em> still scored ≈0.33 on its prior intercept alone — putting lung '
        'malignancy top of the differential for a patient with no nodule. '
        '<strong>Fix:</strong> zero matched features ⇒ penalised out of contention.</p></div>'
        '<div class="block al" style="border-left-width:5px"><h3 class="accent">'
        '(b) Incompetent critique → false reassurance</h3>'
        '<p class="small">Three agents with <strong>no cardiology competence</strong> '
        'critiqued the cardiologist’s correct ACS position using their own ignorance '
        'floor as the comparison. S* fell 0.84 → 0.27, below τ_flag, and the case '
        '<strong>converged instead of escalating</strong> — manufacturing exactly the '
        'false reassurance the system exists to prevent. <strong>Fix:</strong> the right '
        'to object is tied to competence.</p></div>'
        '<div class="block al"><h3>(c) Unbounded reinforcement → echo chamber</h3>'
        '<p class="small">Uncontested positions inflated every round, so apparent '
        'disagreement <em>drifted upward</em> — the opposite of the intended dynamic. '
        '<strong>Fix:</strong> reinforcement capped at the agent’s own prior. '
        'Consolidation may restore a position; it may not inflate it.</p></div>'
        '<div class="block al"><h3>(d) Ignorance floors counted as dissent</h3>'
        '<p class="small">Floors never move, so including them in Eq. (3) created '
        'irreducible disagreement: the benign case exhausted its budget instead of '
        'converging. <strong>Fix:</strong> restrict (3) to substantive opinions.</p></div>'
        '</div>'
        '<p class="lead" style="margin-top:1.1em"><strong>Aggregation rules, not agent '
        'count, determine whether an ensemble is safe.</strong> An unweighted debate '
        'among heterogeneous agents can be <em>more</em> dangerous than one competent '
        'agent — it gives confident non-experts a mechanism to overrule a correct '
        'specialist.</p>'
    )))

    d.append(figure_split("Evaluation", "The study this is not (yet)", "abl",
                          "<b>Figure 14.</b> Expected effects — hypotheses to be "
                          "tested, not measurements.",
                          ["<strong>Data:</strong> knowledge probes; "
                           "clinicopathological-conference cases; a prospective "
                           "<strong>silent trial</strong>, read-only, never influencing "
                           "care.",
                           "<strong>Primary endpoint is safety, not accuracy:</strong> "
                           "can’t-miss recall and the <strong>false-reassurance "
                           "rate</strong>.",
                           "Also: ECE / Brier, groundedness, blinded specialist "
                           "ratings, rounds-to-converge, and subgroup parity.",
                           "<strong>Ablations:</strong> single agent · majority vote · "
                           "debate without RAG · without calibration · full system."]))

    d.append(slide("Safety", (
        '<h2>Assistive by design — the clinician decides</h2>'
        '<div class="cols c2" style="margin-top:.5em">'
        '<div><div class="block gl"><h3>Human gate</h3><p class="small">Mandatory '
        'sign-off before any recommendation informs care. Uncertainty and can’t-miss '
        'findings <strong>escalate rather than close</strong> a case.</p></div>'
        '<div class="block" style="margin-top:14px"><h3>Privacy</h3><p class="small">'
        'De-identification at intake · PHI enclave · encryption · per-access audit · no '
        'training on patient data absent governance and consent.</p></div></div>'
        '<div><div class="block"><h3>Regulatory</h3><p class="small">Decision support '
        'driving diagnosis is likely <strong>Software as a Medical Device</strong>. '
        'Transparent evidence and a replayable transcript support the “clinician can '
        'independently review the basis” pathway — but deployment needs clinical '
        'validation, a predetermined change-control plan, and post-market '
        'surveillance.</p></div>'
        '<div class="block" style="margin-top:14px"><h3>Equity</h3><p class="small">'
        'Corpus and evaluation stratified by subgroup, calibration checked per stratum '
        'and monitored continuously.</p></div></div></div>'
        '<p class="sub" style="margin-top:1.2em">MedJar does not autonomously diagnose '
        'or treat, and is not a substitute for professional medical judgement.</p>'
    )))

    d.append(slide("Limitations", (
        '<h2>Limitations and threats to validity</h2>'
        '<table style="margin-top:.4em"><thead><tr><th>Limitation</th>'
        '<th>Consequence</th></tr></thead><tbody>'
        '<tr><td><strong>Three synthetic cases, rule-based reasoner</strong></td>'
        '<td>Validates mechanism only. No LLM in the loop, no real data, no clinician '
        'review.</td></tr>'
        '<tr><td><strong>Calibration unmet</strong> (ECE 0.243)</td>'
        '<td>Confidence-weighted aggregation is only sound once cᵢ is fitted.</td></tr>'
        '<tr><td><strong>Surrogate components</strong></td>'
        '<td>Hashed bag-of-words for embeddings, lexical coverage for entailment — each '
        'would change absolute numbers.</td></tr>'
        '<tr><td><strong>Crude polarity classification</strong></td>'
        '<td>ACS received E = −0.41 because passages <em>defining</em> its criteria '
        'contain cautionary language. Needs a trained stance classifier.</td></tr>'
        '<tr><td><strong>Correlated agent failure</strong></td>'
        '<td>Shared base models may share blind spots, weakening the diversity the '
        'protocol depends on.</td></tr>'
        '<tr><td><strong>Automation bias</strong></td>'
        '<td>Leading with uncertainty is intended to counter over-trust; whether it '
        'does is a human-factors question.</td></tr>'
        '</tbody></table>'
    )))

    d.append(slide("Conclusion", (
        '<h2>Conclusion</h2>'
        '<p class="lead" style="margin:.5em 0 1.1em">MedJar recasts the '
        'multidisciplinary case conference as a computational protocol: specialists '
        'reason independently, ground every claim, debate under rules that tie the '
        'right to object to competence, and converge on a calibrated, auditable '
        'assessment — <strong>escalating to a human precisely when they should</strong>.</p>'
        '<div class="cols c3">'
        '<div class="block gl"><h3>Demonstrated</h3><p class="small">The full pipeline '
        'runs end to end, deterministically, and D̄ works as a control signal across '
        'all three stopping paths.</p></div>'
        '<div class="block al"><h3>The transferable result</h3><p class="small">Naive '
        'multi-agent debate is <strong>not automatically safer</strong>. We watched a '
        'correct can’t-miss diagnosis suppressed by agents with no competence in the '
        'domain.</p></div>'
        '<div class="block"><h3>Next</h3><p class="small">Fit the calibration layer; '
        'then a prospective silent trial — the only way to learn whether any of this '
        'helps a clinician.</p></div></div>'
        '<p class="lead" style="margin-top:1.3em;text-align:center"><strong>Aggregation '
        'rules, not agent count, determine whether an ensemble is safe.</strong></p>'
    )))

    d.append(slide("References", (
        '<h2>Selected references</h2>'
        '<div class="cols c2" style="margin-top:.5em">'
        '<ul class="pts tiny" style="list-style:none">'
        '<li>[1] National Academies. <em>Improving Diagnosis in Health Care.</em> 2015.</li>'
        '<li>[2] Du et al. Improving factuality and reasoning through multiagent '
        'debate. 2023.</li>'
        '<li>[3] Madaan et al. Self-Refine: iterative refinement with self-feedback. '
        'NeurIPS 2023.</li>'
        '<li>[4] Lewis et al. Retrieval-augmented generation for knowledge-intensive '
        'NLP. NeurIPS 2020.</li>'
        '<li>[5] Cormack et al. Reciprocal rank fusion. SIGIR 2009.</li></ul>'
        '<ul class="pts tiny" style="list-style:none">'
        '<li>[6] Jin et al. MedQA / USMLE-style medical QA. 2021.</li>'
        '<li>[7] Pal et al. MedMCQA. CHIL 2022.</li>'
        '<li>[8] Singhal et al. Large language models encode clinical knowledge. '
        'Nature 2023.</li>'
        '<li>[9] Guo et al. On calibration of modern neural networks. ICML 2017.</li>'
        '<li>[10] U.S. FDA. Clinical Decision Support Software guidance; GMLP '
        'principles.</li></ul></div>'
        '<p class="illus" style="margin-top:1.2em">Citations are provided at the level '
        'of identification; verify against primary sources before publication.</p>'
        '<p class="sub" style="margin-top:1.4em;text-align:center">MedJar · Consensus '
        'Diagnosis by Debating Specialist Agents · thank you</p>'
    )))

    html = ("<!DOCTYPE html>\n<html lang=\"en\">\n<head>\n"
            "<meta charset=\"UTF-8\"/>\n"
            "<meta name=\"viewport\" content=\"width=device-width, initial-scale=1.0\"/>\n"
            "<title>MedJar — Consensus Diagnosis by Debating Specialist Agents</title>\n"
            f"<style>{CSS}</style>\n</head>\n<body>\n"
            "<div class=\"progress\" id=\"progress\"></div>\n"
            "<div class=\"dwell\" id=\"dwell\"></div>\n"
            f"<div id=\"deck\">\n{''.join(d)}\n</div>\n"
            "<div class=\"dots\" id=\"dots\"></div>\n"
            "<div class=\"hint\">← → navigate&nbsp;·&nbsp;"
            "<span id=\"autobtn\" class=\"btn\">Auto</span>&nbsp;·&nbsp;F fullscreen</div>\n"
            "<div class=\"chrome\"><span id=\"counter\">1 / 1</span></div>\n"
            f"<script>{JS}</script>\n</body>\n</html>\n")
    return html


def main() -> int:
    html = build()
    with open(OUTFILE, "w", encoding="utf-8") as f:
        f.write(html)
    n = html.count('<section class="slide')
    print(f"Wrote {os.path.relpath(OUTFILE, HERE)}  "
          f"({len(html):,} bytes, {n} slides, {len(FIGS)} figures inlined)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

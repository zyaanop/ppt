#!/usr/bin/env python3
"""
build_deck.py — assemble presentation.html from the generated figures.

The figures in figures/*.svg are inlined into a single self-contained HTML file,
so the deck opens anywhere with no external assets and no network.

Slide copy is deliberately plain: the formal treatment lives in PAPER.md, and a
slide that needs re-reading has failed. `check_deck.py` enforces this with word
and sentence-length budgets.

    cd figures && python3 make_figures.py
    cd ..      && python3 build_deck.py && python3 check_deck.py
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

/* type */
h1{font-family:var(--serif);font-weight:600;font-size:clamp(26px,3.9vw,52px);line-height:1.07}
h2{font-family:var(--serif);font-weight:600;font-size:clamp(22px,2.65vw,36px);line-height:1.12;
  margin-bottom:.1em}
h2:after{content:"";display:block;width:58px;height:3px;background:var(--accent);margin-top:.38em}
h3{font-size:clamp(12.5px,1.2vw,16.5px);font-weight:700;color:var(--ink);letter-spacing:.01em}
p,li{font-family:var(--serif);font-size:clamp(14px,1.34vw,20px);line-height:1.52;color:var(--ink2)}
.sub{font-family:var(--serif);font-style:italic;color:var(--ink3)}
.small{font-size:clamp(12px,1.08vw,15.5px)}
.tiny{font-size:clamp(10.5px,.94vw,13px)}
strong{font-weight:700;color:var(--ink)}
.mono{font-family:var(--mono);font-size:.9em}
.accent{color:var(--accent)}.green{color:var(--green)}
.lead{max-width:62ch}

/* layout */
.cols{display:grid;gap:2.4vw}
.c2{grid-template-columns:1fr 1fr}
.c2f{grid-template-columns:1.52fr 1fr}
.c3{grid-template-columns:repeat(3,1fr)}
.c4{grid-template-columns:repeat(4,1fr)}
ul.pts{list-style:none}
ul.pts>li{position:relative;padding-left:1.35em;margin:.5em 0}
ul.pts>li:before{content:"\\2014";position:absolute;left:0;color:var(--accent);font-family:var(--sans)}
ol.num{list-style:none;counter-reset:c}
ol.num>li{counter-increment:c;position:relative;padding-left:2.2em;margin:.6em 0}
ol.num>li:before{content:counter(c);position:absolute;left:0;top:.02em;width:1.45em;height:1.45em;
  border:1.5px solid var(--accent);color:var(--accent);border-radius:50%;display:grid;
  place-items:center;font-family:var(--sans);font-weight:700;font-size:.6em}
.block{border:1px solid var(--rule);background:#f4f2ec;padding:14px 16px}
.block.al{border-left:3px solid var(--accent)}
.block.gl{border-left:3px solid var(--green)}
table{width:100%;border-collapse:collapse;font-family:var(--sans)}
th{text-align:left;font-size:10.5px;letter-spacing:.06em;text-transform:uppercase;
  color:var(--accent);border-bottom:1.5px solid var(--ink);padding:7px 10px;font-weight:700}
td{font-family:var(--serif);font-size:clamp(12px,1.1vw,16.5px);color:var(--ink2);
  border-bottom:1px solid var(--rule);padding:7px 10px}
tr:last-child td{border-bottom:none}
td.num{font-family:var(--mono);font-size:.9em}

/* figures */
.figwrap{flex:1;display:flex;align-items:center;justify-content:center;min-height:0;margin:.4vh 0}
.figwrap svg{max-width:100%;max-height:100%;width:auto;height:auto;
  border:1px solid var(--rule);background:#fff;padding:6px}
.figwrap.big svg{max-height:70vh}
.cap{flex:none;font-size:clamp(11px,1vw,13.5px);color:var(--ink3);margin-top:1vh;
  text-align:center;font-family:var(--sans);line-height:1.45}
.cap b{color:var(--ink)}
.illus{font-size:9.5px;letter-spacing:.12em;text-transform:uppercase;color:var(--faint)}

/* Figures settle into place, then their connectors are drawn in. Decorative
   only, and suppressed for viewers who prefer reduced motion. Child selectors
   keep <defs> markers out of it, so arrowheads never flicker. */
@keyframes figSettle{from{opacity:0;transform:translateY(10px) scale(.994)}
                     to{opacity:1;transform:none}}
@keyframes inkIn{from{opacity:0}to{opacity:1}}
.slide.active .figwrap svg{animation:figSettle .62s cubic-bezier(.2,.7,.2,1) both}
.slide.active .figwrap svg>rect,
.slide.active .figwrap svg>text,
.slide.active .figwrap svg>g{animation:inkIn .48s ease .10s both}
.slide.active .figwrap svg>path,
.slide.active .figwrap svg>line,
.slide.active .figwrap svg>polyline,
.slide.active .figwrap svg>circle{animation:inkIn .55s ease .30s both}
@media (prefers-reduced-motion:reduce){
  .slide,.slide.active .figwrap svg,.slide.active .figwrap svg>*{
    animation:none!important;transition:none!important}
}

/* maths */
.eq{font-family:var(--serif);font-size:clamp(15px,1.75vw,24px);color:var(--ink);
  display:flex;align-items:center;gap:.3em;flex-wrap:wrap}
.frac{display:inline-flex;flex-direction:column;text-align:center;margin:0 .12em}
.frac .n{border-bottom:1.4px solid var(--ink);padding:0 .45em .04em}
.frac .d{padding:.04em .45em 0}
.eqlab{margin-left:auto;font-family:var(--sans);font-size:11.5px;color:var(--ink3);
  font-style:italic}

/* dividers and title */
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

/* chrome */
.progress{position:fixed;top:0;left:0;height:3px;background:var(--accent);z-index:20;
  transition:width .28s ease}
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
  function pause(){if(auto){clearTimeout(timer);clearBar();clearTimeout(relaunch);
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

    d: List[str] = []

    # ---------------- title ----------------
    d.append(
        '<section class="slide title"><div class="body">'
        '<div class="kick">Multi-Agent Clinical Reasoning · Research Prototype</div>'
        '<h1>MedJar: Consensus Diagnosis by Debating Specialist Agents</h1>'
        '<div class="rule"></div>'
        '<p class="sub lead">Several AI specialists read the same patient case and '
        'argue about it. Each must back its claims with a citation. If they cannot '
        'agree, or something dangerous appears, the case goes to a doctor.</p>'
        '<div class="byline"><div><strong>MedJar Working Group</strong></div>'
        '<div class="af" style="margin-top:9px">Assistive only — not an autonomous '
        'diagnostic device</div></div>'
        '</div></section>')

    # ---------------- motivation ----------------
    d.append(slide("Motivation", (
        '<h2>Why hard cases go wrong</h2>'
        '<p class="lead" style="margin:.5em 0 1em">About <strong>1 in 20</strong> '
        'adults gets a wrong or delayed diagnosis each year. It happens most in cases '
        'that cross specialties.</p>'
        '<div class="cols c2">'
        '<ul class="pts">'
        '<li><strong>The first idea sticks.</strong> Later evidence gets bent to fit '
        'it.</li>'
        '<li><strong>The search stops early.</strong> One plausible answer ends the '
        'thinking.</li></ul>'
        '<ul class="pts">'
        '<li><strong>Experts sit in silos.</strong> The people who could settle it '
        'never meet on the case.</li>'
        '<li><strong>Guidelines move.</strong> Nobody can keep up with all of '
        'them.</li></ul></div>'
        '<p class="lead sub" style="margin-top:1.3em">Hospitals already have a fix: '
        'the tumour board. What makes it work is <strong>disagreement</strong>, not '
        'agreement.</p>'
    )))

    d.append(slide("Motivation", (
        '<h2>Why one AI is not enough</h2>'
        '<p class="lead" style="margin:.4em 0 1.1em">Telling a single model '
        '<em>“you are an expert doctor”</em> buys you one point of view.</p>'
        '<div class="cols c3">'
        '<div class="block al"><h3>One blind spot</h3><p class="small">One set of '
        'instincts. Nothing inside it argues back.</p></div>'
        '<div class="block al"><h3>Confident either way</h3><p class="small">It sounds '
        'equally sure when it is right and when it is wrong.</p></div>'
        '<div class="block al"><h3>Nothing to check</h3><p class="small">Its claims are '
        'not tied to a source you can look up.</p></div></div>'
        '<p class="lead" style="margin-top:1.3em">Simple voting does not fix it '
        'either. Voting hides <em>why</em> they disagree, and it outvotes the one '
        'agent that spotted something dangerous.</p>'
    )))

    d.append(slide("Contributions", (
        '<h2>What is new here</h2>'
        '<ol class="num" style="margin-top:.6em">'
        '<li><strong>Specialists that really differ.</strong> Each has its own '
        'instincts and searches its own library.</li>'
        '<li><strong>A debate with rules.</strong> Propose, criticise, reply, then '
        'check whether they agree.</li>'
        '<li><strong>A fair way to combine scores.</strong> Weight each agent by its '
        'confidence and by how much it knows about that disease.</li>'
        '<li><strong>Only experts may object.</strong> An agent cannot argue down a '
        'diagnosis outside its field. We show this is essential.</li>'
        '<li><strong>A working prototype</strong> — and an honest account of what did '
        'not work.</li></ol>'
    )))

    # ---------------- Part I ----------------
    d.append(divider("I", "System", "How a case moves through it.", "Part I"))

    d.append(figure_slide("System · Architecture", "Six layers, one loop", "arch",
                          "<b>Figure 1.</b> Data flows downward. Steps 0–2 just "
                          "prepare the case. The debate happens at step 3. Steps 4–5 "
                          "score it and write the report."))

    d.append(figure_slide("System · Workflow", "The whole thing, end to end", "flow",
                          "<b>Figure 2.</b> All 16 steps. Names are stripped in the "
                          "intake lane, so nothing below that line can identify a "
                          "patient. Steps 10–12 repeat until the agents agree or time "
                          "runs out. Every route ends with a doctor signing off.",
                          big=True))

    d.append(figure_split("System · Case file", "One shared case file", "cco",
                          "<b>Figure 3.</b> Six kinds of input, all mapped to standard "
                          "medical codes.",
                          ["Every agent reads the same file.",
                           "Names are removed first, and scan images never leave the "
                           "hospital.",
                           "It records what was <em>ruled out</em>, not just what was "
                           "found.",
                           "Swap an input reader and nothing downstream changes."]))

    # ---------------- Part II ----------------
    d.append(divider("II", "Method", "Sources, the debate, and the score.", "Part II"))

    d.append(figure_slide("Method · Sources", "Every claim needs a source", "rag",
                          "<b>Figure 4.</b> Two searches run at once — one by meaning, "
                          "one by exact wording — and the results are merged. If the "
                          "cited passage does not actually support the claim, the claim "
                          "is thrown away before it can count."))

    d.append(slide("Method · Agents", (
        '<h2>The four specialists</h2>'
        '<p class="lead" style="margin:.4em 0 .9em">Each has its own instincts and its '
        'own reading list.</p>'
        '<table><thead><tr><th>Agent</th><th>Looks at first</th>'
        '<th>Its question</th></tr></thead><tbody>'
        '<tr><td><strong>Radiologist</strong></td><td>the shape and place of what is '
        'on the scan</td><td class="sub">What does the image actually show?</td></tr>'
        '<tr><td><strong>Cardiologist</strong></td><td>anything about the heart that '
        'could kill today</td><td class="sub">Is the heart the cause, or a '
        'casualty?</td></tr>'
        '<tr><td><strong>Oncologist</strong></td><td>whether it is cancer, and how far '
        'it has spread</td><td class="sub">What proves the stage?</td></tr>'
        '<tr><td><strong>Generalist</strong></td><td>the whole patient</td>'
        '<td class="sub">Does this explain everything?</td></tr>'
        '</tbody></table>'
        '<div class="block al" style="margin-top:1.2em"><p class="small">'
        'Each turn comes back as a filled-in form, not an essay. It gives the '
        'disease, a probability, evidence for and against, and the next test. '
        '<strong>Nobody stays silent</strong> — an agent outside its field gives a low '
        '“not my area” score, which counts for less.</p></div>'
    )))

    d.append(figure_slide("Method · Debate", "Propose, criticise, reply, check", "seq",
                          "<b>Figure 5.</b> Each agent writes its first answer alone, "
                          "so nobody copies anybody. Then they criticise each other "
                          "anonymously and reply. One round of criticism always happens, "
                          "even when they already agree."))

    d.append(slide("Method · Score", (
        '<h2>How the scores are combined</h2>'
        '<div style="margin:.5em 0 1em">'
        '<div class="eq">S(h) = <span class="frac"><span class="n">Σᵢ wᵢ(h)·cᵢ·pᵢ(h)'
        '</span><span class="d">Σᵢ wᵢ(h)·cᵢ</span></span>'
        '<span class="eqlab">(1) a weighted average of the agents’ scores</span></div>'
        '</div>'
        '<div style="margin:.9em 0">'
        '<div class="eq">S*(h) = σ( α·logit S(h) + β·E(h) )'
        '<span class="eqlab">(2) adjust for how good the evidence is</span></div></div>'
        '<div style="margin:.9em 0">'
        '<div class="eq">Disagree(h) = <span class="frac">'
        '<span class="n">Σ<sub>i∈𝒮</sub> wᵢcᵢ( pᵢ(h) − S(h) )²</span>'
        '<span class="d">Σ<sub>i∈𝒮</sub> wᵢcᵢ</span></span>'
        '<span class="eqlab">(3) how far apart they are</span></div></div>'
        '<div class="cols c3" style="margin-top:1.1em">'
        '<div class="block"><h3>wᵢ — who to trust</h3><p class="small">The cardiologist '
        'counts most on heart problems. Everyone still votes on everything.</p></div>'
        '<div class="block"><h3>E — evidence quality</h3><p class="small">Support minus '
        'contradiction, weighted by how strong and how recent the source is.</p></div>'
        '<div class="block al"><h3>𝒮 — who has a real view</h3><p class="small">“Not my '
        'field” answers are left out. Not knowing is not disagreeing.</p></div></div>'
    )))

    d.append(figure_slide("Method · Score", "From four opinions to one number", "cons",
                          "<b>Figure 6.</b> Real numbers from CASE-001. The "
                          "cardiologist’s 0.17 means “not my field”, not “I "
                          "disagree” — so it is weighted down, and left out of the "
                          "disagreement number."))

    d.append(figure_split("Method · Control", "Who runs the meeting", "fsm",
                          "<b>Figure 7.</b> The states, and the rules for moving "
                          "between them.",
                          ["A fixed program runs the meeting, not a model.",
                           "<strong>They agree</strong> → write the report.",
                           "<strong>Time runs out</strong> → send it to a doctor.",
                           "<strong>Something dangerous scores high</strong> → send it "
                           "to a doctor, whatever the others think."]))

    d.append(figure_split("Method · Output", "The report starts with the doubts",
                          "report",
                          "<b>Figure 8.</b> Status, dangers and disagreements come "
                          "before the list of diagnoses.",
                          ["Putting doubt first is a safety choice, not a style one.",
                           "What the system is unsure about is the useful part.",
                           "Disagreements are shown, never hidden.",
                           "Every claim links back to the passage it came from."]))

    d.append(figure_slide("System · Privacy", "Where the patient data lives", "deploy",
                          "<b>Figure 9.</b> Names and scan images stay inside the "
                          "hospital. The reasoning side only ever sees the anonymous "
                          "case. Names are added back just for the doctor, and every "
                          "access is logged."))

    # ---------------- Part III ----------------
    d.append(divider("III", "Prototype &amp; results",
                     "What was built, and what broke.", "Part III"))

    d.append(slide("Prototype", (
        '<h2>It runs, with nothing to install</h2>'
        '<div class="cols c2f" style="margin-top:.5em">'
        '<div><table><thead><tr><th>File</th><th>Job</th></tr></thead><tbody>'
        '<tr><td class="mono">corpus.py</td><td>the medical library</td></tr>'
        '<tr><td class="mono">retrieval.py</td><td>finds relevant passages</td></tr>'
        '<tr><td class="mono">verify.py</td><td>checks a claim against its source</td></tr>'
        '<tr><td class="mono">agents.py</td><td>the four specialists</td></tr>'
        '<tr><td class="mono">consensus.py</td><td>the three equations</td></tr>'
        '<tr><td class="mono">debate.py</td><td>runs the meeting</td></tr>'
        '<tr><td class="mono">report.py</td><td>writes the report</td></tr>'
        '</tbody></table></div>'
        '<div><ul class="pts">'
        '<li>Python only, <strong>no libraries</strong>.</li>'
        '<li>Same answer every time, so the maths can be checked without a model in '
        'the loop.</li>'
        '<li>Two engines you can swap: offline rules, or real LLMs.</li>'
        '<li>The charts are built from the run itself, so numbers and pictures cannot '
        'drift apart.</li></ul>'
        '<div class="block gl" style="margin-top:1em"><p class="small mono">'
        'python3 run_demo.py<br>python3 make_figures.py</p></div>'
        '</div></div>'
    )))

    d.append(slide("Results", (
        '<h2>What it does on three cases</h2>'
        '<div class="cols c2f" style="margin-top:.5em">'
        '<div><table><thead><tr><th>Case</th><th>Right answer</th><th>Score</th>'
        '<th>Rounds</th><th>Outcome</th></tr></thead><tbody>'
        '<tr><td class="mono">CASE-001</td><td>Lung cancer</td>'
        '<td class="num">0.79 ✓</td><td class="num">4</td>'
        '<td class="accent"><strong>sent to a doctor</strong></td></tr>'
        '<tr><td class="mono">CASE-002</td><td>Harmless nodule</td>'
        '<td class="num">0.59 ✓</td><td class="num">2</td>'
        '<td class="green"><strong>agreed</strong></td></tr>'
        '<tr><td class="mono">CASE-003</td><td>Heart attack</td>'
        '<td class="num">0.55 ✓</td><td class="num">1</td>'
        '<td class="accent"><strong>sent to a doctor</strong></td></tr>'
        '</tbody></table>'
        '<p class="small sub" style="margin-top:.8em">Between them, these three take '
        'all three possible exits.</p></div>'
        '<div><table><thead><tr><th>Measure</th><th>Value</th></tr></thead><tbody>'
        '<tr><td>Top answer correct</td><td class="num">3 of 3</td></tr>'
        '<tr><td>Claims backed by a source</td><td class="num">130 of 130</td></tr>'
        '<tr><td>Citations recorded</td><td class="num">91</td></tr>'
        f'<tr><td>Confidence error (ECE)</td><td class="num accent">{S["ece"]:.3f}</td></tr>'
        '</tbody></table>'
        '<div class="block al" style="margin-top:1em"><p class="small">'
        'Three <strong>made-up</strong> cases, offline engine. This shows the machinery '
        'works. It says <strong>nothing</strong> about whether it can diagnose.</p>'
        '</div></div></div>'
    )))

    d.append(figure_split("Results", "Disagreement decides what happens", "conv",
                          "<b>Figure 10.</b> Real run data.",
                          ["<strong>CASE-002</strong> — they converge, so the report "
                           "goes out.",
                           "<strong>CASE-001</strong> — they narrow the gap but never "
                           "close it, so a doctor gets it.",
                           "<strong>CASE-003</strong> — they agree quickly, yet a "
                           "dangerous diagnosis still forces escalation.",
                           "A clear rule for <em>“we are not sure — ask a human.”</em>"]))

    d.append(figure_split("Results", "Why “who knows what” matters", "diverge",
                          "<b>Figure 11.</b> CASE-001, final round. Real run data.",
                          ["On the top diagnosis the four agents said "
                           "<span class='mono'>0.83, 0.17, 0.90, 0.79</span>.",
                           "The 0.17 is the cardiologist saying “not my field”.",
                           "Weighting stops it dragging the score down.",
                           "And it is left out of the disagreement number "
                           "altogether."]))

    d.append(figure_split("Results", "Good evidence moves the score", "diff",
                          "<b>Figure 12.</b> CASE-001. Real run data.",
                          ["<strong>Lung cancer goes up</strong> — the sources back it "
                           "(0.72 → 0.79).",
                           "<strong>Cancer in the heart lining goes down</strong> — the "
                           "guideline says you need a lab test first (0.37 → 0.33).",
                           "So “sounds likely” and “is actually supported” are kept "
                           "apart."]))

    d.append(figure_split("Results", "What did not work: the confidence numbers",
                          "calib",
                          "<b>Figure 13.</b> Real run data, very small sample.",
                          ["The confidence scores are <strong>badly calibrated</strong> "
                           f"(ECE {S['ece']:.3f}).",
                           "We set the weights by hand instead of fitting them to data.",
                           "The maths weights agents <em>by</em> confidence, so this "
                           "matters.",
                           "Read the scores as a ranking, not as real probabilities."]))

    # ---------------- failure modes, split over two slides ----------------
    d.append(slide("Findings", (
        '<h2>What broke — and one of them was serious</h2>'
        '<div class="cols c2" style="margin-top:.4em">'
        '<div class="block al"><h3>A diagnosis floating on a hunch</h3>'
        '<p class="small">A disease with <em>no</em> supporting findings still scored '
        '0.33, on its prior alone. It topped the list for a patient '
        'with none of its signs.</p>'
        '<p class="small" style="margin-top:.6em"><strong>Fix:</strong> no evidence, no '
        'place on the list.</p></div>'
        '<div class="block al" style="border-left-width:5px">'
        '<h3 class="accent">Non-experts overruling the expert</h3>'
        '<p class="small">Three agents with <strong>no heart training</strong> argued '
        'the cardiologist out of a <strong>correct heart-attack diagnosis</strong>. The '
        'score fell 0.84 → 0.27, below the alarm level, and the case '
        '<strong>closed instead of escalating</strong>.</p>'
        '<p class="small" style="margin-top:.6em"><strong>Fix:</strong> you may only '
        'object in a field you actually know.</p></div>'
        '</div>'
        '<p class="lead" style="margin-top:1.1em">That is exactly the false '
        'reassurance the system exists to prevent.</p>'
    )))

    d.append(slide("Findings", (
        '<h2>What broke — the other two</h2>'
        '<div class="cols c2" style="margin-top:.4em">'
        '<div class="block al"><h3>An echo chamber</h3>'
        '<p class="small">Agents kept boosting their own unchallenged answers every '
        'round, so disagreement <em>grew</em> instead of shrinking — the opposite of '
        'what should happen.</p>'
        '<p class="small" style="margin-top:.6em"><strong>Fix:</strong> confidence may '
        'recover to where it started, never above.</p></div>'
        '<div class="block al"><h3>Silence counted as dissent</h3>'
        '<p class="small">“Not my field” answers were counted as disagreement. They '
        'never change, so the argument could never end. A simple case ran out of time '
        'instead of agreeing.</p>'
        '<p class="small" style="margin-top:.6em"><strong>Fix:</strong> leave those '
        'answers out of the disagreement number.</p></div>'
        '</div>'
        '<p class="lead" style="margin-top:1.1em"><strong>The rules for combining '
        'opinions matter more than the number of agents.</strong> Without them, a '
        'debate can be worse than one good doctor.</p>'
    )))

    d.append(figure_split("Evaluation", "What we have not done yet", "abl",
                          "<b>Figure 14.</b> Expected effects — a plan, not results.",
                          ["Test on real recorded cases, then run quietly alongside "
                           "real doctors.",
                           "The main measure is <strong>safety</strong>: how often it "
                           "wrongly says nothing is dangerous.",
                           "Compare one agent, plain voting, debate without sources, "
                           "and the full system.",
                           "Only then can accuracy be claimed."]))

    d.append(slide("Safety", (
        '<h2>The doctor decides</h2>'
        '<div class="cols c2" style="margin-top:.5em">'
        '<div><div class="block gl"><h3>A human always signs off</h3>'
        '<p class="small">Nothing reaches patient care unread. When the system is '
        'unsure, it escalates instead of closing the case.</p></div>'
        '<div class="block" style="margin-top:14px"><h3>Privacy</h3><p class="small">'
        'Names removed at intake, held in a locked zone, every access logged.</p></div></div>'
        '<div><div class="block"><h3>It counts as a medical device</h3>'
        '<p class="small">Showing the evidence and the argument is what lets a doctor '
        'check the reasoning. Real use would still need clinical trials and '
        'monitoring.</p></div>'
        '<div class="block" style="margin-top:14px"><h3>Fairness</h3><p class="small">'
        'Accuracy and confidence have to be checked separately for each patient '
        'group.</p></div></div></div>'
        '<p class="sub" style="margin-top:1.2em">MedJar does not diagnose or treat on '
        'its own, and is not a substitute for a doctor.</p>'
    )))

    d.append(slide("Limitations", (
        '<h2>What to hold against it</h2>'
        '<table style="margin-top:.4em"><thead><tr><th>Limitation</th>'
        '<th>Why it matters</th></tr></thead><tbody>'
        '<tr><td><strong>Three made-up cases</strong></td>'
        '<td>Shows the machinery runs. Says nothing about diagnosing.</td></tr>'
        '<tr><td><strong>No real model in the loop</strong></td>'
        '<td>The reported results use hand-written rules, not an LLM.</td></tr>'
        '<tr><td><strong>Confidence not calibrated</strong></td>'
        '<td>The weighting is only sound once it is fitted to data.</td></tr>'
        '<tr><td><strong>Stand-in components</strong></td>'
        '<td>Search and claim-checking are simple substitutes. Real ones change the '
        'numbers.</td></tr>'
        '<tr><td><strong>“For” vs “against” is crude</strong></td>'
        '<td>A passage defining a disease often reads as arguing against it.</td></tr>'
        '<tr><td><strong>Shared blind spots</strong></td>'
        '<td>Agents on the same base model may fail the same way.</td></tr>'
        '<tr><td><strong>Tiny library</strong></td>'
        '<td>24 passages. Real use needs licensed, maintained guidelines.</td></tr>'
        '</tbody></table>'
    )))

    d.append(slide("Conclusion", (
        '<h2>Conclusion</h2>'
        '<p class="lead" style="margin:.5em 0 1.1em">MedJar turns the hospital case '
        'conference into a program. Specialists think alone, cite their sources, argue '
        'under rules, and hand the case to a doctor when they should.</p>'
        '<div class="cols c3">'
        '<div class="block gl"><h3>It works</h3><p class="small">The pipeline runs end '
        'to end, and the disagreement number reliably picks the right exit.</p></div>'
        '<div class="block al"><h3>The warning</h3><p class="small">More agents is not '
        'automatically safer. We watched non-experts talk down a correct dangerous '
        'diagnosis.</p></div>'
        '<div class="block"><h3>Next</h3><p class="small">Fit the confidence numbers, '
        'then trial it quietly beside real doctors.</p></div></div>'
        '<p class="lead" style="margin-top:1.3em;text-align:center"><strong>The rules '
        'for combining opinions decide whether an ensemble is safe.</strong></p>'
    )))

    d.append(slide("References", (
        '<h2>Selected references</h2>'
        '<div class="cols c2" style="margin-top:.5em">'
        '<ul class="pts tiny">'
        '<li>[1] National Academies. <em>Improving Diagnosis in Health Care.</em> 2015.</li>'
        '<li>[2] Du et al. Multiagent debate improves factuality. 2023.</li>'
        '<li>[3] Madaan et al. Self-Refine. NeurIPS 2023.</li>'
        '<li>[4] Lewis et al. Retrieval-augmented generation. NeurIPS 2020.</li>'
        '<li>[5] Cormack et al. Reciprocal rank fusion. SIGIR 2009.</li></ul>'
        '<ul class="pts tiny">'
        '<li>[6] Jin et al. MedQA. 2021.</li>'
        '<li>[7] Pal et al. MedMCQA. CHIL 2022.</li>'
        '<li>[8] Singhal et al. LLMs encode clinical knowledge. Nature 2023.</li>'
        '<li>[9] Guo et al. On calibration of modern networks. ICML 2017.</li>'
        '<li>[10] U.S. FDA. Clinical Decision Support guidance; GMLP.</li></ul></div>'
        '<p class="illus" style="margin-top:1.2em">Verify against the primary sources '
        'before citing.</p>'
        '<p class="sub" style="margin-top:1.4em;text-align:center">MedJar · thank '
        'you</p>'
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

#!/usr/bin/env python3
"""
check_deck.py — formatting and readability audit for presentation.html.

The build environment cannot render HTML, so this stands in for a visual review.
It reports, per slide, the things that actually break a deck:

  * text volume — slides that hold more prose than fits comfortably
  * sentence length and long-word density — a proxy for "is this readable from
    the back of a room", since the copy should be plain, not academic
  * structural faults — unbalanced tags, duplicate ids, external references
    (the deck must stay self-contained), oversized tables

Thresholds are deliberately strict for a spoken presentation:
    figure slides   <=  60 words   (the figure carries the content)
    text slides     <= 110 words
    any sentence    <=  24 words
    long words      <=  14 %       (words of 12+ characters)
"""
from __future__ import annotations

import os
import re
import sys
from typing import Dict, List, Tuple

HERE = os.path.dirname(os.path.abspath(__file__))
DECK = os.path.join(HERE, "presentation.html")

MAX_WORDS_FIGURE = 60
MAX_WORDS_TEXT = 110
MAX_SENTENCE = 24
MAX_LONGWORD_PCT = 14.0


def slides(html: str) -> List[Tuple[str, str]]:
    """Return (class_attr, inner_html) per slide."""
    out = []
    for m in re.finditer(r'<section class="slide([^"]*)">(.*?)</section>', html, re.S):
        out.append((m.group(1).strip(), m.group(2)))
    return out


def visible_text(fragment: str, drop_tabular: bool = False) -> str:
    """Text content of a fragment.

    Inline SVG is always dropped: figure labels are part of the diagram, not
    slide copy. With `drop_tabular`, tables and equation blocks are dropped too —
    they are scanned rather than read, so counting them as prose would both
    inflate word counts and manufacture nonsense "sentences" out of joined cells.
    """
    frag = re.sub(r"<svg.*?</svg>", " ", fragment, flags=re.S)
    frag = re.sub(r"<style.*?</style>", " ", frag, flags=re.S)
    if drop_tabular:
        frag = re.sub(r"<table.*?</table>", " ", frag, flags=re.S)
        frag = re.sub(r'<div class="eq".*?</div>\s*', " ", frag, flags=re.S)
    # Block boundaries end a sentence. Without this, a heading runs into the
    # paragraph beneath it and the sentence-length check reports phantom
    # 30-word sentences that no reader ever sees.
    frag = re.sub(r"</(?:h1|h2|h3|h4|p|li|td|th|div|section)>", ". ", frag)
    frag = re.sub(r"<[^>]+>", " ", frag)
    frag = re.sub(r"\s*\.\s*(?:\.\s*)+", ". ", frag)
    frag = (frag.replace("&nbsp;", " ").replace("&amp;", "&")
            .replace("&lt;", "<").replace("&gt;", ">").replace("&times;", "x")
            .replace("&mdash;", "—").replace("&#8226;", "-"))
    return re.sub(r"\s+", " ", frag).strip()


def sentences(text: str) -> List[str]:
    # Split on terminal punctuation regardless of what follows: the next segment
    # may begin with a symbol (𝒮, ←, a digit), and requiring A-Z there silently
    # merged sentences and inflated the reported lengths.
    parts = re.split(r"(?<=[.!?])\s+", text)
    return [p.strip() for p in parts if len(p.split()) > 1]


def title_of(fragment: str) -> str:
    for tag in ("h2", "h1"):
        m = re.search(rf"<{tag}[^>]*>(.*?)</{tag}>", fragment, re.S)
        if m:
            return visible_text(m.group(1))[:52]
    return "(untitled)"


def audit(html: str) -> Tuple[List[str], Dict[str, float]]:
    issues: List[str] = []
    sl = slides(html)

    # ---- document-level structure ----
    for tag in ("section", "svg", "table", "div", "ul", "ol", "script", "style"):
        o = len(re.findall(rf"<{tag}[ >]", html))
        c = len(re.findall(rf"</{tag}>", html))
        if o != c:
            issues.append(f"[doc] unbalanced <{tag}>: {o} open, {c} close")

    ids = re.findall(r'id="([^"]+)"', html)
    dups = sorted({i for i in ids if ids.count(i) > 1})
    if dups:
        issues.append(f"[doc] duplicate ids: {', '.join(dups[:6])}")

    ext = [u for u in re.findall(r'(?:src|href)="(?!#)([^"]+)"', html)
           if not u.startswith("data:")]
    if ext:
        issues.append(f"[doc] external references (deck must be self-contained): {ext[:4]}")

    # ---- per-slide ----
    tot_words = 0
    tot_sents = 0
    tot_long = 0
    worst: List[Tuple[int, int, str]] = []

    for i, (cls, frag) in enumerate(sl, 1):
        text = visible_text(frag, drop_tabular=True)
        words = text.split()
        n = len(words)
        tot_words += n
        has_fig = 'class="figwrap' in frag
        is_divider = "divider" in cls or "title" in cls
        is_refs = "reference" in title_of(frag).lower()
        cap = MAX_WORDS_FIGURE if has_fig else MAX_WORDS_TEXT
        if is_divider:
            cap = 60
        kind = "divider" if is_divider else ("figure" if has_fig else "text")
        # a citation list is scanned, not read aloud
        if n > cap and not is_refs:
            issues.append(f"[s{i:02d}] {kind} slide holds {n} words of prose "
                          f"(limit {cap}) — {title_of(frag)!r}")

        ss = sentences(text)
        tot_sents += len(ss)
        for s in ss:
            wc = len(s.split())
            if wc > MAX_SENTENCE:
                worst.append((wc, i, s[:88]))

        longw = [w for w in words if len(w.strip(".,;:()—-")) >= 12]
        tot_long += len(longw)
        pct = 100.0 * len(longw) / n if n else 0.0
        if pct > MAX_LONGWORD_PCT and n >= 25:
            issues.append(f"[s{i:02d}] {pct:.0f}% long words (limit "
                          f"{MAX_LONGWORD_PCT:.0f}%) — {title_of(frag)!r}")

        # count rows per table, not per slide: two small tables are fine
        for t_i, tbl in enumerate(re.findall(r"<table.*?</table>", frag, re.S), 1):
            rows = tbl.count("<tr")
            if rows > 10:
                issues.append(f"[s{i:02d}] table {t_i} has {rows} rows "
                              f"(>10 is hard to read from a distance)")

    for wc, i, s in sorted(worst, reverse=True)[:8]:
        issues.append(f"[s{i:02d}] {wc}-word sentence: “{s}…”")

    stats = {
        "slides": len(sl),
        "words_total": tot_words,
        "words_per_slide": round(tot_words / max(1, len(sl)), 1),
        "sentences": tot_sents,
        "words_per_sentence": round(tot_words / max(1, tot_sents), 1),
        "long_word_pct": round(100.0 * tot_long / max(1, tot_words), 1),
        "long_sentences": len(worst),
    }
    return issues, stats


def main() -> int:
    if not os.path.exists(DECK):
        print(f"! {DECK} not found — run build_deck.py first")
        return 2
    with open(DECK, "r", encoding="utf-8") as f:
        html = f.read()

    issues, stats = audit(html)

    print("=" * 74)
    print("Deck audit — presentation.html")
    print("=" * 74)
    for k, v in stats.items():
        print(f"  {k.replace('_', ' '):22} {v}")
    print()
    if issues:
        print(f"{len(issues)} issue(s):\n")
        for it in issues:
            print("  · " + it)
        return 1
    print("No formatting or readability issues found.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

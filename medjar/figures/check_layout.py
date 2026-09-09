#!/usr/bin/env python3
"""
check_layout.py — geometric sanity checks for the generated SVG figures.

The build environment cannot rasterise or visually inspect SVG, so this script
substitutes for a visual review. It flags the layout faults that matter:

  1. connectors (lines / polyline paths) that pass through the interior of a
     box they neither start nor end at;
  2. text that overflows the canvas;
  3. boxes that overlap one another.

Container rectangles (lane bands, zone frames, the background) are excluded by
an area heuristic, since everything legitimately sits inside them.
"""
from __future__ import annotations

import glob
import os
import re
import sys
from typing import List, Optional, Sequence, Tuple

Rect = Tuple[float, float, float, float]
Seg = Tuple[float, float, float, float]


def parse_svg(text: str) -> Tuple[float, float, List[Rect], List[Seg], List[Tuple[float, float]]]:
    vb = re.search(r'viewBox="([\d.\s-]+)"', text)
    _, _, W, H = [float(v) for v in vb.group(1).split()]

    rects: List[Rect] = []
    for m in re.finditer(r'<rect ([^>]+)/>', text):
        at = m.group(1)

        def g(name: str) -> Optional[float]:
            mm = re.search(rf'{name}="(-?[\d.]+)"', at)
            return float(mm.group(1)) if mm else None
        x, y, w, h = g("x"), g("y"), g("width"), g("height")
        if None in (w, h):
            continue
        x, y = x or 0.0, y or 0.0
        stroke = re.search(r'stroke="([^"]+)"', at)
        if stroke and stroke.group(1) == "none":
            continue
        rects.append((x, y, w, h))

    segs: List[Seg] = []
    for m in re.finditer(r'<line ([^>]+)/>', text):
        at = m.group(1)
        v = {}
        for k in ("x1", "y1", "x2", "y2"):
            mm = re.search(rf'{k}="(-?[\d.]+)"', at)
            v[k] = float(mm.group(1)) if mm else 0.0
        segs.append((v["x1"], v["y1"], v["x2"], v["y2"]))

    for m in re.finditer(r'<path d="([^"]+)"', text):
        d = m.group(1)
        if re.search(r'[CQAZcqaz]', d):
            continue
        pts = [(float(a), float(b)) for a, b in
               re.findall(r'[ML](-?[\d.]+),(-?[\d.]+)', d)]
        for i in range(len(pts) - 1):
            segs.append((pts[i][0], pts[i][1], pts[i + 1][0], pts[i + 1][1]))

    texts: List[Tuple[float, float]] = []
    for m in re.finditer(r'<text x="(-?[\d.]+)" y="(-?[\d.]+)"', text):
        texts.append((float(m.group(1)), float(m.group(2))))
    return W, H, rects, segs, texts


def inside(px: float, py: float, r: Rect, pad: float = 3.0) -> bool:
    x, y, w, h = r
    return (x + pad < px < x + w - pad) and (y + pad < py < y + h - pad)


def touches(seg: Seg, r: Rect, pad: float = 3.0) -> bool:
    """True if either endpoint is at/inside the rect (so the segment connects to it)."""
    x1, y1, x2, y2 = seg
    x, y, w, h = r
    for px, py in ((x1, y1), (x2, y2)):
        if (x - pad - 4 <= px <= x + w + pad + 4) and (y - pad - 4 <= py <= y + h + pad + 4):
            return True
    return False


def check(path: str) -> List[str]:
    with open(path, "r", encoding="utf-8") as f:
        text = f.read()
    W, H, rects, segs, texts = parse_svg(text)
    issues: List[str] = []

    # containers excluded from the crossing test
    boxes = [r for r in rects
             if r[2] < 0.55 * W and r[3] < 0.55 * H and r[2] * r[3] < 0.16 * W * H]

    for seg in segs:
        x1, y1, x2, y2 = seg
        length = max(abs(x2 - x1), abs(y2 - y1))
        if length < 4:
            continue
        n = max(6, int(length / 6))
        for r in boxes:
            if touches(seg, r):
                continue
            hits = 0
            for i in range(n + 1):
                t = i / n
                if inside(x1 + (x2 - x1) * t, y1 + (y2 - y1) * t, r):
                    hits += 1
            if hits >= 3:
                issues.append(
                    f"connector ({x1:.0f},{y1:.0f})→({x2:.0f},{y2:.0f}) crosses "
                    f"box at ({r[0]:.0f},{r[1]:.0f},{r[2]:.0f}×{r[3]:.0f})")

    for tx, ty in texts:
        if tx < -20 or tx > W + 20 or ty < 0 or ty > H + 6:
            issues.append(f"text outside canvas at ({tx:.0f},{ty:.0f})")

    def contains(outer: Rect, inner: Rect, pad: float = 2.0) -> bool:
        return (outer[0] - pad <= inner[0]
                and outer[1] - pad <= inner[1]
                and outer[0] + outer[2] + pad >= inner[0] + inner[2]
                and outer[1] + outer[3] + pad >= inner[1] + inner[3])

    for i, a in enumerate(boxes):
        for b in boxes[i + 1:]:
            ox = min(a[0] + a[2], b[0] + b[2]) - max(a[0], b[0])
            oy = min(a[1] + a[3], b[1] + b[3]) - max(a[1], b[1])
            if ox <= 6 or oy <= 6:
                continue
            # full containment is intentional nesting (panel inside a frame)
            if contains(a, b) or contains(b, a):
                continue
            issues.append(
                f"boxes overlap: ({a[0]:.0f},{a[1]:.0f},{a[2]:.0f}×{a[3]:.0f}) "
                f"and ({b[0]:.0f},{b[1]:.0f},{b[2]:.0f}×{b[3]:.0f})")
    return issues


def main(argv: Sequence[str]) -> int:
    here = os.path.dirname(os.path.abspath(__file__))
    files = sorted(glob.glob(os.path.join(here, "*.svg")))
    total = 0
    for f in files:
        issues = check(f)
        name = os.path.basename(f)
        if issues:
            total += len(issues)
            print(f"\n{name}  — {len(issues)} issue(s)")
            for i in issues[:12]:
                print(f"    · {i}")
            if len(issues) > 12:
                print(f"    · … {len(issues) - 12} more")
        else:
            print(f"{name:34} clean")
    print(f"\n{total} issue(s) across {len(files)} figures")
    return 1 if total else 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))

"""
svgkit — a minimal, dependency-free SVG drawing and charting toolkit.

Written for the MedJar figure set: no matplotlib is available in the build
environment, and vector output is preferable for a paper anyway (crisp at any
zoom, renders natively on GitHub, small files).

Provides primitives (text, rect, box, arrow, path) and a small `Axes` class with
bar / line / scatter helpers and automatic data-to-pixel mapping.
"""
from __future__ import annotations

import math
from typing import Dict, Iterable, List, Optional, Sequence, Tuple

# --- house palette (matches the deck and paper) ---------------------------
INK = "#1B1B22"
INK2 = "#3F3F4A"
INK3 = "#6B6B76"
FAINT = "#A9A69C"
RULE = "#D8D4C8"
PAPER = "#FFFFFF"
PAPER2 = "#F4F2EC"
ACCENT = "#8A1524"      # scholarly crimson
SLATE = "#2F4B6E"       # secondary
OCHRE = "#B08322"       # tertiary
GREEN = "#2F6B3F"       # positive / converged
GREY = "#8A8A96"

SANS = "Helvetica Neue, Helvetica, Arial, sans-serif"
MONO = "SF Mono, Consolas, Menlo, monospace"
SERIF = "Georgia, Palatino, serif"

ARROW_COLORS = {"ink3": INK3, "accent": ACCENT, "slate": SLATE,
                "green": GREEN, "ochre": OCHRE, "faint": FAINT}


def esc(s) -> str:
    return (str(s).replace("&", "&amp;").replace("<", "&lt;")
            .replace(">", "&gt;").replace('"', "&quot;"))


class SVG:
    def __init__(self, width: float, height: float, bg: str = PAPER):
        self.w = width
        self.h = height
        self.bg = bg
        self.parts: List[str] = []

    # -- raw ------------------------------------------------------------
    def add(self, xml: str) -> "SVG":
        self.parts.append(xml)
        return self

    # -- primitives -----------------------------------------------------
    def text(self, x: float, y: float, s: str, size: float = 13,
             anchor: str = "start", fill: str = INK, weight: str = "normal",
             style: str = "normal", family: str = SANS,
             spacing: Optional[float] = None, opacity: float = 1.0) -> "SVG":
        ls = f' letter-spacing="{spacing}"' if spacing else ""
        op = f' opacity="{opacity}"' if opacity != 1.0 else ""
        return self.add(
            f'<text x="{x:.1f}" y="{y:.1f}" font-family="{family}" font-size="{size}" '
            f'fill="{fill}" text-anchor="{anchor}" font-weight="{weight}" '
            f'font-style="{style}"{ls}{op}>{esc(s)}</text>')

    def vtext(self, x: float, y: float, s: str, size: float = 12,
              fill: str = INK3, family: str = SANS) -> "SVG":
        """Vertically rotated (y-axis) label."""
        return self.add(
            f'<text x="{x:.1f}" y="{y:.1f}" font-family="{family}" font-size="{size}" '
            f'fill="{fill}" text-anchor="middle" '
            f'transform="rotate(-90 {x:.1f} {y:.1f})">{esc(s)}</text>')

    def wrap(self, x: float, y: float, s: str, width_chars: int, size: float = 12,
             line_h: float = 1.35, anchor: str = "start", fill: str = INK2,
             family: str = SANS, weight: str = "normal") -> "SVG":
        """Naive word wrap at `width_chars`."""
        words, lines, cur = s.split(), [], ""
        for w in words:
            if len(cur) + len(w) + 1 <= width_chars:
                cur = (cur + " " + w).strip()
            else:
                lines.append(cur)
                cur = w
        if cur:
            lines.append(cur)
        for i, ln in enumerate(lines):
            self.text(x, y + i * size * line_h, ln, size=size, anchor=anchor,
                      fill=fill, family=family, weight=weight)
        return self

    def rect(self, x: float, y: float, w: float, h: float, fill: str = "none",
             stroke: str = INK, sw: float = 1.3, rx: float = 3,
             dash: Optional[str] = None, opacity: float = 1.0) -> "SVG":
        d = f' stroke-dasharray="{dash}"' if dash else ""
        op = f' opacity="{opacity}"' if opacity != 1.0 else ""
        return self.add(
            f'<rect x="{x:.1f}" y="{y:.1f}" width="{w:.1f}" height="{h:.1f}" rx="{rx}" '
            f'fill="{fill}" stroke="{stroke}" stroke-width="{sw}"{d}{op}/>')

    def line(self, x1: float, y1: float, x2: float, y2: float, stroke: str = INK,
             sw: float = 1.3, dash: Optional[str] = None,
             opacity: float = 1.0) -> "SVG":
        d = f' stroke-dasharray="{dash}"' if dash else ""
        op = f' opacity="{opacity}"' if opacity != 1.0 else ""
        return self.add(
            f'<line x1="{x1:.1f}" y1="{y1:.1f}" x2="{x2:.1f}" y2="{y2:.1f}" '
            f'stroke="{stroke}" stroke-width="{sw}"{d}{op}/>')

    def path(self, d: str, stroke: str = INK, sw: float = 1.3, fill: str = "none",
             dash: Optional[str] = None, marker: Optional[str] = None,
             opacity: float = 1.0) -> "SVG":
        ds = f' stroke-dasharray="{dash}"' if dash else ""
        mk = f' marker-end="url(#arrow-{marker})"' if marker else ""
        op = f' opacity="{opacity}"' if opacity != 1.0 else ""
        return self.add(f'<path d="{d}" stroke="{stroke}" stroke-width="{sw}" '
                        f'fill="{fill}"{ds}{mk}{op}/>')

    def circle(self, cx: float, cy: float, r: float, fill: str = INK,
               stroke: str = "none", sw: float = 1.0) -> "SVG":
        return self.add(f'<circle cx="{cx:.1f}" cy="{cy:.1f}" r="{r}" fill="{fill}" '
                        f'stroke="{stroke}" stroke-width="{sw}"/>')

    def polyline(self, pts: Sequence[Tuple[float, float]], stroke: str = INK,
                 sw: float = 2.0, dash: Optional[str] = None,
                 fill: str = "none") -> "SVG":
        p = " ".join(f"{x:.1f},{y:.1f}" for x, y in pts)
        d = f' stroke-dasharray="{dash}"' if dash else ""
        return self.add(f'<polyline points="{p}" fill="{fill}" stroke="{stroke}" '
                        f'stroke-width="{sw}"{d}/>')

    # -- composites -----------------------------------------------------
    def box(self, x: float, y: float, w: float, h: float, title: str,
            sub: Optional[str] = None, fill: str = PAPER2, stroke: str = INK,
            sw: float = 1.3, title_size: float = 13, sub_size: float = 10.5,
            title_color: str = INK, accent_bar: Optional[str] = None,
            rx: float = 4, wrap_chars: int = 0) -> "SVG":
        self.rect(x, y, w, h, fill=fill, stroke=stroke, sw=sw, rx=rx)
        if accent_bar:
            self.add(f'<path d="M{x + 1:.1f},{y + 2.5:.1f} L{x + 1:.1f},{y + h - 2.5:.1f}" '
                     f'stroke="{accent_bar}" stroke-width="3.2"/>')
        cx = x + w / 2
        if sub:
            self.text(cx, y + h / 2 - 3, title, size=title_size, anchor="middle",
                      fill=title_color, weight="bold")
            if wrap_chars:
                self.wrap(cx, y + h / 2 + 12, sub, wrap_chars, size=sub_size,
                          anchor="middle", fill=INK3)
            else:
                self.text(cx, y + h / 2 + 12, sub, size=sub_size, anchor="middle",
                          fill=INK3)
        else:
            self.text(cx, y + h / 2 + 4.5, title, size=title_size, anchor="middle",
                      fill=title_color, weight="bold")
        return self

    def numbox(self, x: float, y: float, w: float, h: float, n: str, title: str,
               sub: Optional[str] = None, fill: str = PAPER2,
               stroke: str = INK, accent: str = ACCENT) -> "SVG":
        """Numbered step box."""
        self.rect(x, y, w, h, fill=fill, stroke=stroke, sw=1.3, rx=4)
        self.circle(x + 15, y + 15, 9.5, fill=accent)
        self.text(x + 15, y + 18.8, n, size=10.5, anchor="middle", fill="#FFFFFF",
                  weight="bold", family=MONO)
        self.text(x + 31, y + 19, title, size=12.5, fill=INK, weight="bold")
        if sub:
            self.wrap(x + 12, y + 36, sub, int((w - 22) / 5.4), size=10.2, fill=INK3)
        return self

    def arrow(self, x1: float, y1: float, x2: float, y2: float,
              color: str = "ink3", dash: Optional[str] = None, sw: float = 1.4,
              label: Optional[str] = None, label_size: float = 10,
              label_dy: float = -5, label_color: Optional[str] = None) -> "SVG":
        stroke = ARROW_COLORS.get(color, color)
        self.path(f"M{x1:.1f},{y1:.1f} L{x2:.1f},{y2:.1f}", stroke=stroke, sw=sw,
                  dash=dash, marker=color if color in ARROW_COLORS else "ink3")
        if label:
            mx, my = (x1 + x2) / 2, (y1 + y2) / 2
            self.text(mx, my + label_dy, label, size=label_size, anchor="middle",
                      fill=label_color or stroke)
        return self

    def elbow(self, x1: float, y1: float, x2: float, y2: float, via: str = "h",
              color: str = "ink3", dash: Optional[str] = None, sw: float = 1.4,
              label: Optional[str] = None, label_size: float = 10) -> "SVG":
        """Right-angled connector. via='h' goes horizontal first, 'v' vertical."""
        stroke = ARROW_COLORS.get(color, color)
        if via == "h":
            d = f"M{x1:.1f},{y1:.1f} L{x2:.1f},{y1:.1f} L{x2:.1f},{y2:.1f}"
            lx, ly = (x1 + x2) / 2, y1 - 6
        else:
            d = f"M{x1:.1f},{y1:.1f} L{x1:.1f},{y2:.1f} L{x2:.1f},{y2:.1f}"
            lx, ly = (x1 + x2) / 2, y2 - 6
        self.path(d, stroke=stroke, sw=sw, dash=dash,
                  marker=color if color in ARROW_COLORS else "ink3")
        if label:
            self.text(lx, ly, label, size=label_size, anchor="middle", fill=stroke)
        return self

    def lane(self, x: float, y: float, w: float, h: float, label: str,
             fill: str = "#FBFAF7", label_w: float = 118) -> "SVG":
        """Swimlane band with a left-hand rotated label."""
        self.rect(x, y, w, h, fill=fill, stroke=RULE, sw=1.1, rx=0)
        self.rect(x, y, label_w, h, fill="#F1EEE7", stroke=RULE, sw=1.1, rx=0)
        cy = y + h / 2
        self.add(f'<text x="{x + label_w / 2:.1f}" y="{cy:.1f}" font-family="{SANS}" '
                 f'font-size="11" fill="{INK2}" text-anchor="middle" font-weight="bold" '
                 f'transform="rotate(-90 {x + label_w / 2:.1f} {cy:.1f})">'
                 f'{esc(label)}</text>')
        return self

    def caption_tag(self, x: float, y: float, s: str) -> "SVG":
        """Small uppercase annotation, e.g. ILLUSTRATIVE."""
        return self.text(x, y, s, size=9.5, fill=FAINT, spacing="0.12em",
                         family=SANS)

    def legend(self, x: float, y: float,
               items: Sequence[Tuple[str, str]], size: float = 10.5,
               gap: float = 15, swatch: str = "line",
               horizontal: bool = False, hgap: float = 150) -> "SVG":
        for i, (color, label) in enumerate(items):
            if horizontal:
                ix, iy = x + i * hgap, y
            else:
                ix, iy = x, y + i * gap
            if swatch == "line":
                self.line(ix, iy, ix + 18, iy, stroke=color, sw=2.4)
            else:
                self.rect(ix, iy - 5, 14, 10, fill=color, stroke="none", rx=1)
            self.text(ix + 24, iy + 3.5, label, size=size, fill=INK2)
        return self

    # -- output ---------------------------------------------------------
    def _defs(self) -> str:
        mk = []
        for name, col in ARROW_COLORS.items():
            mk.append(
                f'<marker id="arrow-{name}" markerWidth="8" markerHeight="8" '
                f'refX="6.6" refY="2.6" orient="auto">'
                f'<path d="M0,0 L6.6,2.6 L0,5.2 Z" fill="{col}"/></marker>')
        return "<defs>" + "".join(mk) + "</defs>"

    def render(self) -> str:
        return (f'<svg xmlns="http://www.w3.org/2000/svg" '
                f'viewBox="0 0 {self.w:.0f} {self.h:.0f}" width="{self.w:.0f}" '
                f'height="{self.h:.0f}" font-family="{SANS}">'
                f'{self._defs()}'
                f'<rect width="{self.w:.0f}" height="{self.h:.0f}" fill="{self.bg}"/>'
                + "".join(self.parts) + "</svg>")

    def save(self, path: str) -> str:
        with open(path, "w", encoding="utf-8") as f:
            f.write(self.render())
        return path


# --------------------------------------------------------------------------
class Axes:
    """Cartesian plotting frame with data->pixel mapping."""

    def __init__(self, svg: SVG, x: float, y: float, w: float, h: float,
                 xlim: Tuple[float, float], ylim: Tuple[float, float],
                 xlabel: str = "", ylabel: str = "",
                 xticks: Optional[Sequence[float]] = None,
                 yticks: Optional[Sequence[float]] = None,
                 xtick_labels: Optional[Sequence[str]] = None,
                 ytick_fmt: str = "{:.2f}", grid: bool = True,
                 tick_size: float = 10.5):
        self.s, self.x, self.y, self.w, self.h = svg, x, y, w, h
        self.x0, self.x1 = xlim
        self.y0, self.y1 = ylim

        if grid and yticks:
            for t in yticks:
                py = self.py(t)
                svg.line(x, py, x + w, py, stroke=RULE, sw=1.0)
        # axes
        svg.line(x, y, x, y + h, stroke=INK, sw=1.3)
        svg.line(x, y + h, x + w, y + h, stroke=INK, sw=1.3)
        # ticks
        if yticks:
            for t in yticks:
                py = self.py(t)
                svg.line(x - 4, py, x, py, stroke=INK, sw=1.1)
                svg.text(x - 8, py + 3.5, ytick_fmt.format(t), size=tick_size,
                         anchor="end", fill=INK3)
        if xticks:
            labels = xtick_labels or [f"{t:g}" for t in xticks]
            for t, lb in zip(xticks, labels):
                px = self.px(t)
                svg.line(px, y + h, px, y + h + 4, stroke=INK, sw=1.1)
                svg.text(px, y + h + 17, lb, size=tick_size, anchor="middle", fill=INK3)
        if xlabel:
            svg.text(x + w / 2, y + h + 36, xlabel, size=11.5, anchor="middle", fill=INK2)
        if ylabel:
            svg.vtext(x - 42, y + h / 2, ylabel, size=11.5, fill=INK2)

    # -- mapping --------------------------------------------------------
    def px(self, xv: float) -> float:
        if self.x1 == self.x0:
            return self.x
        return self.x + (xv - self.x0) / (self.x1 - self.x0) * self.w

    def py(self, yv: float) -> float:
        if self.y1 == self.y0:
            return self.y + self.h
        return self.y + self.h - (yv - self.y0) / (self.y1 - self.y0) * self.h

    # -- geometry -------------------------------------------------------
    def vbar(self, xv: float, yv: float, width_px: float, color: str,
             label: Optional[str] = None, label_size: float = 11,
             label_color: Optional[str] = None) -> None:
        px, py = self.px(xv), self.py(yv)
        base = self.py(max(self.y0, 0))
        self.s.rect(px - width_px / 2, min(py, base), width_px, abs(base - py),
                    fill=color, stroke="none", rx=1.5)
        if label:
            self.s.text(px, py - 7, label, size=label_size, anchor="middle",
                        fill=label_color or INK, weight="bold")

    def hbar(self, yv: float, xv: float, height_px: float, color: str,
             label: Optional[str] = None, label_size: float = 11) -> None:
        px, py = self.px(xv), self.py(yv)
        base = self.px(max(self.x0, 0))
        self.s.rect(min(px, base), py - height_px / 2, abs(px - base), height_px,
                    fill=color, stroke="none", rx=1.5)
        if label:
            self.s.text(px + 6, py + 3.8, label, size=label_size, fill=INK,
                        weight="bold")

    def plot(self, pts: Sequence[Tuple[float, float]], color: str = ACCENT,
             sw: float = 2.3, dash: Optional[str] = None, marker_r: float = 3.6,
             marker: bool = True) -> None:
        ppts = [(self.px(a), self.py(b)) for a, b in pts]
        self.s.polyline(ppts, stroke=color, sw=sw, dash=dash)
        if marker:
            for cx, cy in ppts:
                self.s.circle(cx, cy, marker_r, fill=color)

    def hline(self, yv: float, color: str = INK3, dash: str = "5 4",
              sw: float = 1.2, label: Optional[str] = None,
              label_anchor: str = "end") -> None:
        py = self.py(yv)
        self.s.line(self.x, py, self.x + self.w, py, stroke=color, sw=sw, dash=dash)
        if label:
            lx = self.x + self.w - 4 if label_anchor == "end" else self.x + 4
            self.s.text(lx, py - 6, label, size=10.5, anchor=label_anchor, fill=color)

    def diagonal(self, color: str = INK3, dash: str = "4 4") -> None:
        self.s.line(self.px(self.x0), self.py(self.y0), self.px(self.x1),
                    self.py(self.y1), stroke=color, sw=1.2, dash=dash)

    def annotate(self, xv: float, yv: float, s: str, size: float = 10.5,
                 color: str = INK2, anchor: str = "start", dx: float = 6,
                 dy: float = 0) -> None:
        self.s.text(self.px(xv) + dx, self.py(yv) + dy, s, size=size,
                    anchor=anchor, fill=color)

"""
A small, dependency-free PDF generation engine.

Font metrics for the PDF base-14 Times / Helvetica families are read from the
Adobe AFM-derived font description files that ship with groff, so text
measurement (and therefore justification) is exact.
"""

import os
import re
import zlib

# ---------------------------------------------------------------- page geometry
PAGE_W, PAGE_H = 612.0, 792.0          # US Letter, matching the reference doc
ML, MR = 36.0, 36.0                    # left / right margin  (0.5 inch)
CONTENT_W = PAGE_W - ML - MR           # 540 pt
BODY_TOP = 92.0                        # first baseline area, below the header
BODY_BOTTOM = 722.0                    # last usable y (top-down coords)
FOOTER_Y = 741.0                       # footer baseline (top-down coords)

# ---------------------------------------------------------------- font metrics
GROFF_DIR = "/usr/share/groff/1.22.4/font/devps"

FONT_FILES = {
    "Times-Roman": "TR",
    "Times-Bold": "TB",
    "Times-Italic": "TI",
    "Times-BoldItalic": "TBI",
    "Helvetica": "HR",
    "Helvetica-Bold": "HB",
    "Helvetica-Oblique": "HI",
    "Helvetica-BoldOblique": "HBI",
}

# PDF font resource names
FONT_RES = {name: "F%d" % (i + 1) for i, name in enumerate(FONT_FILES)}

_ASCII_NAMES = {
    32: "space", 33: "exclam", 34: "quotedbl", 35: "numbersign", 36: "dollar",
    37: "percent", 38: "ampersand", 39: "quotesingle", 40: "parenleft",
    41: "parenright", 42: "asterisk", 43: "plus", 44: "comma", 45: "hyphen",
    46: "period", 47: "slash", 48: "zero", 49: "one", 50: "two", 51: "three",
    52: "four", 53: "five", 54: "six", 55: "seven", 56: "eight", 57: "nine",
    58: "colon", 59: "semicolon", 60: "less", 61: "equal", 62: "greater",
    63: "question", 64: "at", 91: "bracketleft", 92: "backslash",
    93: "bracketright", 94: "asciicircum", 95: "underscore", 96: "quoteleft",
    123: "braceleft", 124: "bar", 125: "braceright", 126: "asciitilde",
}
for _c in range(65, 91):
    _ASCII_NAMES[_c] = chr(_c)
for _c in range(97, 123):
    _ASCII_NAMES[_c] = chr(_c)

# characters beyond ASCII that the document actually uses (cp1252 encodable)
_EXTRA_NAMES = {
    "\u2018": "quoteleft", "\u2019": "quoteright",
    "\u201c": "quotedblleft", "\u201d": "quotedblright",
    "\u2013": "endash", "\u2014": "emdash", "\u2022": "bullet",
    "\u00a7": "section", "\u00a9": "copyright", "\u00ae": "registered",
    "\u2122": "trademark", "\u00b0": "degree", "\u00b7": "periodcentered",
    "\u00bd": "onehalf", "\u00a3": "sterling", "\u20ac": "Euro",
    "\u00e9": "eacute", "\u00a0": "space", "\u2026": "ellipsis",
}


def _parse_groff_font(path):
    """Return {psname: width} from a groff devps font description file."""
    widths = {}
    prev = None
    in_charset = False
    with open(path, "r", encoding="latin-1") as fh:
        for line in fh:
            line = line.rstrip("\n")
            if not in_charset:
                if line.strip() == "charset":
                    in_charset = True
                continue
            if not line.strip():
                continue
            parts = line.split("\t")
            if len(parts) < 2:
                continue
            if parts[1].strip() == '"':
                # alias of the previous glyph; the psname column is absent
                continue
            metrics = parts[1].split(",")
            try:
                w = float(metrics[0])
            except ValueError:
                continue
            psname = parts[-1].strip() if len(parts) >= 5 else parts[0].strip()
            if psname and psname not in widths:
                widths[psname] = w
            prev = psname
    return widths


class Metrics:
    def __init__(self):
        self.tables = {}
        for font, stem in FONT_FILES.items():
            self.tables[font] = _parse_groff_font(os.path.join(GROFF_DIR, stem))
        self.missing = set()

    def char_width(self, font, ch):
        table = self.tables[font]
        o = ord(ch)
        if o < 127:
            name = _ASCII_NAMES.get(o)
        else:
            name = _EXTRA_NAMES.get(ch)
        if name is None:
            self.missing.add(ch)
            return 500.0
        w = table.get(name)
        if w is None:
            self.missing.add(ch + "/" + name)
            return 500.0
        return w

    def width(self, text, font, size):
        t = self.tables[font]
        total = 0.0
        for ch in text:
            o = ord(ch)
            name = _ASCII_NAMES.get(o) if o < 127 else _EXTRA_NAMES.get(ch)
            w = t.get(name) if name else None
            if w is None:
                self.missing.add(ch)
                w = 500.0
            total += w
        return total * size / 1000.0


M = Metrics()


# ---------------------------------------------------------------- font families
SERIF = {"": "Times-Roman", "b": "Times-Bold", "i": "Times-Italic",
         "bi": "Times-BoldItalic"}
SANS = {"": "Helvetica", "b": "Helvetica-Bold", "i": "Helvetica-Oblique",
        "bi": "Helvetica-BoldOblique"}


def sw(text, style, size, family=SERIF):
    return M.width(text, family[style], size)


# ---------------------------------------------------------------- colours
BLACK = (0, 0, 0)
WHITE = (1, 1, 1)
CU_RED = (0.79, 0.10, 0.13)
DARK_RED = (0.55, 0.06, 0.09)
NAVY = (0.13, 0.26, 0.42)
GREY = (0.45, 0.45, 0.45)
LGREY = (0.62, 0.62, 0.62)
TBL_HEAD = (0.851, 0.882, 0.949)
CASE_BG = (0.996, 0.949, 0.949)
CASE_BORDER = (0.75, 0.10, 0.13)
TEAL = (0.11, 0.47, 0.42)
ORANGE = (0.83, 0.55, 0.05)
SLATE = (0.36, 0.40, 0.47)
BOXFILL = (0.945, 0.949, 0.957)


def esc(s):
    out = []
    for ch in s:
        if ch in "()\\":
            out.append("\\" + ch)
        else:
            try:
                b = ch.encode("cp1252")
            except UnicodeEncodeError:
                b = b"?"
            if b[0] < 32 or b[0] > 126:
                out.append("\\%03o" % b[0])
            else:
                out.append(chr(b[0]))
    return "".join(out)


# ---------------------------------------------------------------- canvas
class Canvas:
    def __init__(self):
        self.ops = []
        self.zone = "body"
        self.marks = []          # (zone, x0, y0, x1, y1) in top-down coords

    def _mark(self, x0, y0, x1, y1):
        self.marks.append((self.zone, min(x0, x1), min(y0, y1),
                           max(x0, x1), max(y0, y1)))

    # -- primitives (all y values are top-down page coordinates) --
    def _y(self, y):
        return PAGE_H - y

    def text(self, x, y, s, font, size, color=BLACK, char_space=None):
        if not s:
            return
        self._mark(x, y - size * 0.9, x + M.width(s, font, size), y + size * 0.25)
        self.ops.append("BT")
        self.ops.append("%.4f %.4f %.4f rg" % color)
        if char_space:
            self.ops.append("%.3f Tc" % char_space)
        self.ops.append("/%s %.2f Tf" % (FONT_RES[font], size))
        self.ops.append("1 0 0 1 %.2f %.2f Tm" % (x, self._y(y)))
        self.ops.append("(%s) Tj" % esc(s))
        if char_space:
            self.ops.append("0 Tc")
        self.ops.append("ET")

    def rect(self, x, y, w, h, fill=None, stroke=None, lw=0.6):
        if fill is None and stroke is None:
            return
        self._mark(x, y, x + w, y + h)
        if fill:
            self.ops.append("%.4f %.4f %.4f rg" % fill)
        if stroke:
            self.ops.append("%.4f %.4f %.4f RG" % stroke)
            self.ops.append("%.2f w" % lw)
        self.ops.append("%.2f %.2f %.2f %.2f re" % (x, self._y(y + h), w, h))
        if fill and stroke:
            self.ops.append("B")
        elif fill:
            self.ops.append("f")
        else:
            self.ops.append("S")

    def round_rect(self, x, y, w, h, r, fill=None, stroke=None, lw=0.6):
        self._mark(x, y, x + w, y + h)
        k = 0.5523 * r
        y0 = self._y(y + h)
        y1 = self._y(y)
        p = []
        p.append("%.2f %.2f m" % (x + r, y0))
        p.append("%.2f %.2f l" % (x + w - r, y0))
        p.append("%.2f %.2f %.2f %.2f %.2f %.2f c" % (x + w - r + k, y0, x + w, y0 + r - k, x + w, y0 + r))
        p.append("%.2f %.2f l" % (x + w, y1 - r))
        p.append("%.2f %.2f %.2f %.2f %.2f %.2f c" % (x + w, y1 - r + k, x + w - r + k, y1, x + w - r, y1))
        p.append("%.2f %.2f l" % (x + r, y1))
        p.append("%.2f %.2f %.2f %.2f %.2f %.2f c" % (x + r - k, y1, x, y1 - r + k, x, y1 - r))
        p.append("%.2f %.2f l" % (x, y0 + r))
        p.append("%.2f %.2f %.2f %.2f %.2f %.2f c" % (x, y0 + r - k, x + r - k, y0, x + r, y0))
        if fill:
            self.ops.append("%.4f %.4f %.4f rg" % fill)
        if stroke:
            self.ops.append("%.4f %.4f %.4f RG" % stroke)
            self.ops.append("%.2f w" % lw)
        self.ops.extend(p)
        self.ops.append("h")
        if fill and stroke:
            self.ops.append("B")
        elif fill:
            self.ops.append("f")
        else:
            self.ops.append("S")

    def line(self, x1, y1, x2, y2, color=BLACK, lw=0.6, dash=None):
        self._mark(x1, y1, x2, y2)
        self.ops.append("%.4f %.4f %.4f RG" % color)
        self.ops.append("%.2f w" % lw)
        if dash:
            self.ops.append("[%s] 0 d" % dash)
        self.ops.append("%.2f %.2f m %.2f %.2f l S" % (x1, self._y(y1), x2, self._y(y2)))
        if dash:
            self.ops.append("[] 0 d")

    def arrow(self, x1, y1, x2, y2, color=BLACK, lw=0.8, head=4.0):
        import math
        ang = math.atan2(-(y2 - y1), x2 - x1)
        bx = x2 - head * math.cos(ang)
        by = y2 + head * math.sin(ang)
        self.line(x1, y1, bx, by, color, lw)
        lx = x2 - head * 1.25 * math.cos(ang - 0.42)
        ly = y2 + head * 1.25 * math.sin(ang - 0.42)
        rx = x2 - head * 1.25 * math.cos(ang + 0.42)
        ry = y2 + head * 1.25 * math.sin(ang + 0.42)
        self.ops.append("%.4f %.4f %.4f rg" % color)
        self.ops.append("%.2f %.2f m %.2f %.2f l %.2f %.2f l h f"
                        % (x2, self._y(y2), lx, self._y(ly), rx, self._y(ry)))

    # -- convenience text helpers --
    def ctext(self, cx, y, s, font, size, color=BLACK):
        w = M.width(s, font, size)
        self.text(cx - w / 2.0, y, s, font, size, color)

    def rtext(self, rx, y, s, font, size, color=BLACK):
        w = M.width(s, font, size)
        self.text(rx - w, y, s, font, size, color)

    def stream(self):
        return "\n".join(self.ops).encode("latin-1")


# ---------------------------------------------------------------- rich text
_TOKEN = re.compile(r"\*\*(.+?)\*\*|__(.+?)__|\*(.+?)\*")


def parse_runs(s):
    """'**bold** and *italic*' -> [(text, style), ...]"""
    runs = []
    pos = 0
    for m in _TOKEN.finditer(s):
        if m.start() > pos:
            runs.append((s[pos:m.start()], ""))
        if m.group(1) is not None:
            runs.append((m.group(1), "b"))
        elif m.group(2) is not None:
            runs.append((m.group(2), "bi"))
        else:
            runs.append((m.group(3), "i"))
        pos = m.end()
    if pos < len(s):
        runs.append((s[pos:], ""))
    return [r for r in runs if r[0]]


def runs_to_words(runs):
    words = []
    for text, style in runs:
        parts = text.split(" ")
        for i, p in enumerate(parts):
            if p == "":
                continue
            words.append([p, style])
    return words


def wrap(words, width, size, family=SERIF, first_indent=0.0):
    """Greedy wrap. Returns list of lines; each line is a list of [word,style,w]."""
    space = {st: sw(" ", st, size, family) for st in ("", "b", "i", "bi")}
    lines = []
    cur = []
    curw = 0.0
    avail = width - first_indent
    for word, style in words:
        w = sw(word, style, size, family)
        add = w if not cur else space[style] + w
        if cur and curw + add > avail + 0.01:
            lines.append(cur)
            cur = [[word, style, w]]
            curw = w
            avail = width
        else:
            cur.append([word, style, w])
            curw += add
    if cur:
        lines.append(cur)
    return lines


# ---------------------------------------------------------------- document
class Doc:
    def __init__(self, footer_left, footer_right, header_fn):
        self.pages = []
        self.canvas = None
        self.y = 0.0
        self.footer_left = footer_left
        self.footer_right = footer_right
        self.header_fn = header_fn
        self.new_page()

    def new_page(self):
        self.canvas = Canvas()
        self.pages.append(self.canvas)
        c = self.canvas
        c.zone = "header"
        self.header_fn(c)
        c.zone = "footer"
        c.text(ML, FOOTER_Y, self.footer_left, "Times-Bold", 11)
        c.text(ML + 359, FOOTER_Y, self.footer_right, "Times-Bold", 11)
        c.zone = "body"
        self.y = BODY_TOP

    def validate(self):
        """Assert nothing spills outside the page or the body text block."""
        problems = []
        for pno, c in enumerate(self.pages, start=1):
            for zone, x0, y0, x1, y1 in c.marks:
                if x0 < -0.6 or x1 > PAGE_W + 0.6 or y0 < -0.6 or y1 > PAGE_H + 0.6:
                    problems.append("p%d %s off-page %.1f,%.1f-%.1f,%.1f"
                                    % (pno, zone, x0, y0, x1, y1))
                if zone == "body":
                    if x0 < ML - 1.0 or x1 > PAGE_W - MR + 1.0:
                        problems.append("p%d body x out of margins %.1f-%.1f"
                                        % (pno, x0, x1))
                    if y1 > BODY_BOTTOM + 1.0 or y0 < BODY_TOP - 14.0:
                        problems.append("p%d body y out of block %.1f-%.1f"
                                        % (pno, y0, y1))
        return problems

    def space(self, h):
        if self.y + h > BODY_BOTTOM:
            return
        self.y += h

    def ensure(self, h):
        if self.y + h > BODY_BOTTOM:
            self.new_page()
            return True
        return False

    def avail(self):
        return BODY_BOTTOM - self.y

    # ---------------------------------------------------------- blocks
    def para(self, text, size=11, leading=13.6, space_before=0.0,
             space_after=9.0, justify=True, family=SERIF, indent=0.0,
             align="left", color=BLACK, keep_with_next=False):
        self.space(space_before)
        words = runs_to_words(parse_runs(text))
        width = CONTENT_W - indent
        lines = wrap(words, width, size, family)
        if keep_with_next and self.avail() < leading * min(3, len(lines)) + 24:
            self.new_page()
        for i, line in enumerate(lines):
            if self.y + leading > BODY_BOTTOM:
                self.new_page()
            last = (i == len(lines) - 1)
            self._draw_line(ML + indent, self.y + size * 0.86, line, size,
                            width, family, justify and not last, align, color)
            self.y += leading
        self.y += space_after

    def _draw_line(self, x, baseline, line, size, width, family, justify,
                   align="left", color=BLACK):
        space_w = sw(" ", "", size, family)
        natural = sum(w for _, _, w in line) + space_w * (len(line) - 1)
        extra = 0.0
        if justify and len(line) > 1:
            extra = (width - natural) / (len(line) - 1)
            if extra > space_w * 2.2:
                extra = 0.0
        if align == "center":
            x = x + (width - natural) / 2.0
        elif align == "right":
            x = x + (width - natural)
        cx = x
        for word, style, w in line:
            self.canvas.text(cx, baseline, word, family[style], size, color)
            cx += w + space_w + extra

    def heading(self, text, size=12, space_before=13.0, space_after=8.0):
        need = size + space_after + 30
        if self.y + space_before + need > BODY_BOTTOM:
            self.new_page()
        else:
            self.y += space_before
        self.canvas.text(ML, self.y + size * 0.86, text, "Times-Bold", size)
        self.y += size * 1.22
        self.y += space_after

    def bullets(self, items, size=11, leading=13.6, bullet="\u2022",
                indent=18.0, gap=6.0, space_before=0.0, space_after=9.0,
                marker_font="Times-Roman"):
        self.space(space_before)
        for n, item in enumerate(items):
            words = runs_to_words(parse_runs(item))
            width = CONTENT_W - indent - gap
            lines = wrap(words, width, size)
            if self.y + leading * min(2, len(lines)) > BODY_BOTTOM:
                self.new_page()
            mark = bullet if bullet != "#" else "%d." % (n + 1)
            for i, line in enumerate(lines):
                if self.y + leading > BODY_BOTTOM:
                    self.new_page()
                if i == 0:
                    self.canvas.text(ML + indent - 12, self.y + size * 0.86,
                                     mark, marker_font, size)
                last = (i == len(lines) - 1)
                self._draw_line(ML + indent + gap, self.y + size * 0.86, line,
                                size, width, SERIF, not last)
                self.y += leading
            self.y += 2.0
        self.y += space_after

    def numbered(self, items, size=11, leading=13.6, indent=24.0, gap=6.0,
                 space_before=0.0, space_after=9.0, start=1):
        self.space(space_before)
        for n, item in enumerate(items):
            words = runs_to_words(parse_runs(item))
            width = CONTENT_W - indent - gap
            lines = wrap(words, width, size)
            if self.y + leading * min(2, len(lines)) > BODY_BOTTOM:
                self.new_page()
            mark = "%d." % (n + start)
            for i, line in enumerate(lines):
                if self.y + leading > BODY_BOTTOM:
                    self.new_page()
                if i == 0:
                    self.canvas.rtext(ML + indent - 4, self.y + size * 0.86,
                                      mark, "Times-Roman", size)
                last = (i == len(lines) - 1)
                self._draw_line(ML + indent + gap, self.y + size * 0.86, line,
                                size, width, SERIF, not last)
                self.y += leading
            self.y += 3.0
        self.y += space_after

    # ---------------------------------------------------------- table
    def table(self, caption, header, rows, widths, size=10, leading=12.2,
              pad=4.0, space_before=6.0, space_after=11.0, align=None):
        total = sum(widths)
        colw = [CONTENT_W * w / total for w in widths]

        def cell_lines(txt, cw):
            return wrap(runs_to_words(parse_runs(txt)), cw - 2 * pad, size)

        def row_h(cells):
            n = 1
            for txt, cw in zip(cells, colw):
                n = max(n, len(cell_lines(txt, cw)))
            return n * leading + 2 * pad

        hh = row_h(header)
        cap_h = 0.0
        if caption:
            cap_h = 15.0

        # caption + header + at least one row must fit
        first_row_h = row_h(rows[0]) if rows else 0
        if self.y + space_before + cap_h + hh + first_row_h > BODY_BOTTOM:
            self.new_page()
        else:
            self.y += space_before

        def draw_caption():
            self.canvas.ctext(ML + CONTENT_W / 2.0, self.y + 8.4, caption,
                              "Times-Bold", 10)
            self.y += 14.0

        def draw_row(cells, h, bold=False, fill=None):
            x = ML
            for i, (txt, cw) in enumerate(zip(cells, colw)):
                self.canvas.rect(x, self.y, cw, h, fill=fill, stroke=BLACK, lw=0.6)
                lines = cell_lines(txt, cw)
                by = self.y + pad + size * 0.85
                for line in lines:
                    a = (align or ["left"] * len(colw))[i] if align else "left"
                    self._draw_line(x + pad, by, line, size, cw - 2 * pad,
                                    SERIF, False, a)
                    by += leading
                x += cw
            self.y += h

        if caption:
            draw_caption()
        hdr = [("**%s**" % h if not h.startswith("**") else h) for h in header]
        draw_row(hdr, hh, fill=TBL_HEAD)
        for r in rows:
            h = row_h(r)
            if self.y + h > BODY_BOTTOM:
                self.new_page()
                draw_row(hdr, hh, fill=TBL_HEAD)
            draw_row(r, h)
        self.y += space_after

    # ---------------------------------------------------------- case box
    def casebox(self, text, size=10, leading=12.4, pad=7.0, space_before=6.0,
                space_after=12.0):
        words = runs_to_words(parse_runs(text))
        width = CONTENT_W - 2 * pad - 2
        lines = wrap(words, width, size)
        self.space(space_before)
        if self.avail() < leading * 3 + 2 * pad:
            self.new_page()
        i = 0
        n = len(lines)
        while i < n:
            room = BODY_BOTTOM - self.y - 2 * pad
            fit = max(1, int(room // leading))
            chunk = lines[i:i + fit]
            h = len(chunk) * leading + 2 * pad
            self.canvas.rect(ML, self.y, CONTENT_W, h, fill=CASE_BG,
                             stroke=CASE_BORDER, lw=0.9)
            by = self.y + pad + size * 0.85
            for j, line in enumerate(chunk):
                last = (i + j == n - 1)
                self._draw_line(ML + pad + 1, by, line, size, width, SERIF,
                                not last)
                by += leading
            self.y += h
            i += fit
            if i < n:
                self.new_page()
        self.y += space_after

    # ---------------------------------------------------------- figure
    def figure(self, height, draw, caption, space_before=8.0, space_after=12.0):
        if self.y + space_before + height + 16 > BODY_BOTTOM:
            self.new_page()
        else:
            self.y += space_before
        draw(self.canvas, ML, self.y, CONTENT_W)
        self.y += height + 4
        # italic centered caption
        words = runs_to_words([(caption, "i")])
        lines = wrap(words, CONTENT_W, 10)
        for line in lines:
            self._draw_line(ML, self.y + 8.4, line, 10, CONTENT_W, SERIF,
                            False, "center")
            self.y += 12.0
        self.y += space_after

    # ---------------------------------------------------------- output
    def save(self, path):
        objs = []          # list of bytes bodies, 1-indexed

        def add(body):
            objs.append(body)
            return len(objs)

        font_ids = {}
        for name in FONT_FILES:
            font_ids[name] = add(
                ("<< /Type /Font /Subtype /Type1 /BaseFont /%s "
                 "/Encoding /WinAnsiEncoding >>" % name).encode())

        res = "<< /Font << " + " ".join(
            "/%s %d 0 R" % (FONT_RES[n], font_ids[n]) for n in FONT_FILES
        ) + " >> >>"
        res_id = add(res.encode())

        pages_id = add(b"PLACEHOLDER")
        page_ids = []
        for c in self.pages:
            data = zlib.compress(c.stream())
            sid = add(b"<< /Length %d /Filter /FlateDecode >>\nstream\n" % len(data)
                      + data + b"\nendstream")
            pid = add(("<< /Type /Page /Parent %d 0 R /MediaBox [0 0 %.2f %.2f] "
                       "/Resources %d 0 R /Contents %d 0 R >>"
                       % (pages_id, PAGE_W, PAGE_H, res_id, sid)).encode())
            page_ids.append(pid)

        objs[pages_id - 1] = ("<< /Type /Pages /Count %d /Kids [%s] >>"
                              % (len(page_ids),
                                 " ".join("%d 0 R" % p for p in page_ids))).encode()
        cat_id = add(("<< /Type /Catalog /Pages %d 0 R >>" % pages_id).encode())
        info_id = add(b"<< /Title (Experiment 1.4 - Copyright and Related Rights) "
                      b"/Author (Mohammad Saood) /Creator (Kiro) >>")

        out = bytearray(b"%PDF-1.4\n%\xe2\xe3\xcf\xd3\n")
        offsets = []
        for i, body in enumerate(objs, start=1):
            offsets.append(len(out))
            out += ("%d 0 obj\n" % i).encode() + body + b"\nendobj\n"
        xref = len(out)
        out += ("xref\n0 %d\n" % (len(objs) + 1)).encode()
        out += b"0000000000 65535 f \n"
        for off in offsets:
            out += ("%010d 00000 n \n" % off).encode()
        out += ("trailer\n<< /Size %d /Root %d 0 R /Info %d 0 R >>\nstartxref\n%d\n%%%%EOF\n"
                % (len(objs) + 1, cat_id, info_id, xref)).encode()
        with open(path, "wb") as fh:
            fh.write(bytes(out))
        return len(self.pages)

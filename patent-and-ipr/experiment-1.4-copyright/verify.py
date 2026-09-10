#!/usr/bin/env python3
"""Structural + layout verification of the generated PDF, with no external deps.

- walks the xref table and checks every offset resolves to "<n> 0 obj"
- inflates every content stream and re-parses the text operators
- rebuilds a plain-text view of each page so the flow can be proof-read
- flags text that overruns the right margin or overlaps horizontally
"""
import re
import sys
import zlib

PATH = sys.argv[1] if len(sys.argv) > 1 else \
    "Experiment_1.4_Copyright_Mohammad_Saood.pdf"
data = open(PATH, "rb").read()

# ---------------------------------------------------------------- structure
m = re.search(rb"startxref\s+(\d+)\s+%%EOF\s*$", data)
assert m, "no startxref/EOF"
xref_off = int(m.group(1))
assert data[xref_off:xref_off + 4] == b"xref", "startxref does not point at xref"
hdr = re.match(rb"xref\s+0 (\d+)\s+", data[xref_off:])
size = int(hdr.group(1))
body = data[xref_off + hdr.end():]
entries = re.findall(rb"(\d{10}) (\d{5}) ([nf])", body[: size * 20])
assert len(entries) == size, "xref entry count %d != %d" % (len(entries), size)
bad = []
for i, (off, gen, kind) in enumerate(entries):
    if kind == b"f":
        continue
    o = int(off)
    if not re.match(rb"%d 0 obj" % i, data[o:o + 20]):
        bad.append(i)
assert not bad, "broken xref offsets for objects %r" % bad
trailer = re.search(rb"trailer\s*<<(.+?)>>", data, re.S).group(1)
assert b"/Root" in trailer and b"/Size" in trailer
print("structure: %d objects, xref consistent, trailer OK" % (size - 1))

# ---------------------------------------------------------------- page order
kids = re.search(rb"/Type /Pages /Count (\d+) /Kids \[(.+?)\]", data)
count = int(kids.group(1))
page_ids = [int(x) for x in re.findall(rb"(\d+) 0 R", kids.group(2))]
assert len(page_ids) == count
objs = {}
for i, (off, gen, kind) in enumerate(entries):
    if kind == b"f":
        continue
    o = int(off)
    end = data.find(b"\nendobj", o)
    objs[i] = data[o:end]

contents = []
for pid in page_ids:
    b = objs[pid]
    cid = int(re.search(rb"/Contents (\d+) 0 R", b).group(1))
    sb = objs[cid]
    raw = sb[sb.index(b"stream\n") + 7: sb.rindex(b"\nendstream")]
    contents.append(zlib.decompress(raw).decode("latin-1"))
print("pages: %d, all content streams inflate cleanly" % len(contents))

# ---------------------------------------------------------------- text replay
from pdfgen import M, FONT_RES, PAGE_H, ML, MR, PAGE_W

RES2FONT = {v: k for k, v in FONT_RES.items()}
UNESC = {"\\(": "(", "\\)": ")", "\\\\": "\\"}


def unesc(s):
    out = []
    i = 0
    while i < len(s):
        if s[i] == "\\":
            if s[i + 1:i + 2].isdigit():
                out.append(bytes([int(s[i + 1:i + 4], 8)]).decode("cp1252"))
                i += 4
            else:
                out.append(s[i + 1])
                i += 2
        else:
            out.append(s[i])
            i += 1
    return "".join(out)


problems = []
pages_text = []
for pno, cs in enumerate(contents, start=1):
    font = None
    size = 0.0
    items = []
    for blk in cs.split("\nBT\n")[1:]:
        blk = blk.split("\nET\n")[0]
        fm = re.search(r"/(F\d+) ([\d.]+) Tf", blk)
        if fm:
            font = RES2FONT[fm.group(1)]
            size = float(fm.group(2))
        tm = re.search(r"1 0 0 1 ([-\d.]+) ([-\d.]+) Tm", blk)
        tj = re.search(r"\((.*)\) Tj", blk, re.S)
        if not (tm and tj):
            continue
        x = float(tm.group(1))
        y = PAGE_H - float(tm.group(2))
        s = unesc(tj.group(1))
        w = M.width(s, font, size)
        items.append((y, x, x + w, s, size, font))
        if x + w > PAGE_W - MR + 1.2 and size >= 9:
            problems.append("p%d right-margin overrun x=%.1f..%.1f %r"
                            % (pno, x, x + w, s[:40]))
    items.sort(key=lambda t: (round(t[0], 1), t[1]))
    # horizontal overlap on the same baseline
    for a, b in zip(items, items[1:]):
        if abs(a[0] - b[0]) < 0.4 and a[2] > b[1] + 0.6:
            problems.append("p%d overlap %r | %r" % (pno, a[3][:25], b[3][:25]))
    # rebuild readable lines
    lines = []
    cur_y = None
    buf = []
    for y, x0, x1, s, sz, fn in items:
        if cur_y is None or abs(y - cur_y) > 0.6:
            if buf:
                lines.append((cur_y, buf))
            cur_y = y
            buf = []
        buf.append((x0, s))
    if buf:
        lines.append((cur_y, buf))
    out = []
    for y, parts in lines:
        row = ""
        for x0, s in parts:
            col = int(round(x0 / 4.6))
            if len(row) < col:
                row += " " * (col - len(row))
            row += s
        out.append(row)
    pages_text.append((pno, out))

if problems:
    print("PROBLEMS (%d):" % len(problems))
    for p in problems[:60]:
        print("  " + p)
else:
    print("no margin overruns, no overlapping text runs")

with open("pagedump.txt", "w") as fh:
    for pno, out in pages_text:
        fh.write("\n" + "=" * 100 + "\nPAGE %d\n" % pno + "=" * 100 + "\n")
        fh.write("\n".join(out) + "\n")
print("wrote pagedump.txt")

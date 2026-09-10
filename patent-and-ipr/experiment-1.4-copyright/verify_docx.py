#!/usr/bin/env python3
"""Validate the generated .docx: XML well-formedness, relationship integrity,
part completeness, and a readable text dump for proof-reading."""
import re
import sys
import zipfile
import xml.etree.ElementTree as ET

PATH = sys.argv[1] if len(sys.argv) > 1 else \
    "Experiment_1.4_Copyright_Mohammad_Saood.docx"
z = zipfile.ZipFile(PATH)
names = z.namelist()
problems = []

# ---- 1. every XML part parses
for n in names:
    if n.endswith(".xml") or n.endswith(".rels"):
        try:
            ET.fromstring(z.read(n))
        except ET.ParseError as e:
            problems.append("XML parse error in %s: %s" % (n, e))
print("parsed %d XML parts" % sum(1 for n in names
                                  if n.endswith(('.xml', '.rels'))))

# ---- 2. required parts present
need = ["[Content_Types].xml", "_rels/.rels", "word/document.xml",
        "word/styles.xml", "word/numbering.xml", "word/header1.xml",
        "word/footer1.xml", "word/_rels/document.xml.rels",
        "word/_rels/header1.xml.rels"]
for n in need:
    if n not in names:
        problems.append("missing part: " + n)

# ---- 3. relationship integrity: every r:id/r:embed used resolves,
#         and every relationship target exists
R = "{http://schemas.openxmlformats.org/officeDocument/2006/relationships}"
for part in ["word/document.xml", "word/header1.xml", "word/footer1.xml"]:
    relpart = part.rsplit("/", 1)[0] + "/_rels/" + part.rsplit("/", 1)[1] + ".rels"
    rels = {}
    if relpart in names:
        for rel in ET.fromstring(z.read(relpart)):
            rels[rel.get("Id")] = rel.get("Target")
    xml = z.read(part).decode("utf-8")
    used = set(re.findall(r'r:(?:id|embed)="([^"]+)"', xml))
    for u in used:
        if u not in rels:
            problems.append("%s references unknown relationship %s" % (part, u))
        else:
            tgt = rels[u]
            if not tgt.startswith(("http", "mailto")):
                full = "word/" + tgt.lstrip("/")
                if full not in names:
                    problems.append("%s -> %s missing target %s"
                                    % (part, u, full))
    for rid, tgt in rels.items():
        if tgt.startswith(("http", "mailto")):
            continue
        full = "word/" + tgt.lstrip("/")
        if full not in names:
            problems.append("dangling relationship %s in %s -> %s"
                            % (rid, relpart, full))
    print("%-22s uses %d rels, all resolve" % (part, len(used)))

# ---- 4. content types cover every extension in the package
ct = z.read("[Content_Types].xml").decode("utf-8")
exts = {n.rsplit(".", 1)[-1].lower() for n in names if "." in n.rsplit("/", 1)[-1]}
for e in exts:
    if ('Extension="%s"' % e) not in ct and not re.search(
            r'PartName="/[^"]+\.%s"' % e, ct):
        problems.append("no content-type declared for .%s" % e)
print("extensions in package:", sorted(exts))

# ---- 5. structural counts + text dump
doc = z.read("word/document.xml").decode("utf-8")
print("tables: %d   paragraphs: %d   images in body: %d"
      % (doc.count("<w:tbl>"), doc.count("<w:p>"), doc.count("<w:drawing>")))
print("Experiment title:",
      re.search(r"Experiment: [\d.]+", doc).group(0))
# markers unique to Experiment 1.3; the generic word "trademark" is excluded
# because the copyright text refers to trademark law deliberately.
for marker in ["Experiment: 1.3", "Trade Marks Act", "Hybo Hindustan",
               "Cadila", "MAAZA", "Hardie Trading", "TM-A", "TM-R",
               "Nice Classification", "2(1)(zb)", "Agmark",
               "Registrar of Trade Marks", "service mark", "collective mark",
               "certification mark", "well-known mark"]:
    if marker in doc:
        problems.append("leftover Experiment 1.3 content: %r" % marker)

d2 = re.sub(r"</w:p>", "\n", doc)
d2 = re.sub(r"</w:tr>", "\n", d2)
d2 = re.sub(r"</w:tc>", " | ", d2)
import html
txt = html.unescape(re.sub(r"<[^>]+>", "", d2))
open("dump14.txt", "w", encoding="utf-8").write(txt)
print("wrote dump14.txt (%d chars of text)" % len(txt))

caps = re.findall(r"(Table \d+ \u2014 [^<|\n]+)", txt)
print("\ncaptions found (%d):" % len(caps))
for c in caps:
    print("  ", c.strip())
nums = [int(re.match(r"Table (\d+)", c).group(1)) for c in caps]
if nums != list(range(1, len(nums) + 1)):
    problems.append("table numbering not sequential: %r" % nums)

heads = re.findall(r"^(\d\.\s[A-Z][^\n|]{4,70})$", txt, re.M)
print("\nsection headings:")
for h in heads:
    print("  ", h.strip())

if problems:
    print("\nPROBLEMS (%d):" % len(problems))
    for p in problems:
        print("  -", p)
    sys.exit(1)
print("\nALL CHECKS PASSED")

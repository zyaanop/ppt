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

# ---- slide content -------------------------------------------------------
# Slide text lives in pptx_slides.py so the deck copy can be edited without
# touching the Office Open XML rendering code below.
from pptx_slides import SLIDES  # noqa: E402

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

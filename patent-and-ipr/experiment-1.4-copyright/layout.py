"""Page header/branding block and the vector figures for Experiment 1.4."""

from pdfgen import (M, BLACK, WHITE, CU_RED, DARK_RED, NAVY, GREY, LGREY,
                    TEAL, ORANGE, SLATE, BOXFILL, TBL_HEAD)

# --------------------------------------------------------------- page header
_CSE_W = 238.0
_CSE = "COMPUTER SCIENCE & ENGINEERING"
_CSE_SIZE = _CSE_W / M.width(_CSE, "Helvetica-Bold", 1.0)


def header(c):
    # --- Chandigarh University crest block ---
    bx, by, bw, bh = 40.0, 19.0, 34.0, 56.0
    c.rect(bx, by, bw, bh, fill=(0.36, 0.05, 0.07))
    cx = bx + bw / 2.0
    # emblem: pale disc with a dark inner mark
    c.round_rect(cx - 8.5, by + 4.0, 17.0, 17.0, 8.5, fill=(0.93, 0.90, 0.86))
    c.round_rect(cx - 5.0, by + 7.5, 10.0, 10.0, 5.0, fill=(0.62, 0.10, 0.12))
    c.line(cx, by + 6.0, cx, by + 19.5, (0.36, 0.05, 0.07), 0.7)
    c.line(cx - 6.5, by + 12.7, cx + 6.5, by + 12.7, (0.36, 0.05, 0.07), 0.7)
    c.ctext(cx, by + 38.0, "CU", "Helvetica-Bold", 15.0, WHITE)
    c.ctext(cx, by + 46.5, "CHANDIGARH", "Helvetica-Bold", 3.4, WHITE)
    c.ctext(cx, by + 51.0, "UNIVERSITY", "Helvetica-Bold", 3.4, WHITE)

    # --- department wordmark ---
    tx = 84.0
    c.text(tx, 39.0, "DEPARTMENT OF", "Helvetica-Bold", _CSE_SIZE, CU_RED)
    c.text(tx, 57.0, _CSE, "Helvetica-Bold", _CSE_SIZE, (0.10, 0.16, 0.30))
    c.line(tx, 62.0, tx + _CSE_W, 62.0, CU_RED, 1.4)
    c.text(tx, 72.0, "Discover.  Learn.  Empower.", "Helvetica", 8.0,
           (0.42, 0.42, 0.45))

    # --- NAAC A+ accreditation badge ---
    nx = 474.0
    c.text(nx, 34.0, "NAAC", "Helvetica-Bold", 11.5, (0.08, 0.08, 0.08))
    c.text(nx, 56.0, "GRADE", "Helvetica-Bold", 16.0, (0.08, 0.08, 0.08))
    c.round_rect(524.0, 30.0, 38.0, 28.0, 4.0, fill=CU_RED)
    c.ctext(543.0, 53.0, "A+", "Helvetica-Bold", 21.0, WHITE)
    c.line(nx, 59.5, 562.0, 59.5, (0.08, 0.08, 0.08), 1.2)
    c.ctext(518.0, 66.5, "ACCREDITED UNIVERSITY", "Helvetica-Bold", 5.6,
            (0.08, 0.08, 0.08))


# --------------------------------------------------------------- figure tools
def box(c, x, y, w, h, lines, fill=None, stroke=None, tcolor=BLACK,
        size=7.0, font="Helvetica-Bold", lead=None, r=0.0, lw=0.7):
    if r:
        c.round_rect(x, y, w, h, r, fill=fill, stroke=stroke, lw=lw)
    else:
        c.rect(x, y, w, h, fill=fill, stroke=stroke, lw=lw)
    if isinstance(lines, str):
        lines = [lines]
    lead = lead or size * 1.22
    total = len(lines) * lead
    base = y + (h - total) / 2.0 + lead - size * 0.34
    for ln in lines:
        c.ctext(x + w / 2.0, base, ln, font, size, tcolor)
        base += lead


def ltext(c, x, y, s, size=7.0, font="Helvetica", color=BLACK):
    c.text(x, y, s, font, size, color)


# --------------------------------------------------------------- Figure 1
def fig1(c, x, y, w):
    """Three layers of protection under the Copyright Act."""
    top_w = 330.0
    box(c, x + (w - top_w) / 2.0, y, top_w, 21.0,
        "COPYRIGHT  \u2014  THE COPYRIGHT ACT, 1957", fill=DARK_RED,
        tcolor=WHITE, size=10.0)

    gap = 12.0
    bw = (w - 2 * gap) / 3.0
    centres = [x + i * (bw + gap) + bw / 2.0 for i in range(3)]
    # connector
    c.line(x + w / 2.0, y + 21.0, x + w / 2.0, y + 31.0, BLACK, 0.8)
    c.line(centres[0], y + 31.0, centres[2], y + 31.0, BLACK, 0.8)
    for cxx in centres:
        c.arrow(cxx, y + 31.0, cxx, y + 43.0, BLACK, 0.8, 3.6)

    heads = [
        ("ECONOMIC RIGHTS \u2014 S. 14", NAVY),
        ("MORAL RIGHTS \u2014 S. 57", TEAL),
        ("RELATED RIGHTS \u2014 S. 37-38B", SLATE),
    ]
    subs = [
        ["Reproduction and electronic storage",
         "Issue of copies to the public",
         "Public performance / communication",
         "Adaptation and translation",
         "Commercial rental \u2014 software, films"],
        ["Right of paternity \u2014 to be named",
         "Right of integrity \u2014 no distortion",
         "Independent of the economic rights",
         "Survives assignment of copyright",
         "Enforceable by the legal heirs"],
        ["Performers' rights \u2014 S. 38, 38A",
         "Performer's moral rights \u2014 S. 38B",
         "Producers of sound recordings",
         "Broadcast reproduction right \u2014 S. 37",
         "No originality test is applied"],
    ]
    hy = y + 43.0
    for i in range(3):
        bx = x + i * (bw + gap)
        box(c, bx, hy, bw, 19.0, heads[i][0], fill=heads[i][1], tcolor=WHITE,
            size=7.6)
        sy = hy + 22.0
        for s in subs[i]:
            box(c, bx, sy, bw, 13.5, s, fill=BOXFILL, stroke=(0.72, 0.74, 0.78),
                size=6.4, font="Helvetica", lw=0.5)
            sy += 15.0
    note_y = hy + 22.0 + 5 * 15.0 + 9.0
    c.ctext(x + w / 2.0, note_y,
            "Protection is automatic on creation \u00b7 registration is optional "
            "and only evidentiary \u00b7 every term is finite",
            "Helvetica-Oblique", 6.6, GREY)


FIG1_H = 43.0 + 22.0 + 5 * 15.0 + 14.0


# --------------------------------------------------------------- Figure 2
def fig2(c, x, y, w):
    """Layered rights in a single film song."""
    c.ctext(x + w / 2.0, y + 9.0,
            "Layered Rights in a Single Film Song", "Helvetica-Bold", 10.0,
            (0.10, 0.16, 0.30))
    top = y + 18.0
    bw, bh = 176.0, 40.0
    cw, ch = 108.0, 46.0
    ccx = x + w / 2.0
    ccy = top + 22.0

    # centre
    box(c, ccx - cw / 2.0, ccy, cw, ch, ["THE FILM", "SONG"], fill=(0.09, 0.11, 0.16),
        tcolor=WHITE, size=9.0)

    left_x = x
    right_x = x + w - bw

    def unit(bx, by, title, tcolor, lines):
        c.rect(bx, by, bw, bh, fill=WHITE, stroke=tcolor, lw=1.0)
        c.text(bx + 6.0, by + 12.5, title, "Helvetica-Bold", 7.6, tcolor)
        yy = by + 23.0
        for ln in lines:
            c.text(bx + 6.0, yy, ln, "Helvetica", 6.4, (0.20, 0.20, 0.20))
            yy += 8.2
        return bx, by

    unit(left_x, top, "LYRICIST", CU_RED,
         ["Literary work in the lyrics", "Author = the writer of the words"])
    unit(left_x, top + 52.0, "COMPOSER", TEAL,
         ["Musical work in the composition", "Author = the composer"])
    unit(right_x, top, "SINGER & MUSICIANS", (0.10, 0.16, 0.30),
         ["Performer's right, S. 38 and 38A", "Moral rights under S. 38B"])
    unit(right_x, top + 52.0, "PRODUCER", ORANGE,
         ["Sound recording and the film", "First owner under S. 2(d), 17"])

    # arrows into the centre
    c.arrow(left_x + bw + 2, top + bh / 2.0, ccx - cw / 2.0 - 2, ccy + 10.0,
            (0.45, 0.45, 0.45), 0.8)
    c.arrow(left_x + bw + 2, top + 52.0 + bh / 2.0, ccx - cw / 2.0 - 2,
            ccy + ch - 10.0, (0.45, 0.45, 0.45), 0.8)
    c.arrow(right_x - 2, top + bh / 2.0, ccx + cw / 2.0 + 2, ccy + 10.0,
            (0.45, 0.45, 0.45), 0.8)
    c.arrow(right_x - 2, top + 52.0 + bh / 2.0, ccx + cw / 2.0 + 2,
            ccy + ch - 10.0, (0.45, 0.45, 0.45), 0.8)

    # broadcaster below
    by = top + 104.0
    c.arrow(ccx, ccy + ch, ccx, by - 2.0, (0.45, 0.45, 0.45), 0.8)
    box(c, ccx - 150.0, by, 300.0, 20.0,
        "BROADCASTER \u2014 broadcast reproduction right, S. 37, 25 years",
        fill=WHITE, stroke=SLATE, size=7.0, tcolor=(0.15, 0.15, 0.15), lw=0.9)


FIG2_H = 18.0 + 104.0 + 20.0 + 6.0


# --------------------------------------------------------------- Figure 3
def fig3(c, x, y, w):
    """Section 13 categories: primary works and entrepreneurial works."""
    lw_ = 250.0
    rw_ = 250.0
    lx = x
    rx = x + w - rw_
    box(c, lx, y, lw_, 20.0, "PRIMARY (ORIGINAL) WORKS \u2014 S. 13(1)(a)",
        fill=NAVY, tcolor=WHITE, size=8.0)
    box(c, rx, y, rw_, 20.0, "ENTREPRENEURIAL WORKS \u2014 S. 13(1)(b), (c)",
        fill=DARK_RED, tcolor=WHITE, size=8.0)

    left_items = [
        "LITERARY \u2014 books, articles, source code, tables, compilations",
        "DRAMATIC \u2014 plays, screenplays, scenarios, choreography",
        "MUSICAL \u2014 the composition and its graphical notation",
        "ARTISTIC \u2014 paintings, drawings, maps, charts, photographs",
    ]
    right_items = [
        "CINEMATOGRAPH FILM \u2014 S. 2(f), any work of visual recording",
        "SOUND RECORDING \u2014 S. 2(xx), any recording of sounds",
    ]
    yy = y + 25.0
    for it in left_items:
        box(c, lx, yy, lw_, 15.0, it, fill=BOXFILL, stroke=(0.72, 0.74, 0.78),
            size=6.4, font="Helvetica", lw=0.5)
        yy += 17.0
    ry = y + 25.0
    for it in right_items:
        box(c, rx, ry, rw_, 15.0, it, fill=BOXFILL, stroke=(0.72, 0.74, 0.78),
            size=6.4, font="Helvetica", lw=0.5)
        ry += 17.0
    box(c, rx, ry + 4.0, rw_, 26.0,
        ["An entrepreneurial work is a container: it absorbs the",
         "underlying works but never extinguishes their own copyright"],
        fill=(0.99, 0.95, 0.95), stroke=CU_RED, size=6.4,
        font="Helvetica-Oblique", tcolor=(0.35, 0.10, 0.12), lw=0.7)
    # absorbing arrow
    c.arrow(lx + lw_ + 3.0, y + 50.0, rx - 3.0, y + 50.0, CU_RED, 1.0, 4.5)

    bottom = y + 25.0 + 4 * 17.0 + 8.0
    box(c, x, bottom, w, 17.0,
        "OUTSIDE COPYRIGHT ALTOGETHER \u2014 ideas \u00b7 themes and plots \u00b7 "
        "facts and news \u00b7 methods and procedures \u00b7 titles and slogans \u00b7 "
        "unfixed expression",
        fill=(0.93, 0.93, 0.93), stroke=(0.60, 0.60, 0.60), size=6.4,
        font="Helvetica", tcolor=(0.25, 0.25, 0.25), lw=0.6)


FIG3_H = 25.0 + 4 * 17.0 + 8.0 + 17.0 + 4.0


# --------------------------------------------------------------- Figure 4
_TERMS = [
    ("Broadcast reproduction\nright", 25, "25 years from the year of the broadcast \u2014 S. 37", SLATE),
    ("Performer's right", 50, "50 years from the year of the performance \u2014 S. 38", ORANGE),
    ("Sound recording", 60, "60 years from publication \u2014 S. 27", TEAL),
    ("Cinematograph film", 60, "60 years from publication \u2014 S. 26", TEAL),
    ("Government / PSU\nwork", 60, "60 years from first publication \u2014 S. 28, 28A", NAVY),
    ("Anonymous or\npseudonymous work", 60, "60 years from first publication \u2014 S. 23", NAVY),
    ("Photograph", 80, "Author's lifetime + 60 years (S. 25 omitted in 2012)", CU_RED),
    ("Literary, dramatic,\nmusical, artistic", 80, "Author's lifetime + 60 years \u2014 S. 22", CU_RED),
]


def fig4(c, x, y, w):
    c.ctext(x + w / 2.0, y + 10.0,
            "Term of Protection Compared \u2014 Indian Copyright and Related Rights",
            "Helvetica-Bold", 10.0, (0.10, 0.16, 0.30))
    top = y + 20.0
    lab_w = 104.0
    plot_x = x + lab_w
    plot_w = 150.0
    scale = plot_w / 100.0
    rowh = 15.5
    n = len(_TERMS)
    for i, (label, val, note, col) in enumerate(_TERMS):
        ry = top + i * rowh
        parts = label.split("\n")
        if len(parts) == 1:
            c.rtext(plot_x - 6.0, ry + 9.5, parts[0], "Helvetica", 6.6, BLACK)
        else:
            c.rtext(plot_x - 6.0, ry + 6.0, parts[0], "Helvetica", 6.6, BLACK)
            c.rtext(plot_x - 6.0, ry + 13.0, parts[1], "Helvetica", 6.6, BLACK)
        c.line(plot_x - 3.0, ry + 8.0, plot_x, ry + 8.0, BLACK, 0.5)
        bh = 8.5
        c.rect(plot_x, ry + 8.0 - bh / 2.0, val * scale, bh, fill=col)
        c.text(plot_x + val * scale + 5.0, ry + 10.5, note, "Helvetica", 6.4,
               (0.20, 0.20, 0.20))
    axis_y = top + n * rowh + 2.0
    c.line(plot_x, axis_y, plot_x + plot_w + 2.0, axis_y, BLACK, 0.7)
    c.line(plot_x, top - 2.0, plot_x, axis_y, BLACK, 0.7)
    for t in (0, 20, 40, 60, 80, 100):
        tx = plot_x + t * scale
        c.line(tx, axis_y, tx, axis_y + 3.0, BLACK, 0.6)
        c.ctext(tx, axis_y + 11.0, str(t), "Helvetica", 6.4, BLACK)
    c.ctext(plot_x + plot_w / 2.0, axis_y + 21.0,
            "Approximate duration of exclusivity (years)", "Helvetica", 6.8,
            (0.25, 0.25, 0.25))


FIG4_H = 20.0 + len(_TERMS) * 15.5 + 26.0


# --------------------------------------------------------------- Figure 5
_STAGES = [
    ("1  Creation", "Original expression is", "fixed in a tangible form", NAVY),
    ("2  Notice", "\u00a9 symbol, author, year;", "internal date records", NAVY),
    ("3  Registration", "Form XIV, 30-day wait,", "entry in the Register", DARK_RED),
    ("4  Exploitation", "Assignment (S. 18-19),", "licence (S. 30), societies", NAVY),
    ("5  Monitoring", "Market and online", "surveillance for copies", NAVY),
    ("6  Takedown", "Notice under the IT Rules;", "S. 65A / 65B on DRM", DARK_RED),
    ("7  Enforcement", "S. 55 injunction, damages;", "S. 63 criminal complaint", NAVY),
    ("8  Expiry", "Term ends on 31 December;", "work enters public domain", NAVY),
]


def fig5(c, x, y, w):
    c.ctext(x + w / 2.0, y + 10.0, "The Copyright Protection Lifecycle",
            "Helvetica-Bold", 10.5, (0.10, 0.16, 0.30))
    top = y + 20.0
    cols = 4
    gap = 14.0
    bw = (w - (cols - 1) * gap) / cols
    for i, (title, l1, l2, col) in enumerate(_STAGES):
        r, cidx = divmod(i, cols)
        bx = x + cidx * (bw + gap)
        byy = top + r * 62.0
        box(c, bx, byy, bw, 20.0, title, fill=col, tcolor=WHITE, size=8.4)
        c.ctext(bx + bw / 2.0, byy + 30.0, l1, "Helvetica", 6.3, (0.25, 0.25, 0.25))
        c.ctext(bx + bw / 2.0, byy + 38.0, l2, "Helvetica", 6.3, (0.25, 0.25, 0.25))
        if cidx < cols - 1:
            c.arrow(bx + bw + 2.0, byy + 10.0, bx + bw + gap - 2.0, byy + 10.0,
                    (0.35, 0.35, 0.35), 0.9, 3.6)
    c.ctext(x + w / 2.0, top + 62.0 + 50.0,
            "Stages 1-3 establish the right   |   Stages 4-6 preserve and "
            "monetise it   |   Stages 7-8 defend and release it",
            "Helvetica-Oblique", 6.8, GREY)


FIG5_H = 20.0 + 62.0 + 50.0 + 8.0


# --------------------------------------------------------------- Figure 6
def fig6(c, x, y, w):
    cxm = x + w / 2.0
    rows = [
        (300.0, 20.0, "Ministry of Commerce and Industry", (0.09, 0.11, 0.16), WHITE, 9.0),
        (330.0, 24.0, "DPIIT \u2014 Department for Promotion of Industry and Internal Trade",
         NAVY, WHITE, 8.0),
        (330.0, 24.0, "CGPDTM \u2014 Controller General of Patents, Designs and Trade Marks",
         DARK_RED, WHITE, 8.0),
    ]
    yy = y
    for bw, bh, label, fill, tc, sz in rows:
        box(c, cxm - bw / 2.0, yy, bw, bh, label, fill=fill, tcolor=tc, size=sz)
        yy += bh
        c.arrow(cxm, yy, cxm, yy + 12.0, BLACK, 0.8, 3.6)
        yy += 12.0

    leaves = [
        ("Registrar of\nCopyrights", "Copyright Office, New Delhi\nRegister of Copyrights"),
        ("Copyright\nSocieties \u2014 S. 33", "IPRS \u00b7 PPL \u00b7 ISRA \u00b7 SCRIPT\nTariff and distribution schemes"),
        ("Commercial\nCourts", "Hear copyright suits since the\nTribunals Reforms Act, 2021"),
    ]
    gap = 16.0
    bw = (w - 2 * gap) / 3.0
    c.line(x + bw / 2.0, yy - 12.0, x + w - bw / 2.0, yy - 12.0, BLACK, 0.8)
    for i, (title, note) in enumerate(leaves):
        bx = x + i * (bw + gap)
        c.arrow(bx + bw / 2.0, yy - 12.0, bx + bw / 2.0, yy - 2.0, BLACK, 0.8, 3.4)
        box(c, bx, yy, bw, 30.0, title.split("\n"), fill=BOXFILL,
            stroke=(0.55, 0.58, 0.62), size=7.6, tcolor=(0.12, 0.12, 0.12))
        ny = yy + 39.0
        for ln in note.split("\n"):
            c.ctext(bx + bw / 2.0, ny, ln, "Helvetica", 6.3, GREY)
            ny += 8.0
    bottom = yy + 58.0
    box(c, x + 40.0, bottom, w - 80.0, 20.0,
        "The Copyright Office was transferred from the Ministry of Human Resource "
        "Development to DPIIT in 2016",
        fill=WHITE, stroke=(0.55, 0.58, 0.62), size=6.6, font="Helvetica",
        tcolor=(0.20, 0.20, 0.20), lw=0.6)


FIG6_H = (20.0 + 12.0) + (24.0 + 12.0) + (24.0 + 12.0) + 58.0 + 20.0 + 4.0

# Experiment 1.4 — Copyright and Related Rights

**Subject:** Patent and IPR (26CSP – 626) · **Student:** Mohammad Saood (26MAI10040) ·
**Branch:** M.E. (CSE) (AIML), Section B

**Deliverable:** [`Experiment_1.4_Copyright_Mohammad_Saood.pdf`](Experiment_1.4_Copyright_Mohammad_Saood.pdf) — 16 pages.

## Aim

An article and case study on what a copyright is and the rights related to it, the types
of work protected by copyright, the authorship and ownership of copyright, and the
duration of copyright protection.

## Contents of the document

| § | Section | Includes |
|---|---|---|
| 1 | What a copyright actually is | Table 1 — the statutory and treaty framework |
| 2 | The rights conferred, and related rights | Figure 1, Figure 2, Tables 2–3; Amar Nath Sehgal, Neha Bhasin |
| 3 | Types of work protected | Figure 3, Table 4; Eastern Book Co. v. Modak, R. G. Anand v. Delux Films |
| 4 | Authorship and ownership | Tables 5–7; IPRS v. EIMPA, V. T. Thomas v. Malayala Manorama |
| 5 | Duration of copyright | Figure 4, Tables 8–9; the Tagore public-domain episode |
| 6 | Registration, infringement and remedies | Figure 5, Tables 10–11; UTV Software v. 1337x |
| 7 | Administration of copyright in India | Figure 6, Table 12 |
| 8 | Viva questions and answers | 10 questions |
| 9 | Learning outcomes | Mapped to CO3 / BT1–BT3 |

## Rebuilding the PDF

The PDF is generated, not hand-authored. No third-party packages are used — the
generator is a small PDF writer that takes its font metrics from the Adobe AFM data
shipped with groff, so text measurement and justification are exact.

```sh
python3 build.py      # writes Experiment_1.4_Copyright_Mohammad_Saood.pdf
python3 verify.py     # checks the xref, inflates every stream, dumps a text view
```

| File | Role |
|---|---|
| `pdfgen.py` | PDF writer, font metrics, and the flowing layout engine (paragraphs, tables that repeat their header across a page break, case-study boxes, figures) |
| `layout.py` | The page header block and the six vector figures |
| `build.py` | The document itself — all the prose, tables and case studies |
| `verify.py` | Structural and layout verification; writes `pagedump.txt` |

`build.py` fails with a non-zero exit code if any element lands outside the page or the
text block, and `verify.py` reports right-margin overruns and overlapping text runs.

**Requirements:** Python 3 (standard library only) and the groff font descriptions at
`/usr/share/groff/*/font/devps` — adjust `GROFF_DIR` in `pdfgen.py` if that path differs.

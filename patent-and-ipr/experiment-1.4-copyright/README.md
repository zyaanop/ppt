# Experiment 1.4 — Copyright and Related Rights

**Subject:** Patent and IPR (26CSP – 626) · **Student:** Mohammad Saood (26MAI10040) ·
**Branch:** M.E. (CSE) (AIML), Section B · **CO Mapping:** CO3 · BT1, BT2, BT3

**Deliverable:** [`Experiment_1.4_Copyright_Mohammad_Saood.docx`](Experiment_1.4_Copyright_Mohammad_Saood.docx)

## Aim

An article and case study on (a) what a copyright is and the rights related to it,
(b) the types of work protected by copyright, (c) the authorship and ownership of
copyright, and (d) the duration of copyright.

## How this was produced

It is the Experiment 1.3 submission (trademarks) with its body replaced. The
university header image, the footer, `styles.xml`, `numbering.xml`, the page size and
margins, and the student-details block are carried over untouched, so the formatting
is identical to the previous submission rather than an imitation of it.

| File | Role |
|---|---|
| `Experiment_1.4_Copyright_Mohammad_Saood.docx` | The submission |
| `template-experiment-1.3-trademarks.docx` | The source document that was edited |
| `build_docx.py` | Rewrites `word/document.xml` with the Experiment 1.4 body |
| `verify_docx.py` | Validates the result and writes a text dump for proof-reading |

```sh
python3 build_docx.py     # regenerates the .docx from the template
python3 verify_docx.py    # parses every part, checks relationships, dumps the text
```

Only the standard library is used — a `.docx` is a ZIP of XML parts, which `zipfile`
and `xml.etree` handle without any third-party package.

## Contents of the document

| § | Section | Includes |
|---|---|---|
| 1 | The nature of copyright | Table 1 — statutes and treaties |
| 1.1 | Rights conferred by copyright | Table 2 — Section 14 rights by category; moral rights under Section 57 · *Amar Nath Sehgal* |
| 1.2 | Rights related to copyright | Tables 3–4 — performers, phonogram producers, broadcasters; neighbouring rights in Germany and France · *Neha Bhasin* |
| 2 | Types of work protected | Table 5 — the Section 13 categories |
| 2.1 | What copyright does not protect | *Eastern Book Co. v. Modak* · *R. G. Anand v. Delux Films* |
| 3 | Authorship and ownership | Table 6 — authors under Section 2(d); Table 7 — first owners under Section 17; Table 8 — the two distinguished · *IPRS v. EIMPA* · *V. T. Thomas* |
| 4 | Duration of copyright | Table 9 — term by category; Table 10 — international comparison · the Tagore public-domain episode |
| 5 | Viva questions and answers | 10 questions |
| 6 | Learning outcomes | 7 outcomes |

10 numbered tables, 7 case studies.

## Verification

`build_docx.py` asserts that the preamble it copies really contains the title it is
replacing and that the dropped image relationship is gone. `verify_docx.py` then
checks the finished file independently:

- all 22 XML parts parse
- every `r:id` / `r:embed` resolves to a relationship whose target exists in the package
- no dangling relationships, and a content type is declared for every extension
- table captions are numbered 1…10 with no gaps
- no Experiment 1.3 content survives anywhere in the body

Both currently report `ALL CHECKS PASSED`.

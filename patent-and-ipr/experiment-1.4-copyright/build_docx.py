#!/usr/bin/env python3
"""Rewrite the Experiment template (ipre3 = Exp 1.3, trademarks) as Experiment 1.4
on copyright, keeping every formatting idiom, the header logo image, the footer,
styles and numbering exactly as they are in the source document."""

import os
import re
import zipfile

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(HERE, "template-experiment-1.3-trademarks.docx")
OUT = os.path.join(HERE, "Experiment_1.4_Copyright_Mohammad_Saood.docx")

# the body flowchart PNG belongs to Experiment 1.3 only
DROP_MEDIA = "word/media/70a36272c461e5f43ed72c888e81b8263b09c9a9.png"
DROP_REL_ID = "rId9"

TNR = ('<w:rFonts w:ascii="Times New Roman" w:cs="Times New Roman"'
       ' w:eastAsia="Times New Roman" w:hAnsi="Times New Roman"/>')


def esc(t):
    return (t.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;"))


def rpr(b=False, i=False, sz=24):
    x = TNR
    if b:
        x += "<w:b/><w:bCs/>"
    if i:
        x += "<w:i/><w:iCs/>"
    x += '<w:sz w:val="%d"/><w:szCs w:val="%d"/>' % (sz, sz)
    return "<w:rPr>" + x + "</w:rPr>"


def r(t, b=False, i=False, sz=24):
    return ("<w:r>" + rpr(b, i, sz)
            + '<w:t xml:space="preserve">' + esc(t) + "</w:t></w:r>")


_BOLD = re.compile(r"\*\*(.+?)\*\*")


def runs(text, sz=24, i=False):
    """'plain **bold** plain' -> run sequence"""
    out = []
    pos = 0
    for m in _BOLD.finditer(text):
        if m.start() > pos:
            out.append(r(text[pos:m.start()], sz=sz, i=i))
        out.append(r(m.group(1), b=True, sz=sz, i=i))
        pos = m.end()
    if pos < len(text):
        out.append(r(text[pos:], sz=sz, i=i))
    return "".join(out)


def para(inner, spacing="", jc=None, ind="", style=None, num=None):
    ppr = ""
    if style:
        ppr += '<w:pStyle w:val="%s"/>' % style
    if num:
        ppr += ('<w:numPr><w:ilvl w:val="0"/><w:numId w:val="%d"/></w:numPr>'
                % num)
    ppr += spacing + ind
    if jc:
        ppr += '<w:jc w:val="%s"/>' % jc
    return "<w:p>" + ("<w:pPr>%s</w:pPr>" % ppr if ppr else "") + inner + "</w:p>"


# ---------------------------------------------------------------- block styles
SP_BODY = '<w:spacing w:after="100" w:before="100" w:line="240" w:lineRule="auto"/>'
SP_H1 = '<w:spacing w:after="120" w:before="240"/>'
SP_H2 = '<w:spacing w:after="100" w:before="200"/>'
SP_CAP = '<w:spacing w:after="80" w:before="160"/>'
SP_CASE = '<w:spacing w:after="60" w:before="60" w:line="240" w:lineRule="auto"/>'
SP_Q = '<w:spacing w:after="60" w:before="160"/>'
SP_A = '<w:spacing w:after="60" w:line="240" w:lineRule="auto"/>'
SP_BUL = '<w:spacing w:after="60" w:before="60" w:line="240" w:lineRule="auto"/>'

BODY = []


def body(text):
    BODY.append(para(runs(text), SP_BODY, jc="both"))


def h1(text):
    BODY.append(para(r(text, b=True, sz=27), SP_H1))


def h2(text):
    BODY.append(para(r(text, b=True, sz=25), SP_H2))


def caption(text):
    BODY.append(para(r(text, b=True, sz=22), SP_CAP, jc="center"))


TBL_PR = ('<w:tblPr><w:tblW w:type="dxa" w:w="10080"/><w:jc w:val="center"/>'
          '<w:tblBorders>'
          '<w:top w:val="single" w:color="auto" w:sz="4"/>'
          '<w:left w:val="single" w:color="auto" w:sz="4"/>'
          '<w:bottom w:val="single" w:color="auto" w:sz="4"/>'
          '<w:right w:val="single" w:color="auto" w:sz="4"/>'
          '<w:insideH w:val="single" w:color="auto" w:sz="4"/>'
          '<w:insideV w:val="single" w:color="auto" w:sz="4"/>'
          '</w:tblBorders></w:tblPr>')

CELL_BORDERS = ('<w:tcBorders>'
                '<w:top w:val="single" w:color="999999" w:sz="4"/>'
                '<w:left w:val="single" w:color="999999" w:sz="4"/>'
                '<w:bottom w:val="single" w:color="999999" w:sz="4"/>'
                '<w:right w:val="single" w:color="999999" w:sz="4"/>'
                '</w:tcBorders>')
CELL_MAR = ('<w:tcMar><w:top w:type="dxa" w:w="60"/>'
            '<w:left w:type="dxa" w:w="100"/>'
            '<w:bottom w:type="dxa" w:w="60"/>'
            '<w:right w:type="dxa" w:w="100"/></w:tcMar>')


def cell(text, w, head=False):
    tcpr = '<w:tcPr><w:tcW w:type="dxa" w:w="%d"/>%s' % (w, CELL_BORDERS)
    if head:
        tcpr += '<w:shd w:fill="D9E2F3" w:color="auto" w:val="clear"/>'
    tcpr += CELL_MAR + '<w:vAlign w:val="center"/></w:tcPr>'
    inner = r(text, b=True, sz=22) if head else runs(text, sz=22)
    return "<w:tc>" + tcpr + "<w:p>" + inner + "</w:p></w:tc>"


def table(widths, header, rows, cap):
    assert sum(widths) == 10080, sum(widths)
    x = ["<w:tbl>", TBL_PR, "<w:tblGrid>"]
    x += ['<w:gridCol w:w="%d"/>' % w for w in widths]
    x.append("</w:tblGrid>")
    x.append("<w:tr><w:trPr><w:tblHeader/></w:trPr>")
    x += [cell(t, w, head=True) for t, w in zip(header, widths)]
    x.append("</w:tr>")
    for row in rows:
        x.append("<w:tr>")
        x += [cell(t, w) for t, w in zip(row, widths)]
        x.append("</w:tr>")
    x.append("</w:tbl>")
    BODY.append("".join(x))
    caption(cap)


def casebox(lead, text):
    tcpr = ('<w:tcPr><w:tcW w:type="dxa" w:w="10080"/>'
            '<w:tcBorders>'
            '<w:top w:val="single" w:color="B01C2E" w:sz="6"/>'
            '<w:left w:val="single" w:color="B01C2E" w:sz="6"/>'
            '<w:bottom w:val="single" w:color="B01C2E" w:sz="6"/>'
            '<w:right w:val="single" w:color="B01C2E" w:sz="6"/>'
            '</w:tcBorders>'
            '<w:shd w:fill="FDF2F3" w:color="auto" w:val="clear"/>'
            '<w:tcMar><w:top w:type="dxa" w:w="100"/>'
            '<w:left w:type="dxa" w:w="140"/>'
            '<w:bottom w:type="dxa" w:w="100"/>'
            '<w:right w:type="dxa" w:w="140"/></w:tcMar></w:tcPr>')
    inner = para(r(lead, b=True, sz=22) + runs(" " + text, sz=22),
                 SP_CASE, jc="both")
    BODY.append("<w:tbl>" + TBL_PR
                + '<w:tblGrid><w:gridCol w:w="10080"/></w:tblGrid>'
                + "<w:tr><w:tc>" + tcpr + inner + "</w:tc></w:tr></w:tbl>")


def viva(n, q, a):
    BODY.append(para(r("%d.  " % n, b=True) + r(q, b=True), SP_Q,
                     ind='<w:ind w:left="360" w:hanging="360"/>'))
    BODY.append(para(r("A: ", b=True) + runs(a), SP_A,
                     ind='<w:ind w:left="360"/>', jc="both"))


def bullet(text):
    BODY.append(para(runs(text), SP_BUL, jc="both",
                     style="ListParagraph", num=1))


# ======================================================== AIM AND CO MAPPING
BODY.append(para(
    r("Aim: ", b=True)
    + r("Write an article and case study on the topics given below \u2014 "
        "(a) what a copyright is and the rights related to it; (b) the types of "
        "work protected by copyright; (c) the authorship and ownership of "
        "copyright; and (d) the duration of copyright."),
    SP_BODY, jc="both"))
BODY.append(para(r("CO Mapping: ", b=True) + r("CO3 \u00b7 BT1, BT2, BT3"),
                 '<w:spacing w:after="160" w:before="60"/>'))

# ======================================================== 1. INTRODUCTION
h1("1. Introduction: The Nature of Copyright")

body("Copyright is the right the law gives an author over the particular form in "
     "which an idea has been expressed. It is not a right over the idea, the "
     "information or the technique itself; it is a right over the arrangement of "
     "words, notes, lines, frames or instructions through which that subject "
     "matter has been made perceptible to somebody else. The Copyright Act, 1957 "
     "therefore never asks whether a work is good, useful or commercially "
     "valuable. It asks only two questions \u2014 is the expression original to "
     "this author, and has it been fixed in a form from which it can be "
     "reproduced?")

body("This makes copyright behave quite differently from a trademark or a "
     "patent. A trademark must be applied for and registered before the "
     "statutory action for infringement becomes available, and a patent does not "
     "exist at all until it has been examined and granted. Copyright exists from "
     "the instant of creation. No application, examination, deposit, fee or "
     "notice is required, and registration under Section 45 is purely voluntary "
     "\u2014 the entry in the Register of Copyrights is evidence of ownership "
     "under Section 48, not the source of it. India inherited that position from "
     "Article 5(2) of the Berne Convention, which forbids member states from "
     "making protection conditional on any formality.")

body("Copyright relates to original work of a literary, artistic, dramatic or "
     "musical character, to cinematograph films, to sound recordings and to "
     "software programs. What the author receives is not one right but a bundle "
     "of negative rights \u2014 the ability to stop others from reproducing, "
     "performing, communicating, adapting or translating the work, and to "
     "license or assign each of those abilities separately. Like every "
     "intellectual property right it is a bargain rather than a gift: in return "
     "for exclusivity the author accepts a finite term, after which the work "
     "falls irreversibly into the public domain, and accepts the substantial "
     "list of permitted uses in Section 52 which the owner cannot prevent.")

table([3000, 1000, 3540, 2540],
      ["Instrument", "Year", "What It Governs", "Position in India"],
      [["The Copyright Act", "1957",
        "Subject matter (Section 13), rights (Section 14), ownership (Section "
        "17), term (Sections 22 to 29), infringement and remedies",
        "The principal statute, amended six times"],
       ["The Copyright (Amendment) Act", "2012",
        "Performers' rights, the author's non-assignable royalty share, "
        "statutory licences, offences relating to digital rights management, "
        "and access for the disabled",
        "The most far-reaching revision to date"],
       ["The Copyright Rules", "2013",
        "Registration procedure, copyright societies, and the compulsory and "
        "statutory licensing machinery",
        "Replaced the Rules of 1958"],
       ["Berne Convention", "1886",
        "Automatic protection without formality, a minimum term of the author's "
        "life plus fifty years, and national treatment",
        "India has been a member since 1928"],
       ["Rome Convention", "1961",
        "The rights of performers, producers of phonograms and broadcasting "
        "organisations",
        "The origin of the category of related rights"],
       ["TRIPS Agreement", "1995",
        "Minimum standards of protection and enforcement binding on all members "
        "of the World Trade Organization",
        "Binding on India since 1995"],
       ["WCT and WPPT, the WIPO Internet Treaties", "1996",
        "Rights in the digital environment, technological protection measures "
        "and rights management information",
        "India acceded in 2018"],
       ["Marrakesh VIP Treaty", "2013",
        "Accessible format copies for persons with a print disability",
        "India was the first country to ratify it"]],
      "Table 1 \u2014 The Legal Framework Governing Copyright in India")

# ---------------------------------------------------------------- 1.1
h2("1.1 The Rights Conferred by Copyright")

body("Section 14 defines copyright as the exclusive right to do, or to authorise "
     "the doing of, certain acts \u2014 and it defines a different set of acts "
     "for each category of work. This is the most commonly misread provision in "
     "the Act, because there is no single uniform \u201ccopyright\u201d in India. "
     "A sound recording carries no adaptation or translation right, since the "
     "idea has no meaning for it, while a computer program carries a commercial "
     "rental right that an ordinary book does not.")

table([3080, 7000],
      ["Category of Work", "Acts Reserved Exclusively to the Owner"],
      [["Literary, dramatic or musical work, other than a computer program",
        "Reproduce the work in any material form, including electronic storage; "
        "issue copies not already in circulation; perform it in public or "
        "communicate it to the public; make a cinematograph film or sound "
        "recording of it; make any translation or adaptation; and do any of "
        "these acts in relation to a translation or adaptation"],
       ["Computer program",
        "All of the rights above, and in addition the right to sell, to give on "
        "commercial rental, or to offer for sale or rental any copy of the "
        "program, whether or not that copy has been sold before"],
       ["Artistic work",
        "Reproduce it in any material form, including the depiction in three "
        "dimensions of a two-dimensional work and the reverse; store it "
        "electronically; communicate it to the public; issue copies; include it "
        "in a film; and make any adaptation of it"],
       ["Cinematograph film",
        "Make a copy of the film, including a photograph of any image forming "
        "part of it and its electronic storage; sell or give on commercial "
        "rental any copy; and communicate the film to the public"],
       ["Sound recording",
        "Make any other sound recording embodying it, including electronic "
        "storage; sell or give on commercial rental any copy; and communicate "
        "the recording to the public"]],
      "Table 2 \u2014 Exclusive Rights Conferred by Section 14, Category by "
      "Category")

body("Alongside these economic rights, Section 57 gives the author two rights "
     "that exist independently of them and independently of who owns them. The "
     "right of paternity is the right to claim authorship of the work. The right "
     "of integrity is the right to restrain, or to claim damages for, any "
     "distortion, mutilation or modification of the work that would be "
     "prejudicial to the author's honour or reputation. These moral rights "
     "remain with the author after the copyright has been assigned in full, they "
     "cannot be signed away by an ordinary contract, and they are exercisable by "
     "the author's legal representatives after death.")

casebox("Case Study \u2014 Amar Nath Sehgal v. Union of India, Delhi High Court "
        "(2005).",
        "The plaintiff was commissioned in the late 1950s to create a bronze "
        "mural, some forty feet long, for Vigyan Bhawan in New Delhi; it became "
        "a celebrated example of modern Indian sculpture. During renovation in "
        "1979 the work was pulled down, dismembered and consigned to a "
        "government storeroom, where parts of it were damaged and lost. The "
        "Union of India argued that it owned the copyright outright, having "
        "commissioned and paid for the mural, and that an owner may deal with "
        "its own property as it pleases. The Court accepted that the economic "
        "copyright did vest in the Government but held that this was beside the "
        "point, because Section 57 protects the author's personality in the "
        "work rather than the owner's investment in it, and destruction or "
        "neglect that reduces the volume of an artist's creative corpus is "
        "itself prejudicial to honour and reputation. The Government was "
        "directed to return the remnants to the sculptor, was divested of all "
        "rights in the work, and was ordered to pay damages. The judgment is "
        "the leading Indian authority for three propositions \u2014 that moral "
        "rights survive an unconditional assignment, that they extend to acts "
        "of destruction and not merely to alteration, and that they are "
        "enforceable against the State itself.")

# ---------------------------------------------------------------- 1.2
h2("1.2 Rights Related to Copyright")

body("A related right is the category of rights granted to performers, to "
     "producers of phonograms and to broadcasters. In some countries, such as "
     "the United States of America and the United Kingdom, these rights are "
     "simply incorporated under copyright. Other countries, such as Germany and "
     "France, protect them under a separate category called neighbouring "
     "rights. The distinction exists because copyright, framed around "
     "authorship and originality, could not comfortably accommodate three "
     "classes of contributor whose economic importance is nevertheless obvious. "
     "While copyright protects the works of the authors themselves, related "
     "rights are granted to certain categories of people or businesses that "
     "play an important role in performing, communicating or disseminating "
     "works to the public \u2014 works that may or may not themselves be "
     "protected by copyright. India follows the Rome Convention model and "
     "recognises all three classes.")

table([2600, 4200, 3280],
      ["Type of Related Right", "What It Protects", "Illustration"],
      [["Rights of performers",
        "The performance of an actor, singer, musician, dancer, acrobat, "
        "juggler, conjurer, snake charmer, lecturer or any other person who "
        "makes a performance. It covers a live performance of a pre-existing "
        "artistic, dramatic or musical work, or a live recitation or reading of "
        "a pre-existing literary work. The work performed need not previously "
        "have been fixed in any medium or form, and may be in the public domain "
        "or protected by copyright; the performance may equally be an "
        "improvised one, whether original or based on a pre-existing work",
        "A stage actor's performance; a musician's rendition of a classical "
        "composition that is long out of copyright"],
       ["Rights of producers of sound recordings, or phonograms",
        "The recording itself, as a subject matter distinct from the song "
        "recorded in it, belonging to the producer who organises and finances "
        "the fixation of the sounds",
        "Compact discs; the master file of a commercially released track"],
       ["Rights of broadcasting organisations",
        "Radio and television programmes transmitted over the air and, in India "
        "as in several other countries, the transmission of works by cable. "
        "What is protected is the signal, so the broadcaster may act against "
        "unauthorised re-broadcasting or recording even where it holds no "
        "copyright in the programme content",
        "The live broadcast of a cricket match, in which no underlying work is "
        "authored at all"]],
      "Table 3 \u2014 The Three Categories of Related Rights")

body("In India these rights are conferred by Sections 37 to 38B. Section 37 "
     "gives a broadcasting organisation a broadcast reproduction right. Section "
     "38 recognises the performer's right, Section 38A confers on the performer "
     "exclusive rights over sound and visual recording, reproduction, issue of "
     "copies, communication to the public and commercial rental, and Section 38B "
     "gives the performer moral rights of identification and integrity that "
     "mirror those an author enjoys under Section 57.")

table([2200, 3940, 3940],
      ["Aspect", "Copyright", "Related or Neighbouring Rights"],
      [["Who holds the right",
        "The author \u2014 the writer, composer, artist, photographer or "
        "programmer",
        "Performers, producers of sound recordings, and broadcasting "
        "organisations"],
       ["What is protected",
        "Original expression fixed in a material form",
        "A performance, a fixation of sounds, or a broadcast signal"],
       ["Is originality required",
        "Yes \u2014 the work must originate with the author and display skill "
        "and judgment",
        "No \u2014 investment, skill and organisation are rewarded instead"],
       ["Statutory basis in India",
        "Sections 13, 14 and 57 of the Copyright Act, 1957",
        "Sections 37, 38, 38A and 38B of the same Act"],
       ["Term of protection",
        "Generally the author's lifetime and sixty years thereafter",
        "Fifty years for a performance; twenty-five years for a broadcast"],
       ["Treatment in other systems",
        "A unified copyright in the United States and the United Kingdom",
        "A separate category of neighbouring rights in France and Germany"],
       ["Governing treaty",
        "The Berne Convention, TRIPS, and the WIPO Copyright Treaty",
        "The Rome Convention, TRIPS, and the WIPO Performances and Phonograms "
        "Treaty"]],
      "Table 4 \u2014 Copyright Compared with Related Rights")

casebox("Case Study \u2014 Neha Bhasin v. Anand Raj Anand, Delhi High Court "
        "(2006).",
        "A playback singer recorded a song in a studio for a film. When the "
        "song was released she found that another singer's version had been "
        "used in some formats and that her own credit had been handled "
        "carelessly, and she asserted a performer's right. The defence was "
        "technical but serious \u2014 the Act protects a live performance, and "
        "a controlled studio recording, layered track by track with no audience "
        "present, is not live in any ordinary sense of the word. The Court "
        "rejected the argument and gave the provision the reading it still "
        "carries: every performance is live in the first instance, whether it "
        "happens before an audience or before a microphone, because it is the "
        "act of performing rather than the presence of spectators that the "
        "statute protects, and once that first rendition is recorded the "
        "performer's right attaches to the recording. The case matters because "
        "almost every commercially significant Indian performance is a studio "
        "performance; had the defence succeeded, Section 38 would have "
        "protected almost nothing.")

# ======================================================== 2. TYPES OF WORK
h1("2. Types of Work Protected by Copyright")

body("Section 13(1) confines copyright to three classes \u2014 original "
     "literary, dramatic, musical and artistic works; cinematograph films; and "
     "sound recordings. Every example one can think of, from a newspaper to a "
     "mobile application, a webcast, a product label, a training video, a "
     "database or a work of architecture, is a species of one of these. The "
     "classification is not a matter of housekeeping. It decides which set of "
     "rights under Section 14 applies, who counts as the author under Section "
     "2(d), who is the first owner under Section 17, and how long protection "
     "lasts under Sections 22 to 29.")

table([2400, 3640, 4040],
      ["Statutory Category", "Scope of the Definition",
       "Representative Examples"],
      [["Literary work \u2014 Section 2(o)",
        "Anything expressed in words, figures or symbols; the definition "
        "expressly includes computer programs, tables and compilations, "
        "including computer databases",
        "Books, magazines, newspapers, technical papers, instruction manuals, "
        "catalogues, tables and compilations of literary works, source code and "
        "object code, and some types of database"],
       ["Dramatic work \u2014 Section 2(h)",
        "Any piece for recitation, choreographic work or entertainment in dumb "
        "show, the scenic arrangement or acting form of which is fixed in "
        "writing; a cinematograph film is excluded",
        "Not only plays but also, for example, a sales training programme "
        "captured on videocassette; screenplays, scenarios and choreographic "
        "notation"],
       ["Musical work \u2014 Section 2(p)",
        "A work consisting of music, together with any graphical notation of "
        "it, but excluding the words that are sung and the action performed "
        "with the music",
        "Musical works and compositions, including compilations; the melody and "
        "harmony as distinct from the lyrics and from the recording"],
       ["Artistic work \u2014 Section 2(c)",
        "A painting, sculpture, drawing including a diagram, map, chart or "
        "plan, an engraving or a photograph, whether or not it possesses "
        "artistic quality; a work of architecture; and any other work of "
        "artistic craftsmanship",
        "Cartoons, drawings, paintings, sculptures and computer artwork; "
        "photographic works both on paper and in digital form; maps, globes, "
        "charts, diagrams, plans and technical drawings; advertisements, "
        "commercial prints and labels"],
       ["Cinematograph film \u2014 Section 2(f)",
        "Any work of visual recording, including a sound recording accompanying "
        "it, and any process analogous to cinematography including video",
        "Motion pictures, television shows, webcasts, animation, advertising "
        "films, multimedia products, and the audiovisual layer of a video game"],
       ["Sound recording \u2014 Section 2(xx)",
        "A recording of sounds from which the sounds may be produced, "
        "regardless of the medium on which the recording is made or the method "
        "by which the sounds are produced",
        "Compact discs, digital audio files, streaming masters, podcasts and "
        "phonograms"],
       ["Government work \u2014 Section 2(k)",
        "A work made or published by or under the direction or control of the "
        "Government, a legislature, or a court or tribunal in India",
        "Official reports, gazette notifications, departmental manuals, and "
        "syllabi issued by a public authority"]],
      "Table 5 \u2014 The Statutory Categories and What Falls Within Them")

h2("2.1 What Copyright Does Not Protect")

body("The boundaries of the subject matter are as important as its contents, "
     "and almost all litigation is fought on them. Copyright does not extend to "
     "ideas, themes, plots or concepts, so two writers may lawfully treat the "
     "same social problem and two programmers may lawfully solve the same "
     "problem, provided each writes their own expression of it. It does not "
     "extend to facts, news or data, because the event reported is free to all "
     "and only the reporter's particular account of it is protected. It does not "
     "extend to methods, systems or procedures, so a method of accounting or a "
     "rule of a game lies outside the Act although the manual describing it lies "
     "inside. Titles, names and short phrases are the province of trademark law "
     "rather than copyright. A compilation assembled by pure labour, with no "
     "selection or arrangement calling for judgment, is not protected merely "
     "because it was expensive to produce. And where the appearance of an "
     "article is dictated entirely by its function, design law or patent law "
     "applies instead.")

casebox("Case Study \u2014 Eastern Book Company v. D. B. Modak, Supreme Court "
        "of India (2008).",
        "The appellants published Supreme Court Cases, in which raw judgments "
        "were copy-edited, paragraphed, cross-referenced and supplied with "
        "headnotes, editorial notes and indications of concurring and "
        "dissenting opinions. The respondents reproduced the text of those "
        "judgments on CD-ROM. Because Section 52(1)(q) makes the reproduction "
        "of a judgment of a court non-infringing, the whole case turned on "
        "whether the publisher's editorial layer was itself an original "
        "literary work. The Court used the occasion to settle the Indian test "
        "of originality. It rejected the English \u201csweat of the brow\u201d "
        "approach, under which mere labour and expense suffices, and equally "
        "rejected any requirement of novelty or creative flair. What is "
        "required is a minimal degree of creativity \u2014 skill, judgment and "
        "labour of a kind that is more than trivial and more than purely "
        "mechanical. Applying that standard, the headnotes, the editorial notes "
        "and the identification of separate opinions were original and "
        "protected, while the copy-edited text of the judgments, the paragraph "
        "numbering and the typographical corrections were not. The decision is "
        "now the starting point for every Indian argument about compilations, "
        "databases and derivative works.")

casebox("Case Study \u2014 R. G. Anand v. M/s Delux Films, Supreme Court of "
        "India (1978).",
        "The appellant wrote and staged the Hindi play Hum Hindustani, which "
        "dealt with provincialism and the strain it places on a marriage. He "
        "narrated the storyline to a film producer, who later released the film "
        "New Delhi, built on the same theme. The Supreme Court held that there "
        "is no copyright in an idea, subject matter, theme, plot or historical "
        "fact, and that infringement arises only where the treatment is so "
        "close that a viewer of ordinary intelligence, seeing both works, would "
        "be left with the unmistakable impression that the later work is a copy "
        "of the earlier one. Because the film developed the shared theme "
        "through different incidents, characters and dialogue, the suit failed. "
        "The judgment explains both why two works on the same subject may "
        "lawfully coexist and why lifting a distinctive sequence of scenes, or "
        "a distinctive structure of program modules, will not be excused. The "
        "same reasoning governs software, which is protected as a literary "
        "work: the source and object code, the structure and the sequence of "
        "modules fall within copyright, while the algorithm and the functional "
        "specification do not.")

# ======================================================== 3. AUTHOR / OWNER
h1("3. Authorship and Ownership of Copyright")

body("Authorship and ownership are two different questions, and the Act answers "
     "them in two different places. Authorship is a question of fact \u2014 who "
     "actually created this expression? Section 2(d) supplies the answer for "
     "each category of work. Ownership is a question of law \u2014 in whom do "
     "the economic rights first vest? Section 17 supplies that answer, and it "
     "does not always name the author. In the ordinary case the two coincide and "
     "the author is the first owner. They come apart in a defined set of "
     "situations, every one of which operates only in the absence of any "
     "agreement to the contrary, which is to say that all of them can be "
     "reversed by a properly drafted contract.")

table([4040, 6040],
      ["Category of Work", "The Author, in Relation to That Work, Is"],
      [["Literary or dramatic work",
        "The author of the work \u2014 the person who wrote it"],
       ["Musical work",
        "The composer, that is the person who composed the music, whether or "
        "not it is recorded in any form of notation"],
       ["Artistic work other than a photograph", "The artist"],
       ["Photograph", "The person who takes the photograph"],
       ["Cinematograph film or sound recording",
        "The producer, being the person who takes the initiative and the "
        "responsibility for making the work"],
       ["Computer-generated literary, dramatic, musical or artistic work",
        "The person who causes the work to be created"]],
      "Table 6 \u2014 Who Is the \u201cAuthor\u201d under Section 2(d)")

table([4400, 4400, 1280],
      ["Situation", "The First Owner Is", "Provision"],
      [["A literary, dramatic or artistic work made by the author in the course "
        "of employment by the proprietor of a newspaper, magazine or similar "
        "periodical, under a contract of service or apprenticeship, for the "
        "purpose of publication in it",
        "In the absence of an agreement to the contrary, the proprietor of the "
        "newspaper, magazine or periodical \u2014 but only so far as "
        "publication in that periodical is concerned; the author retains the "
        "rest",
        "Section 17(a)"],
       ["A photograph taken, or a painting or portrait drawn, or an engraving or "
        "a cinematograph film made, for valuable consideration at the instance "
        "of any person",
        "In the absence of any agreement to the contrary, the person who "
        "commissioned the work and paid for it",
        "Section 17(b)"],
       ["Any other work made in the course of the author's employment under a "
        "contract of service or apprenticeship",
        "In the absence of any agreement to the contrary, the employer",
        "Section 17(c)"],
       ["An address or speech delivered in public",
        "The person who delivered the address or speech; where it is delivered "
        "on behalf of another person, that other person",
        "Section 17(cc)"],
       ["A Government work",
        "In the absence of any agreement to the contrary, the Government",
        "Section 17(d)"],
       ["A work made or first published by or under the direction or control of "
        "any public undertaking",
        "In the absence of any agreement to the contrary, the public "
        "undertaking",
        "Section 17(dd)"],
       ["A work made or first published by or under the direction of an "
        "international organisation to which Section 41 applies",
        "That international organisation",
        "Section 17(e)"],
       ["A literary, dramatic, musical or artistic work incorporated in a "
        "cinematograph film, following the amendment of 2012",
        "The author retains copyright in the underlying work; the producer owns "
        "the film but cannot take the author's royalty share for exploitation "
        "outside the cinema hall",
        "Proviso to Section 17"]],
      "Table 7 \u2014 First Ownership of Copyright under Section 17")

body("Two consequences of this scheme are worth stating expressly. First, a "
     "contract of service transfers ownership but a contract for service does "
     "not: an employee's work vests in the employer, whereas an independent "
     "consultant, freelancer or vendor keeps the copyright unless there is a "
     "written assignment to the contrary. This single distinction is the "
     "commonest source of ownership disputes in the software and design "
     "industries. Second, ownership can move but authorship cannot. A company "
     "may own every economic right in a novel, but it can never become the "
     "author, and the term of protection will still be measured from the death "
     "of the human being who wrote it.")

table([2200, 3940, 3940],
      ["Aspect", "Authorship", "Ownership"],
      [["The question it answers", "Who created the expression?",
        "In whom do the economic rights vest?"],
       ["How it is determined",
        "By Section 2(d) \u2014 a question of fact",
        "By Section 17 \u2014 a question of law, subject to contract"],
       ["Can it be transferred",
        "No \u2014 authorship is a permanent historical fact",
        "Yes \u2014 by assignment under Sections 18 and 19, or by testamentary "
        "disposition"],
       ["Rights carried",
        "The moral rights of paternity and integrity under Section 57",
        "The economic rights listed in Section 14, in whole or in part"],
       ["Relevance to the term",
        "The clock is set by the author's death, whoever happens to own the "
        "work",
        "A change of ownership neither extends, shortens nor restarts the term"],
       ["Who may sue",
        "The author, for infringement of the moral rights",
        "The owner, and an exclusive licensee, for infringement of the economic "
        "rights"]],
      "Table 8 \u2014 Authorship Distinguished from Ownership")

body("Ownership is moved either by assignment or by licence. An assignment "
     "under Sections 18 and 19 must be in writing and signed, must identify the "
     "work, the rights assigned, the territory and the duration, and must state "
     "the royalty payable; if no duration is stated it is taken to be five "
     "years, if no territory is stated it is taken to be India, and the "
     "assignment lapses if the assignee does not exercise the rights within one "
     "year. A licence under Section 30 leaves ownership where it is and merely "
     "permits a specified use. The amendment of 2012 added a protection that "
     "cannot be contracted away: the author of a literary or musical work used "
     "in a film or sound recording is entitled to an equal share of the "
     "royalties for all exploitation outside the cinema hall, and any agreement "
     "to the contrary is void.")

casebox("Case Study \u2014 Indian Performing Right Society Ltd. v. Eastern "
        "India Motion Picture Association, Supreme Court of India (1977).",
        "The society, acting for composers and lyricists, published a tariff "
        "for the public performance of film music. Film producers objected that "
        "once a song had been made for a film and paid for, no separate "
        "performing right could survive in favour of the composer. The Supreme "
        "Court held that the producer, having commissioned the composition for "
        "valuable consideration in the course of making the film, becomes the "
        "first owner of the copyright in the film and may exercise the "
        "performing right in the song as part of the film, unless there is a "
        "contract to the contrary. At the same time it confirmed that the "
        "musical work and the lyrics remain distinct works whose authors retain "
        "copyright in them outside the film. The decision is the most important "
        "Indian illustration of Section 17 in operation, and its practical "
        "consequence \u2014 that composers and lyricists earned nothing when "
        "their songs were played on radio, on television or in restaurants "
        "\u2014 is precisely what the amendment of 2012 was enacted to "
        "reverse.")

casebox("Case Study \u2014 V. T. Thomas v. Malayala Manorama, Kerala High "
        "Court (1989).",
        "The cartoonist known as Toms had created the characters Boban and "
        "Molly years before he joined the newspaper Malayala Manorama, and he "
        "continued to draw them during his employment there. After his services "
        "were terminated he resumed publishing the strip elsewhere, and the "
        "newspaper sought an injunction on the footing that it owned the "
        "characters. The Court drew the line exactly where Section 17(c) draws "
        "it. An employer's ownership extends only to works actually made in the "
        "course of the employment; it does not reach backwards to works created "
        "before the employment began, and it does not follow the author forward "
        "after the employment has ended. Because the characters had been "
        "conceived before he joined, the copyright in them remained with him "
        "throughout and he was free to continue drawing them. The case is the "
        "clearest Indian statement that employment transfers the ownership of "
        "specific works, not of an author's creative identity.")

# ======================================================== 4. DURATION
h1("4. Duration of Copyright")

body("The copyright term varies according to the nature of the work. It is "
     "sixty years from the death of the author in the case of a literary, "
     "dramatic, musical or artistic work, and sixty years after publication in "
     "the case of a photograph, a film or a sound recording. That term is ten "
     "years longer than the minimum of fifty years required by the Berne "
     "Convention. Two mechanical rules should be remembered alongside it. "
     "Sections 22 to 29 all compute the term from the beginning of the calendar "
     "year next following the relevant event, so every Indian copyright expires "
     "on a 31 December rather than on the anniversary of a death or a "
     "publication. And where a work has joint authors, the clock starts only on "
     "the death of the last of them to die.")

table([3540, 5260, 1280],
      ["Category of Work", "Term of Protection", "Provision"],
      [["Literary, dramatic, musical or artistic work published within the "
        "author's lifetime",
        "The author's lifetime and sixty years thereafter, counted from the "
        "beginning of the year following the year of death",
        "Section 22"],
       ["Work of joint authorship",
        "Sixty years from the beginning of the year following the death of the "
        "last surviving author",
        "Section 22"],
       ["Anonymous or pseudonymous work",
        "Sixty years from the beginning of the year following first "
        "publication; if the author's identity is disclosed, sixty years from "
        "the author's death instead",
        "Section 23"],
       ["Posthumous work, published after the author's death",
        "Sixty years from the beginning of the year following the year of first "
        "publication",
        "Section 24"],
       ["Photograph",
        "The author's lifetime and sixty years thereafter; the separate "
        "fifty-year rule formerly in Section 25 was omitted by the amendment of "
        "2012, so a photograph is now treated like any other artistic work",
        "Section 22"],
       ["Cinematograph film",
        "Sixty years from the beginning of the year following the year of "
        "publication",
        "Section 26"],
       ["Sound recording",
        "Sixty years from the beginning of the year following the year of "
        "publication",
        "Section 27"],
       ["Government work",
        "Sixty years from the beginning of the year following the year of first "
        "publication",
        "Section 28"],
       ["Work of a public undertaking",
        "Sixty years from the beginning of the year following the year of first "
        "publication",
        "Section 28A"],
       ["Work of an international organisation",
        "Sixty years from the beginning of the year following the year of first "
        "publication",
        "Section 29"],
       ["Broadcast reproduction right",
        "Twenty-five years from the beginning of the year following the year of "
        "the broadcast",
        "Section 37"],
       ["Performer's right",
        "Fifty years from the beginning of the year following the year of the "
        "performance",
        "Section 38"]],
      "Table 9 \u2014 Term of Copyright and Related Rights by Category")

table([2600, 3740, 3740],
      ["Jurisdiction", "Works With a Human Author",
       "Films and Sound Recordings"],
      [["India", "The author's life and sixty years thereafter",
        "Sixty years from publication"],
       ["Berne Convention minimum",
        "The author's life and fifty years thereafter",
        "Fifty years from the making or the publication of the work"],
       ["United States",
        "Life and seventy years; ninety-five years from publication for works "
        "made for hire",
        "Ninety-five years from publication"],
       ["European Union and United Kingdom", "Life and seventy years",
        "Seventy years for sound recordings; for films, seventy years from the "
        "death of the principal director and the other named authors"],
       ["Japan and Canada", "Life and seventy years",
        "Seventy years from publication"]],
      "Table 10 \u2014 The Indian Term in International Perspective")

body("When the term ends the work enters the public domain permanently and "
     "irrevocably, and anyone may then copy, perform, translate, adapt, film or "
     "sell it without permission or payment. Three qualifications matter in "
     "practice. A new edition, translation, arrangement or restoration attracts "
     "a fresh copyright, but only in the new expressive material that the editor "
     "or translator has added, and never in the underlying public domain work. A "
     "brand name or logo associated with the work may continue indefinitely as a "
     "trademark, because a trademark is renewable without limit. And the moral "
     "rights under Section 57 are, on the Indian view, exercisable by the "
     "author's representatives even in respect of works whose economic term has "
     "run out.")

casebox("Case Study \u2014 The Tagore Copyright and Visva-Bharati, 1941 to "
        "2001.",
        "Rabindranath Tagore died in August 1941, and by his bequest the "
        "copyright in his vast body of songs, poems, plays and prose was "
        "administered by Visva-Bharati, the university he had founded. Under "
        "the term then in force, the author's life and fifty years, the "
        "copyright would have expired at the end of 1991, and the university's "
        "approval for the publication, translation and musical arrangement of "
        "Rabindrasangeet would from that point have ceased to be required. In "
        "1991 Parliament extended the general term from fifty to sixty years, "
        "and because the amendment applied to subsisting copyrights the "
        "exclusivity was carried forward to 31 December 2001. On 1 January 2002 "
        "the entire corpus entered the public domain, and the effect was "
        "immediate and visible, as new editions, new translations and new "
        "recorded interpretations appeared without anybody's permission. The "
        "episode is a compact illustration of four rules at once \u2014 that "
        "the term for a literary or musical work is measured from the author's "
        "death and not from publication, that it is computed from the beginning "
        "of the following calendar year and therefore always expires on a 31 "
        "December, that a legislature may extend a term and thereby revive "
        "exclusivity in works that were about to fall free, and that expiry, "
        "once it has happened, cannot be undone.")

# ======================================================== 5. VIVA
h1("5. Viva Questions and Answers")

QA = [
    ("What is copyright, and what are the two conditions a work must satisfy?",
     "Copyright is the exclusive right an author has over the particular form in "
     "which an idea has been expressed, in relation to original literary, "
     "dramatic, musical and artistic works, cinematograph films, sound "
     "recordings and software. The work must be original to the author, and it "
     "must be fixed in some form from which it can be reproduced. Its quality, "
     "usefulness and commercial value are all irrelevant."),
    ("Why does copyright need no registration when a trademark and a patent "
     "benefit from one?",
     "Because copyright protects expression, which is self-evident from the work "
     "itself, whereas a patent protects a technical monopoly that must be "
     "examined before it can be justified and a trademark must be on the "
     "register before the statutory infringement action is available. Article "
     "5(2) of the Berne Convention forbids member states from making copyright "
     "depend on any formality, so registration in India is voluntary and, under "
     "Section 48, only evidentiary."),
    ("What is a related right, and how does it differ from copyright?",
     "A related or neighbouring right is granted to performers, to producers of "
     "phonograms and to broadcasters. It requires no originality and rewards "
     "performance, fixation or dissemination rather than authorship. Copyright, "
     "by contrast, belongs to the author of an original work and is conditional "
     "on originality. In the United States and the United Kingdom related rights "
     "are absorbed into copyright; in Germany and France they form a separate "
     "category."),
    ("Does a performer have rights in a performance of a public domain work?",
     "Yes. The performer's right under Section 38 attaches to the performance "
     "itself. The underlying work need not be original, need not previously have "
     "been fixed in any medium, and may be in the public domain or improvised on "
     "the spot."),
    ("Name the categories of work protected by copyright in India.",
     "Original literary works, which include computer programs, tables and "
     "compilations; dramatic works; musical works; artistic works, which include "
     "paintings, drawings, maps, charts, plans, photographs and works of "
     "architecture; cinematograph films, which include television programmes and "
     "webcasts; and sound recordings. Government works form a distinct category "
     "for the purposes of ownership and term."),
    ("Distinguish authorship from ownership, with an example.",
     "Authorship is a fact fixed by Section 2(d); ownership is a legal "
     "allocation made by Section 17. A staff journalist is the author of the "
     "article she writes, but the proprietor of the newspaper is the first owner "
     "so far as publication in that newspaper is concerned. She remains the "
     "author permanently, retains her moral rights, and the term of protection "
     "is still measured from her death."),
    ("Who owns a wedding photograph, and who owns a photograph taken by a "
     "salaried photographer?",
     "A wedding photograph is commissioned for valuable consideration, so under "
     "Section 17(b) the client who commissioned it is the first owner, although "
     "the photographer remains the author. A photograph taken by a salaried "
     "photographer in the course of employment vests in the employer under "
     "Section 17(c). Both rules yield to an agreement to the contrary."),
    ("How exactly is the sixty-year term calculated?",
     "From the beginning of the calendar year next following the year of the "
     "relevant event \u2014 the author's death for literary, dramatic, musical "
     "and artistic works, and first publication for films, sound recordings, "
     "anonymous works, Government works and works of public undertakings. Every "
     "Indian copyright therefore expires on a 31 December, and for joint authors "
     "the clock starts on the death of the last survivor."),
    ("Has the term for photographs changed?",
     "Yes. Section 25 formerly gave photographs a flat fifty years from "
     "publication. The amendment of 2012 omitted that section, so a photograph "
     "is now treated like any other artistic work and enjoys the author's "
     "lifetime and sixty years thereafter."),
    ("What are moral rights, and can they be assigned away?",
     "Section 57 gives the author the right of paternity, to claim authorship, "
     "and the right of integrity, to restrain distortion, mutilation or "
     "modification prejudicial to honour or reputation. They exist independently "
     "of the economic rights, survive an unconditional assignment, and are "
     "exercisable by the author's legal representatives. Amar Nath Sehgal v. "
     "Union of India applied them even against the destruction of the work by "
     "its owner."),
]
for n, (q, a) in enumerate(QA, start=1):
    viva(n, "Q: " + q, a)

# ======================================================== 6. OUTCOMES
h1("6. Learning Outcomes")

for b in [
    "Defined copyright as a right over original expression rather than over "
    "ideas, explained why it arises automatically on creation and needs no "
    "registration, and placed it within the wider framework of intellectual "
    "property rights and of India's Berne, Rome, TRIPS, WCT, WPPT and Marrakesh "
    "obligations.",
    "Explained the rights related to copyright \u2014 those of performers, of "
    "producers of sound recordings and of broadcasting organisations \u2014 and "
    "why they are absorbed into copyright in the United States and the United "
    "Kingdom but treated as separate neighbouring rights in Germany and France.",
    "Identified and classified the works protected under copyright law, from "
    "literary, dramatic, musical and artistic works to cinematograph films, "
    "sound recordings, software, databases, maps, technical drawings, labels and "
    "multimedia products, and marked the boundary against ideas, facts, methods "
    "and titles.",
    "Differentiated authorship under Section 2(d) from first ownership under "
    "Section 17, worked through the employment, commissioning, speech, "
    "Government and public undertaking situations, and explained why ownership "
    "is transferable while authorship is not.",
    "Interpreted the duration and applicability of copyright protection under "
    "Sections 22 to 29, including the calendar-year computation rule, the "
    "position of joint, anonymous and posthumous works, the revised treatment of "
    "photographs, and the shorter terms attaching to performances and "
    "broadcasts.",
    "Applied copyright concepts through case-based analysis, using Amar Nath "
    "Sehgal, Neha Bhasin, Eastern Book Company v. Modak, R. G. Anand v. Delux "
    "Films, IPRS v. EIMPA, V. T. Thomas and the Tagore public domain episode to "
    "see how the statutory language behaves under litigation.",
    "Developed an appreciation of the ethical use of intellectual property, "
    "including the fair dealing exceptions in Section 52, the author's "
    "non-assignable royalty share introduced in 2012, and the consequences of "
    "a work passing into the public domain.",
]:
    bullet(b)

# ======================================================== ASSEMBLE
orig = zipfile.ZipFile(SRC)
doc = orig.read("word/document.xml").decode("utf-8")

body_start = doc.index("<w:body>") + len("<w:body>")
aim_idx = doc.index('<w:t xml:space="preserve">Aim: </w:t>')
aim_p = doc.rindex("<w:p>", 0, aim_idx)
preamble = doc[body_start:aim_p]          # title + details table + spacer
assert "Experiment: 1.3" in preamble
preamble = preamble.replace("Experiment: 1.3", "Experiment: 1.4")

sect = doc.index("<w:sectPr>")
tail = doc[sect:]

new_doc = doc[:body_start] + preamble + "".join(BODY) + tail

rels = orig.read("word/_rels/document.xml.rels").decode("utf-8")
rels = re.sub(r'<Relationship Id="%s".*?/>' % DROP_REL_ID, "", rels)
assert DROP_REL_ID not in rels

with zipfile.ZipFile(OUT, "w", zipfile.ZIP_DEFLATED) as out:
    for item in orig.infolist():
        if item.filename == DROP_MEDIA:
            continue
        if item.filename == "word/document.xml":
            out.writestr(item, new_doc.encode("utf-8"))
        elif item.filename == "word/_rels/document.xml.rels":
            out.writestr(item, rels.encode("utf-8"))
        else:
            out.writestr(item, orig.read(item.filename))

print("wrote", OUT)
print("blocks:", len(BODY))

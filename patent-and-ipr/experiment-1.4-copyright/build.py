#!/usr/bin/env python3
"""Experiment 1.4 - Copyright, Related Rights, Authorship, Ownership and Term."""

import os
import sys

from pdfgen import (Doc, M, ML, MR, CONTENT_W, BODY_TOP, PAGE_W, SERIF, SANS,
                    BLACK, GREY)
import layout as L

STUDENT = "Mohammad Saood"
UID = "26MAI10040"

d = Doc("Name: %s" % STUDENT, "UID: %s" % UID, L.header)

# ------------------------------------------------------------------ title block
c = d.canvas
c.ctext(ML + CONTENT_W / 2.0, 100.0, "Experiment: 1.4", "Times-Bold", 14.0)

COL2 = ML + 280.0
rows = [
    ("Student Name: %s" % STUDENT, "UID: %s" % UID),
    ("Branch Name: M.E. (CSE) (AIML)", "Section/Group:  B"),
    (None, "Date of Performance:"),          # semester drawn specially
    ("Subject: Patent and IPR", "Subject Code: 26CSP \u2013 626"),
]
yy = 118.0
for left, right in rows:
    if left is None:
        c.text(ML, yy, "Semester: 1", "Times-Bold", 11.0)
        c.text(ML + M.width("Semester: 1", "Times-Bold", 11.0), yy - 4.0, "st",
               "Times-Bold", 7.5)
    else:
        c.text(ML, yy, left, "Times-Bold", 11.0)
    c.text(COL2, yy, right, "Times-Bold", 11.0)
    yy += 17.5

d.y = 182.0

d.para(
    "**Aim:** Write an article and case study on the topics given below \u2014 what a "
    "copyright is and the rights related to it; the types of work protected by "
    "copyright; the authorship and ownership of copyright; and the duration of "
    "copyright protection.",
    space_after=4.0)

# ============================================================== 1. Introduction
d.heading("1. Introduction: What a Copyright Actually Is", space_before=8.0)

d.para(
    "Copyright is the right that the law gives an author over the particular form in "
    "which an idea has been expressed. It is not a right over the idea, the "
    "information, the technique or the subject matter; it is a right over the "
    "arrangement of words, notes, lines, shapes, frames or instructions through which "
    "that subject matter has been made perceptible to someone else. The Copyright Act, "
    "1957 therefore does not ask whether a work is good, useful, novel or "
    "commercially valuable. It asks only two questions: is the expression original to "
    "this author, and has it been fixed in a form from which it can be reproduced?")

d.para(
    "This makes copyright behave very differently from a patent. A patent must be "
    "applied for, examined for novelty and inventive step, and granted before it "
    "exists. Copyright exists from the instant of creation. No application, "
    "examination, deposit, fee or notice is required, and registration under Section 45 "
    "is purely voluntary \u2014 the entry in the Register of Copyrights is evidence of "
    "ownership under Section 48, not the source of it. India inherited this position "
    "from Article 5(2) of the Berne Convention, which forbids member states from making "
    "protection conditional on any formality.")

d.para(
    "What the author receives is not a single right but a bundle of negative rights: "
    "the ability to stop other people from reproducing, performing, communicating, "
    "adapting or translating the work, and to license or assign each of those "
    "abilities separately. Around that core the law has built two further layers. "
    "Moral rights protect the author's personal connection with the work even after the "
    "commercial rights have been sold. Related rights \u2014 called neighbouring rights "
    "in Germany and France, and simply absorbed into copyright in the United States and "
    "the United Kingdom \u2014 protect those who perform, record and broadcast works "
    "rather than those who author them.")

d.para(
    "Like every intellectual property right, copyright is a bargain and not a gift. In "
    "return for exclusivity the author accepts a finite term after which the work falls "
    "irreversibly into the public domain, and accepts a substantial list of permitted "
    "uses under Section 52 \u2014 private study, research, criticism, review, reporting, "
    "judicial proceedings, classroom teaching and conversion into accessible formats for "
    "persons with disabilities \u2014 which the owner cannot prevent.")

d.table(
    "Table 1 \u2014 The Legal Framework Governing Copyright in India",
    ["Instrument", "Year", "What It Governs", "Position in India"],
    [
        ["The Copyright Act", "1957",
         "Subject matter (S. 13), rights (S. 14), ownership (S. 17), term (S. 22-29), "
         "infringement and remedies",
         "The principal statute; amended six times"],
        ["The Copyright (Amendment) Act", "2012",
         "Performers' rights, authors' non-assignable royalty share, statutory "
         "licences, DRM offences, disability access",
         "The most far-reaching revision to date"],
        ["The Copyright Rules", "2013",
         "Registration procedure, copyright societies, statutory and compulsory "
         "licensing machinery",
         "Replaced the Rules of 1958"],
        ["Berne Convention", "1886",
         "Automatic protection without formality; minimum term of life plus 50 years; "
         "national treatment",
         "India a member since 1928"],
        ["Universal Copyright Convention", "1952",
         "Alternative multilateral regime built around the \u00a9 notice",
         "India a member since 1957"],
        ["Rome Convention", "1961",
         "Rights of performers, producers of phonograms and broadcasting organisations",
         "The origin of related rights"],
        ["TRIPS Agreement", "1995",
         "Minimum standards and enforcement obligations for all WTO members",
         "Binding on India since 1995"],
        ["WCT and WPPT (WIPO Internet Treaties)", "1996",
         "Rights in the digital environment, technological protection measures, rights "
         "management information",
         "India acceded in 2018"],
        ["Marrakesh VIP Treaty", "2013",
         "Accessible format copies for persons with print disabilities",
         "India was the first country to ratify"],
    ],
    [1.35, 0.42, 2.5, 1.6])

# ========================================================= 2. The bundle of rights
d.heading("2. The Rights Conferred by Copyright and the Rights Related to It")

d.para(
    "The expression \u201ccopyright and related rights\u201d covers two different "
    "populations of right holders. Copyright protects the people who author works \u2014 "
    "the novelist, the playwright, the composer, the painter, the photographer, the "
    "programmer. Related rights protect the people and businesses who do not author "
    "anything but who perform, fix, disseminate or communicate those works to the "
    "public, and who invest heavily in doing so. The performer of a folk song in the "
    "public domain authors nothing, yet the law protects the performance; the "
    "broadcaster of a live cricket match authors nothing, yet the law protects the "
    "signal.")

d.figure(L.FIG1_H, L.fig1,
         "Figure 1 \u2014 The three layers of protection built on a single work.")

d.heading("2.1 Economic Rights under Section 14", size=11.5, space_before=4.0,
          space_after=6.0)

d.para(
    "Section 14 defines copyright as the exclusive right to do, or authorise the doing "
    "of, certain acts \u2014 and it defines a different set of acts for each category of "
    "work. This is the single most commonly misread provision in the Act: there is no "
    "general, uniform \u201ccopyright\u201d in India. A sound recording, for example, "
    "carries no adaptation or translation right, because the concept has no meaning for "
    "it, while a computer programme carries a commercial rental right that an ordinary "
    "book does not.")

d.table(
    "Table 2 \u2014 Exclusive Rights Conferred by Section 14, Category by Category",
    ["Category of Work", "Acts Reserved Exclusively to the Owner"],
    [
        ["Literary, dramatic or musical work (other than a computer programme)",
         "Reproduce in any material form, including electronic storage; issue copies "
         "not already in circulation; perform or communicate to the public; make a "
         "cinematograph film or sound recording of it; make any translation; make any "
         "adaptation; and do any of these acts in relation to a translation or "
         "adaptation"],
        ["Computer programme",
         "All of the rights above, plus the right to sell, give on commercial rental "
         "or offer for sale or rental any copy of the programme, regardless of whether "
         "that copy has been sold before"],
        ["Artistic work",
         "Reproduce in any material form, including depiction in three dimensions of a "
         "two-dimensional work and vice versa; store electronically; communicate to the "
         "public; issue copies; include in a film; and make any adaptation"],
        ["Cinematograph film",
         "Make a copy of the film, including a photograph of any image forming part of "
         "it and electronic storage; sell or give on commercial rental any copy; and "
         "communicate the film to the public"],
        ["Sound recording",
         "Make any other sound recording embodying it, including electronic storage; "
         "sell or give on commercial rental any copy; and communicate the recording to "
         "the public"],
    ],
    [1.15, 3.0])

d.heading("2.2 Moral Rights under Section 57", size=11.5, space_before=4.0,
          space_after=6.0)

d.para(
    "Section 57 gives the author two rights that exist independently of the economic "
    "rights and independently of who owns them. The right of paternity is the right to "
    "claim authorship of the work. The right of integrity is the right to restrain or "
    "claim damages for any distortion, mutilation, modification or other act in "
    "relation to the work that would be prejudicial to the author's honour or "
    "reputation. These rights remain with the author after the copyright has been "
    "assigned in full, they cannot be waived by an ordinary contract, and they are "
    "exercisable by the author's legal representatives after death.")

d.casebox(
    "**Case Study \u2014 Amar Nath Sehgal v. Union of India, Delhi High Court (2005).** "
    "The plaintiff was commissioned in the late 1950s to create a bronze mural for "
    "Vigyan Bhawan in New Delhi. The work, some forty feet long, was a celebrated "
    "example of modern Indian sculpture. During renovation in 1979 it was pulled down, "
    "dismembered and consigned to a government storeroom, where parts of it were "
    "damaged and lost. The Union of India argued that it owned the copyright outright, "
    "having commissioned and paid for the mural, and that an owner may deal with its "
    "own property as it pleases. The Court accepted that the economic copyright vested "
    "in the Government but held that this was beside the point. Section 57 protects the "
    "author's personality in the work, not the owner's investment in it, and destruction "
    "or neglect that reduces the volume of an artist's creative corpus is itself "
    "prejudicial to honour and reputation. The Government was directed to return the "
    "remnants of the mural to the sculptor, was divested of all rights in it, and was "
    "ordered to pay damages. The judgment is the leading Indian authority for three "
    "propositions: moral rights survive an unconditional assignment, they extend to acts "
    "of destruction and not merely to alteration, and they are enforceable against the "
    "State.")

d.heading("2.3 Related or Neighbouring Rights", size=11.5, space_before=4.0,
          space_after=6.0)

d.para(
    "Related rights were created because copyright, framed around authorship and "
    "originality, could not accommodate three classes of contributor whose economic "
    "importance is nevertheless obvious. India follows the Rome Convention model and "
    "recognises all three:")

d.bullets([
    "**Rights of performers.** A performer includes an actor, singer, musician, dancer, "
    "acrobat, juggler, conjurer, snake charmer, lecturer or any other person who makes "
    "a performance. The right attaches to a live performance \u2014 a rendition of a "
    "pre-existing dramatic or musical work, a recitation or reading of a literary work, "
    "or a wholly improvised piece. The underlying work need not be original, need not "
    "be previously fixed in any medium, and may perfectly well be in the public domain. "
    "Section 38A confers exclusive rights over sound and visual recording, "
    "reproduction, issue of copies, communication to the public and commercial rental; "
    "Section 38B gives the performer moral rights of identification and integrity.",
    "**Rights of producers of sound recordings, or phonograms.** The producer who "
    "organises and finances the fixation of sounds \u2014 historically on a compact "
    "disc, today on a server \u2014 owns the recording as a distinct subject matter, "
    "separate from the song recorded in it.",
    "**Rights of broadcasting organisations.** Section 37 confers a broadcast "
    "reproduction right over radio and television programmes transmitted over the air, "
    "and, in India as in many countries, over transmissions carried by cable. It "
    "protects the signal itself, so a broadcaster can act against unauthorised "
    "re-broadcasting or recording even where it holds no copyright in the programme "
    "content.",
])

d.table(
    "Table 3 \u2014 Copyright Compared with Related (Neighbouring) Rights",
    ["Aspect", "Copyright", "Related / Neighbouring Rights"],
    [
        ["Who holds the right",
         "The author \u2014 writer, composer, artist, photographer, programmer",
         "Performers, producers of sound recordings, broadcasting organisations"],
        ["What is protected",
         "Original expression fixed in a material form",
         "A performance, a fixation of sounds, or a broadcast signal"],
        ["Originality required",
         "Yes \u2014 the work must originate with the author and show skill and judgment",
         "No \u2014 investment, skill and organisation are protected instead"],
        ["Statutory basis in India",
         "Sections 13, 14 and 57 of the Copyright Act, 1957",
         "Sections 37, 38, 38A and 38B of the same Act"],
        ["Term",
         "Generally the author's lifetime plus 60 years",
         "50 years for a performance; 25 years for a broadcast"],
        ["Treatment in other systems",
         "A unified copyright in the United States and the United Kingdom",
         "A separate category of droits voisins in France and Germany"],
        ["Governing treaty",
         "Berne Convention, TRIPS, WIPO Copyright Treaty",
         "Rome Convention, TRIPS, WIPO Performances and Phonograms Treaty"],
    ],
    [0.95, 2.0, 2.0])

d.figure(L.FIG2_H, L.fig2,
         "Figure 2 \u2014 Five different rights attaching simultaneously to one film song.")

d.casebox(
    "**Case Study \u2014 Neha Bhasin v. Anand Raj Anand, Delhi High Court (2006).** "
    "A playback singer recorded a song in a studio for a film. When the song was "
    "released she found that another singer's version had been used in some formats and "
    "that her own credit had been handled carelessly, and she asserted a performer's "
    "right. The defence was technical but serious: Section 2(q) protects a "
    "\u201clive performance\u201d, and a controlled studio recording, layered track by "
    "track with no audience present, is not live in any ordinary sense. The Court "
    "rejected the argument and gave the provision the reading it still carries \u2014 "
    "every performance is live in the first instance, whether it happens before an "
    "audience or before a microphone, because it is the act of performing rather than "
    "the presence of spectators that the statute protects. Once that first rendition is "
    "recorded, the performer's right attaches to the recording. The case matters because "
    "almost all commercially significant Indian performances are studio performances; "
    "had the defence succeeded, Section 38 would have protected almost nothing.")

# ================================================ 3. Types of work protected
d.heading("3. The Types of Work Protected by Copyright")

d.para(
    "Section 13(1) confines copyright to three classes: original literary, dramatic, "
    "musical and artistic works; cinematograph films; and sound recordings. Every "
    "example one can think of \u2014 a newspaper, a mobile application, a webcast, a "
    "product label, a training video, a database, a piece of architecture \u2014 is a "
    "species of one of these. The classification is not cosmetic. It decides which set "
    "of rights under Section 14 applies, who counts as the author under Section 2(d), "
    "who is the first owner under Section 17, and how long protection lasts under "
    "Sections 22 to 29.")

d.table(
    "Table 4 \u2014 The Statutory Categories and What Falls Within Them",
    ["Statutory Category", "Scope of the Definition",
     "Representative Examples"],
    [
        ["Literary work \u2014 S. 2(o)",
         "Anything expressed in words, figures or symbols; expressly includes computer "
         "programmes, tables and compilations, including computer databases",
         "Books, magazines, newspapers, technical papers, instruction manuals, "
         "catalogues, tables, compilations, source code and object code, some databases"],
        ["Dramatic work \u2014 S. 2(h)",
         "Any piece for recitation, choreographic work or entertainment in dumb show, "
         "the scenic arrangement or acting form of which is fixed in writing; excludes "
         "a cinematograph film",
         "Stage plays, screenplays and scenarios, choreographic notation, and a sales "
         "training programme captured on videocassette"],
        ["Musical work \u2014 S. 2(p)",
         "A work consisting of music, together with any graphical notation of it, but "
         "excluding the words sung and the action performed with the music",
         "Compositions and compilations of compositions; the melody and harmony as "
         "distinct from the lyrics and from the recording"],
        ["Artistic work \u2014 S. 2(c)",
         "A painting, sculpture, drawing (including a diagram, map, chart or plan), "
         "engraving or photograph, whether or not it possesses artistic quality; a work "
         "of architecture; any other work of artistic craftsmanship",
         "Cartoons, drawings, paintings, sculptures, computer artwork, photographs on "
         "paper and in digital form, maps, globes, charts, diagrams, plans and technical "
         "drawings, advertisements, commercial prints and labels, logos"],
        ["Cinematograph film \u2014 S. 2(f)",
         "Any work of visual recording, including a sound recording accompanying it, "
         "and any process analogous to cinematography including video",
         "Motion pictures, television programmes, webcasts, animation, advertising "
         "films, multimedia products and the audiovisual layer of video games"],
        ["Sound recording \u2014 S. 2(xx)",
         "A recording of sounds from which the sounds may be produced, regardless of the "
         "medium or the method used",
         "Compact discs, digital audio files, streaming masters, podcasts, phonograms"],
        ["Government work \u2014 S. 2(k)",
         "A work made or published by or under the direction or control of the "
         "Government, a legislature, or a court or tribunal in India",
         "Official reports, gazette notifications, departmental manuals, syllabi and "
         "curricula issued by a public authority"],
    ],
    [1.0, 2.1, 2.2])

d.figure(L.FIG3_H, L.fig3,
         "Figure 3 \u2014 Primary works, entrepreneurial works, and the matter that "
         "falls outside copyright altogether.")

d.heading("3.1 What Copyright Does Not Protect", size=11.5, space_before=4.0,
          space_after=6.0)

d.para(
    "The boundaries of the subject matter are as important as its contents, and almost "
    "all litigation is fought on them:")

d.bullets([
    "**Ideas, themes, plots and concepts.** Two writers may lawfully treat the same "
    "social problem, and two programmers may lawfully solve the same problem, provided "
    "each writes their own expression of it.",
    "**Facts, news and data.** The event reported is free to all; only the reporter's "
    "particular account of it is protected.",
    "**Methods, systems and procedures.** A method of accounting, a rule of a game or a "
    "manufacturing process is outside copyright, although the manual describing it is "
    "inside.",
    "**Titles, names and short phrases.** These are the province of trade mark law; a "
    "film title as such carries no copyright.",
    "**Unoriginal compilations.** A directory assembled by pure labour, with no "
    "selection or arrangement calling for judgment, is not protected merely because it "
    "was expensive to compile.",
    "**Functional shape and purely mechanical form.** Where appearance is dictated "
    "entirely by function, design law or patent law applies instead.",
])

d.casebox(
    "**Case Study \u2014 Eastern Book Company v. D. B. Modak, Supreme Court of India "
    "(2008).** The appellants published Supreme Court Cases, in which raw judgments were "
    "copy-edited, paragraphed, cross-referenced and supplied with headnotes, editorial "
    "notes and indications of concurring and dissenting opinions. The respondents "
    "reproduced the text of the judgments from those volumes on CD-ROM. Section 52(1)(q) "
    "makes the reproduction of a judgment of a court non-infringing, so the whole case "
    "turned on whether the publisher's editorial layer was itself an original literary "
    "work. The Court used the occasion to settle the Indian test of originality. It "
    "rejected the English \u201csweat of the brow\u201d approach, under which mere labour "
    "and expense suffices, and equally rejected any requirement of novelty or creative "
    "flair. What is required is a minimal degree of creativity \u2014 skill, judgment "
    "and some labour of a kind that is more than trivial and more than purely "
    "mechanical. Applying that standard, the headnotes, editorial notes and the "
    "identification of separate opinions were held to be original and protected, while "
    "the copy-edited text of the judgments, paragraph numbering and typographical "
    "corrections were not. Eastern Book Company is now the starting point for every "
    "Indian argument about compilations, databases and derivative works.")

d.casebox(
    "**Case Study \u2014 R. G. Anand v. M/s Delux Films, Supreme Court of India "
    "(1978).** The appellant wrote and staged the Hindi play Hum Hindustani, which dealt "
    "with provincialism and the strain it places on a marriage. He narrated the story to "
    "a producer, who later released the film New Delhi, built on the same theme. The "
    "Supreme Court held that there is no copyright in an idea, subject matter, theme, "
    "plot or historical fact, and that infringement arises only where the treatment is "
    "so close that a viewer of ordinary intelligence, seeing both works, would be left "
    "with the unmistakable impression that the later is a copy of the earlier. Because "
    "the film developed the shared theme through different incidents, characters and "
    "dialogue, the suit failed. The decision explains both why two works on the same "
    "subject may coexist and why lifting a distinctive sequence of scenes, or a "
    "distinctive structure of program modules, will not be excused.")

d.para(
    "The same reasoning governs software. A computer programme is protected as a "
    "literary work, so its source and object code, its structure, its sequence of "
    "modules and its screen displays are within copyright, while the algorithm, the "
    "functional specification and the ideas it implements are not. In Microsoft "
    "Corporation v. Yogesh Papat (2005) the Delhi High Court applied this framework to "
    "an assembler who loaded unlicensed copies of the plaintiff's software onto machines "
    "he sold, and awarded substantial damages calculated on estimated lost licence "
    "revenue \u2014 the first Indian judgment to treat software piracy as a quantifiable "
    "commercial loss rather than a purely technical breach.")

# ============================================== 4. Authorship and ownership
d.heading("4. Authorship and Ownership of Copyright")

d.para(
    "Authorship and ownership are two different questions and the Act answers them in "
    "two different places. Authorship is a question of fact: who actually created this "
    "expression? Section 2(d) supplies the answer for each category of work. Ownership "
    "is a question of law: in whom do the economic rights first vest? Section 17 "
    "supplies that answer, and it does not always name the author. In the ordinary case "
    "the two coincide, and the author is the first owner. They come apart in a defined "
    "set of situations, every one of which operates only \u201cin the absence of any "
    "agreement to the contrary\u201d \u2014 which is to say that all of them can be "
    "reversed by a properly drafted contract.")

d.table(
    "Table 5 \u2014 Who Is the \u201cAuthor\u201d under Section 2(d)",
    ["Category of Work", "The Author Is"],
    [
        ["Literary or dramatic work", "The author of the work \u2014 the person who wrote it"],
        ["Musical work", "The composer, that is the person who composed the music, "
                         "whether or not it is recorded in notation"],
        ["Artistic work other than a photograph", "The artist"],
        ["Photograph", "The person taking the photograph"],
        ["Cinematograph film", "The producer, being the person who takes the initiative "
                               "and responsibility for making the work"],
        ["Sound recording", "The producer of the recording"],
        ["Computer-generated literary, dramatic, musical or artistic work",
         "The person who causes the work to be created"],
    ],
    [1.25, 2.6])

d.table(
    "Table 6 \u2014 First Ownership of Copyright under Section 17",
    ["Situation", "First Owner", "Provision"],
    [
        ["A literary, dramatic or artistic work made by the author in the course of "
         "employment by the proprietor of a newspaper, magazine or similar periodical, "
         "under a contract of service or apprenticeship, for the purpose of publication "
         "in it",
         "The proprietor of the newspaper, magazine or periodical \u2014 but only so far "
         "as publication in that periodical is concerned; the author retains the rest",
         "S. 17(a)"],
        ["A photograph taken, or a painting or portrait drawn, or an engraving or a "
         "cinematograph film made, for valuable consideration at the instance of any "
         "person",
         "The person who commissioned the work and paid for it",
         "S. 17(b)"],
        ["Any other work made in the course of the author's employment under a contract "
         "of service or apprenticeship",
         "The employer",
         "S. 17(c)"],
        ["An address or speech delivered in public",
         "The person who delivered it; where it is delivered on behalf of another "
         "person, that other person",
         "S. 17(cc)"],
        ["A Government work",
         "The Government",
         "S. 17(d)"],
        ["A work made or first published by or under the direction or control of a "
         "public undertaking",
         "The public undertaking",
         "S. 17(dd)"],
        ["A work made or first published by or under the direction of an international "
         "organisation to which Section 41 applies",
         "That international organisation",
         "S. 17(e)"],
        ["A literary, dramatic, musical or artistic work incorporated in a "
         "cinematograph film (after the 2012 amendment)",
         "The author retains copyright in the underlying work; the producer owns the "
         "film, and cannot take the author's royalty share for uses outside the cinema "
         "hall",
         "Proviso to S. 17"],
    ],
    [2.35, 2.2, 0.62])

d.para(
    "Two consequences of this scheme are worth stating expressly. First, a contract of "
    "service transfers ownership but a contract for service does not: an employee's work "
    "vests in the employer, whereas an independent consultant, freelancer or vendor "
    "keeps the copyright unless a written assignment says otherwise. This is the single "
    "most frequent source of ownership disputes in the software and design industries. "
    "Second, ownership can move but authorship cannot. A company may own every economic "
    "right in a novel, but it can never become the author, and the term of protection "
    "will still be measured from the death of the human being who wrote it.")

d.table(
    "Table 7 \u2014 Authorship Distinguished from Ownership",
    ["Aspect", "Authorship", "Ownership"],
    [
        ["Question answered", "Who created the expression?",
         "In whom do the economic rights vest?"],
        ["Determined by", "Section 2(d) \u2014 a question of fact",
         "Section 17 \u2014 a question of law, subject to contract"],
        ["Can it be transferred",
         "No \u2014 authorship is a permanent historical fact",
         "Yes \u2014 by assignment under S. 18 and 19, or by testamentary disposition"],
        ["Rights carried",
         "Moral rights of paternity and integrity under S. 57",
         "The economic rights listed in S. 14, in whole or in part"],
        ["Relevance to term",
         "The clock is set by the author's death, whoever owns the work",
         "Ownership changes do not extend, shorten or restart the term"],
        ["Who may sue",
         "The author, for infringement of moral rights",
         "The owner and an exclusive licensee, for infringement of economic rights"],
    ],
    [0.9, 1.9, 2.15])

d.para(
    "Ownership is moved either by assignment or by licence. An assignment under Sections "
    "18 and 19 must be in writing and signed, must identify the work, the rights "
    "assigned, the territory and the duration, and must state the royalty payable; if no "
    "duration is stated it is taken to be five years, and if no territory is stated it "
    "is taken to be India. An assignment lapses if the assignee does not exercise the "
    "rights within one year. A licence under Section 30 leaves ownership where it is and "
    "merely permits specified use. The 2012 amendment added a protection that cannot be "
    "contracted away: an author of a literary or musical work used in a film or sound "
    "recording is entitled to an equal share of royalties for all exploitation outside "
    "the cinema hall, and any agreement to the contrary is void.")

d.casebox(
    "**Case Study \u2014 Indian Performing Right Society Ltd. v. Eastern India Motion "
    "Picture Association, Supreme Court of India (1977).** The society, acting for "
    "composers and lyricists, published a tariff for the public performance of film "
    "music. Film producers objected that once a song had been made for a film and paid "
    "for, no separate performing right could survive in favour of the composer. The "
    "Supreme Court held that the producer, having commissioned the composition for "
    "valuable consideration in the course of making the film, becomes the first owner of "
    "the copyright in the film and may exercise the performing right in the song as part "
    "of the film \u2014 unless there is a contract to the contrary. At the same time it "
    "confirmed that the musical work and the lyrics remain distinct works whose authors "
    "retain copyright in them outside the film. The decision is the most important "
    "Indian illustration of Section 17 in operation, and its practical consequence "
    "\u2014 that composers and lyricists earned nothing when their songs were played on "
    "radio, television or in restaurants \u2014 is precisely what the 2012 amendment "
    "was enacted to reverse.")

d.casebox(
    "**Case Study \u2014 V. T. Thomas v. Malayala Manorama, Kerala High Court (1989).** "
    "The cartoonist known as Toms had created the characters Boban and Molly years "
    "before he joined the newspaper Malayala Manorama, and he continued to draw them "
    "during his employment there. After his services were terminated he resumed "
    "publishing the strip elsewhere, and the newspaper sought an injunction on the "
    "footing that it owned the characters. The Court drew the line exactly where Section "
    "17(c) draws it. An employer's ownership extends only to works actually made in the "
    "course of employment; it does not reach backwards to works created before the "
    "employment began, and it does not follow the author forward after the employment "
    "ends. The characters had been conceived before he joined, so the copyright in them "
    "remained with him throughout, and he was free to continue drawing them. The case is "
    "the clearest Indian statement that employment transfers ownership of specific "
    "works, not of an author's creative identity.")

# ================================================== 5. Duration of copyright
d.heading("5. The Duration of Copyright")

d.para(
    "Copyright is deliberately finite. The Indian term is sixty years, which is ten "
    "years more than the minimum of fifty required by the Berne Convention, and the "
    "point from which those sixty years run depends on the category of the work. For "
    "works with a human author it runs from the author's death; for works whose "
    "authorship is corporate, anonymous or entrepreneurial it runs from publication. Two "
    "mechanical rules should be remembered. Sections 22 to 29 all compute the term from "
    "the beginning of the calendar year next following the relevant event, so every "
    "Indian copyright expires on a 31 December. And where a work has joint authors, the "
    "clock starts only on the death of the last of them to die.")

d.table(
    "Table 8 \u2014 Term of Copyright and Related Rights by Category",
    ["Category of Work", "Term of Protection", "Provision"],
    [
        ["Literary, dramatic, musical or artistic work published in the author's lifetime",
         "The author's lifetime plus 60 years, counted from the year following the year "
         "of death", "S. 22"],
        ["Work of joint authorship",
         "60 years from the year following the death of the last surviving author",
         "S. 22 with S. 2(z)"],
        ["Anonymous or pseudonymous work",
         "60 years from the year following first publication; if the author's identity "
         "is disclosed, 60 years from the author's death instead", "S. 23"],
        ["Posthumous work \u2014 published after the author's death",
         "60 years from the year following the year of first publication", "S. 24"],
        ["Photograph",
         "The author's lifetime plus 60 years; the separate 50-year rule in S. 25 was "
         "omitted by the 2012 amendment, so photographs are now treated like any other "
         "artistic work", "S. 22"],
        ["Cinematograph film",
         "60 years from the year following the year of publication", "S. 26"],
        ["Sound recording",
         "60 years from the year following the year of publication", "S. 27"],
        ["Government work",
         "60 years from the year following the year of first publication", "S. 28"],
        ["Work of a public undertaking",
         "60 years from the year following the year of first publication", "S. 28A"],
        ["Work of an international organisation",
         "60 years from the year following the year of first publication", "S. 29"],
        ["Broadcast reproduction right",
         "25 years from the beginning of the year following the year of the broadcast",
         "S. 37"],
        ["Performer's right",
         "50 years from the beginning of the year following the year of the performance",
         "S. 38"],
    ],
    [1.85, 2.6, 0.62])

d.figure(L.FIG4_H, L.fig4,
         "Figure 4 \u2014 Duration of exclusivity compared across copyright and "
         "related rights.")

d.table(
    "Table 9 \u2014 The Indian Term in International Perspective",
    ["Jurisdiction", "Works with a Human Author", "Films and Sound Recordings"],
    [
        ["India", "Life of the author plus 60 years",
         "60 years from publication"],
        ["Berne Convention minimum", "Life of the author plus 50 years",
         "50 years from making or publication"],
        ["United States", "Life plus 70 years; 95 years from publication for works "
                          "made for hire", "95 years from publication"],
        ["European Union and United Kingdom", "Life plus 70 years",
         "70 years for sound recordings; 70 years from the death of the principal "
         "director and other named authors for films"],
        ["Japan and Canada", "Life plus 70 years",
         "70 years from publication"],
    ],
    [1.15, 1.7, 2.0])

d.para(
    "When the term ends the work enters the public domain permanently and irrevocably. "
    "Anyone may then copy, perform, translate, adapt, film or sell it without permission "
    "or payment. Three qualifications matter in practice. A new edition, translation, "
    "arrangement or restoration attracts a fresh copyright, but only in the new "
    "expressive material that the editor or translator has added, not in the underlying "
    "public domain work. A brand name or logo associated with the work may continue "
    "indefinitely as a trade mark. And moral rights under Section 57 are, on the Indian "
    "view, exercisable by the author's representatives even in respect of works whose "
    "economic term has run out.")

d.casebox(
    "**Case Study \u2014 The Tagore Copyright and Visva-Bharati (1941 to 2001).** "
    "Rabindranath Tagore died in August 1941, and by his bequest the copyright in his "
    "vast body of songs, poems, plays and prose was administered by Visva-Bharati, the "
    "university he founded. Under the term then in force \u2014 the author's life plus "
    "fifty years \u2014 the copyright would have expired at the end of 1991, and the "
    "university's approvals for the publication, translation and musical arrangement of "
    "Rabindrasangeet would have ceased to be required. In 1991 Parliament extended the "
    "general term from fifty to sixty years, and because the amendment applied to "
    "subsisting copyrights the exclusivity was carried forward to 31 December 2001. On "
    "1 January 2002 the entire corpus entered the public domain, and the effect was "
    "immediate and visible: new editions, new translations and new recorded "
    "interpretations appeared without anybody's permission. The episode is a compact "
    "illustration of four rules at once \u2014 that the term for a literary or musical "
    "work is measured from the author's death and not from publication, that it is "
    "computed from the beginning of the following calendar year and therefore always "
    "expires on 31 December, that a legislature may extend a term and thereby revive "
    "exclusivity in works about to fall free, and that expiry, once it happens, cannot "
    "be undone.")

# ================================= 6. Registration, infringement and remedies
d.heading("6. Registration, Infringement, Defences and Remedies")

d.para(
    "Registration is optional, but it is worth having. Section 48 makes the Register of "
    "Copyrights prima facie evidence of the particulars entered in it, which in "
    "litigation converts a contested question of ownership into a rebuttable "
    "presumption in the plaintiff's favour, and criminal complaints and customs actions "
    "proceed far more smoothly with a registration certificate in hand.")

d.table(
    "Table 10 \u2014 The Copyright Registration Procedure",
    ["Stage", "What Happens"],
    [
        ["Application", "Form XIV is filed online with the prescribed fee, a statement "
                        "of particulars and, where required, a no-objection certificate "
                        "from the author or other rights holders"],
        ["Diary number", "A diary number is issued; a mandatory waiting period of 30 "
                         "days follows, during which any person may object to the "
                         "registration"],
        ["Scrutiny", "If no objection is received the application is examined for "
                     "discrepancies; objections or discrepancies lead to a letter and, "
                     "if necessary, a hearing before the Registrar"],
        ["Registration", "The particulars are entered in the Register of Copyrights and "
                         "an extract is issued to the applicant"],
        ["Evidentiary use", "The extract is prima facie evidence under Section 48 in "
                            "civil, criminal and customs proceedings"],
    ],
    [0.8, 3.2])

d.para(
    "Infringement is defined by Section 51. Primary infringement is doing, without "
    "licence, any act that only the owner may do. Secondary infringement covers "
    "permitting a place to be used for a public performance for profit, and dealing "
    "commercially in infringing copies. The test applied is not identity but substantial "
    "reproduction: whether the defendant has appropriated the material and essential "
    "features of the plaintiff's expression, judged by the impression of an ordinary "
    "observer rather than by counting the differences. Against that stands the fair "
    "dealing catalogue in Section 52, which includes private and personal use, research, "
    "criticism and review, reporting of current events, use in judicial proceedings, "
    "performance in the course of instruction, back-up copies and lawful "
    "interoperability of computer programmes, and the conversion of any work into an "
    "accessible format for the benefit of persons with disabilities. Sections 65A and "
    "65B, inserted in 2012, separately criminalise the circumvention of technological "
    "protection measures and the removal of rights management information.")

d.table(
    "Table 11 \u2014 Remedies Available for Infringement of Copyright",
    ["Type of Remedy", "Instrument", "Practical Effect"],
    [
        ["Civil", "Interim and permanent injunction under S. 55",
         "Stops the infringing publication, performance or upload"],
        ["Civil", "Damages, or an account of profits",
         "Compensates the loss suffered or strips the infringer's gain"],
        ["Civil", "John Doe or Anton Piller order",
         "Search, seizure and relief against unnamed defendants before trial, widely "
         "used before film releases"],
        ["Civil", "Delivery up and destruction of infringing copies and plates",
         "Removes pirated stock and the means of producing it"],
        ["Criminal", "Prosecution under S. 63 \u2014 a cognisable offence",
         "Imprisonment of six months to three years and a fine between fifty thousand "
         "and two lakh rupees"],
        ["Administrative", "Notice to the Commissioner of Customs under S. 53",
         "Detention of infringing consignments at the border"],
        ["Digital", "Dynamic injunction; takedown notice under the intermediary rules",
         "Blocking of rogue websites and their subsequently created mirrors"],
        ["Institutional", "Copyright societies registered under S. 33; statutory "
                          "licence under S. 31D",
         "Collective licensing, tariff setting and royalty distribution"],
    ],
    [0.85, 1.9, 2.1])

d.figure(L.FIG5_H, L.fig5,
         "Figure 5 \u2014 The eight stages through which a copyright is created, "
         "exploited, defended and released.")

d.casebox(
    "**Case Study \u2014 UTV Software Communication Ltd. v. 1337x.to, Delhi High Court "
    "(2019).** A group of film studios sued more than thirty file-sharing websites whose "
    "operators were anonymous, whose servers were abroad and whose domains were replaced "
    "with near-identical mirrors within hours of any blocking order. The Court held that "
    "online infringement is not a lesser species of infringement and that the remedy has "
    "to be shaped to the medium. It set out indicative tests for identifying a "
    "\u201cflagrantly infringing online location\u201d \u2014 the primary purpose of the "
    "site, the concealment of its ownership, the absence of any takedown mechanism, the "
    "volume of traffic and its own encouragement of infringement \u2014 and then granted "
    "what has become known as a dynamic injunction: an order that the plaintiff may "
    "extend to newly appearing mirror and redirect domains by applying to the Joint "
    "Registrar, without filing a fresh suit each time. The judgment also distinguished "
    "the site operator from the ordinary viewer, declining to treat individual users as "
    "targets. It is the leading Indian authority on digital copyright enforcement and on "
    "the obligations of internet service providers.")

# ===================================== 7. Administration of copyright in India
d.heading("7. Administration of Copyright in India")

d.para(
    "Copyright administration was historically separate from industrial property, but "
    "the two were brought together in 2016 when the Copyright Office was transferred "
    "from the Ministry of Human Resource Development to the Department for Promotion of "
    "Industry and Internal Trade, and placed under the Controller General of Patents, "
    "Designs and Trade Marks. Adjudication has also been consolidated: the Copyright "
    "Board was merged into the Intellectual Property Appellate Board in 2017, and when "
    "that body was abolished by the Tribunals Reforms Act, 2021 its functions passed to "
    "the Commercial Courts and the High Courts.")

d.table(
    "Table 12 \u2014 The Institutions and What Each One Does",
    ["Institution", "Location and Status", "Function"],
    [
        ["Copyright Office", "New Delhi; under DPIIT since 2016",
         "Receives applications, maintains the Register of Copyrights, issues extracts"],
        ["Registrar and Deputy Registrars of Copyrights", "Within the Copyright Office",
         "Scrutiny, hearings on objections and discrepancies, entries and rectification"],
        ["CGPDTM", "Headquarters at Mumbai",
         "Administrative control over the Copyright Office alongside patents, designs, "
         "trade marks and geographical indications"],
        ["Commercial Courts and High Courts", "Across the country",
         "Hear copyright suits, statutory licence disputes and appeals after the "
         "abolition of the IPAB in 2021"],
        ["Copyright societies under S. 33",
         "IPRS, PPL, ISRA and SCRIPT among others",
         "Collective licensing of public performance and communication rights, tariff "
         "publication and royalty distribution"],
        ["Cell for IPR Promotion and Management", "New Delhi, under DPIIT",
         "Awareness, training, and coordination of the National IPR Policy of 2016"],
    ],
    [1.3, 1.4, 2.3])

d.figure(L.FIG6_H, L.fig6,
         "Figure 6 \u2014 Administrative structure governing copyright in India.")

# ==================================================== 8. Viva questions
d.heading("8. Viva Questions and Answers")

QA = [
    ("Why does copyright need no registration while a patent does?",
     "Because copyright protects expression, which is self-evident from the work "
     "itself, whereas a patent protects a technical monopoly that has to be examined "
     "for novelty and inventive step before it can be justified. Article 5(2) of the "
     "Berne Convention forbids member states from making copyright depend on any "
     "formality, so registration in India is voluntary and, under Section 48, only "
     "evidentiary."),
    ("What is the difference between copyright and a related right?",
     "Copyright belongs to the author of an original work and is conditional on "
     "originality. A related or neighbouring right belongs to a performer, a producer of "
     "a sound recording or a broadcasting organisation, requires no originality, and "
     "rewards performance, fixation or dissemination rather than authorship. India "
     "recognises them in Sections 37, 38, 38A and 38B."),
    ("Does a performer have rights in a performance of a public domain work?",
     "Yes. The performer's right under Section 38 attaches to the performance itself. "
     "The underlying work need not be original, need not previously have been fixed in "
     "any medium, and may be in the public domain or improvised on the spot."),
    ("Distinguish authorship from ownership with an example.",
     "Authorship is a fact fixed by Section 2(d); ownership is a legal allocation made "
     "by Section 17. A staff journalist is the author of the article she writes, but the "
     "proprietor of the newspaper is the first owner so far as publication in that "
     "newspaper is concerned. She remains the author permanently, retains her moral "
     "rights, and the term of protection is still measured from her death."),
    ("Who owns a wedding photograph, and who owns a photograph taken by a salaried "
     "photographer?",
     "A wedding photograph is commissioned for valuable consideration, so under Section "
     "17(b) the client who commissioned it is the first owner, though the photographer "
     "remains the author. A photograph taken by a salaried photographer in the course of "
     "employment vests in the employer under Section 17(c). Both rules yield to an "
     "agreement to the contrary."),
    ("What is the difference between a contract of service and a contract for service "
     "for copyright purposes?",
     "A contract of service is employment, and Section 17(c) vests the copyright in "
     "works made in its course in the employer. A contract for service is an independent "
     "engagement, and the copyright stays with the consultant or freelancer unless there "
     "is a written assignment complying with Sections 18 and 19. This distinction is the "
     "commonest cause of ownership disputes in software and design projects."),
    ("How exactly is the sixty-year term calculated?",
     "From the beginning of the calendar year next following the year of the relevant "
     "event \u2014 the author's death for literary, dramatic, musical and artistic "
     "works, and first publication for films, sound recordings, anonymous works, "
     "Government works and works of public undertakings. Every Indian copyright "
     "therefore expires on 31 December. For joint authors the clock starts on the death "
     "of the last survivor."),
    ("Has the term for photographs changed?",
     "Yes. Section 25 formerly gave photographs a flat fifty years from publication. The "
     "2012 amendment omitted that section, so a photograph is now treated like any other "
     "artistic work and enjoys the author's lifetime plus sixty years."),
    ("What are moral rights, and can they be assigned away?",
     "Section 57 gives the author the right of paternity, to claim authorship, and the "
     "right of integrity, to restrain distortion, mutilation or modification prejudicial "
     "to honour or reputation. They exist independently of the economic rights, survive "
     "an unconditional assignment, and are exercisable by the author's legal "
     "representatives. Amar Nath Sehgal v. Union of India (2005) applied them even "
     "against destruction of the work by its owner."),
    ("What test does Indian law apply to originality, and which case settled it?",
     "A minimal degree of creativity \u2014 skill and judgment that is more than "
     "trivial and more than purely mechanical. Eastern Book Company v. D. B. Modak "
     "(2008) rejected both the English sweat of the brow standard and any requirement of "
     "novelty, holding editorial headnotes protectable while copy-edited judgment text "
     "was not."),
]

for i, (q, a) in enumerate(QA, start=1):
    d.numbered(["**Q: %s**" % q], space_after=3.0, start=i)
    d.para("**A:** %s" % a, indent=30.0, space_after=8.0, size=11)

# ==================================================== 9. Learning outcomes
d.heading("9. Learning Outcomes")

d.bullets([
    "Defined copyright as a right over original expression rather than over ideas, "
    "explained why it arises automatically on creation, and placed it within the wider "
    "framework of intellectual property rights and the Berne, Rome, TRIPS, WCT, WPPT "
    "and Marrakesh obligations that India has accepted.",
    "Set out the bundle of economic rights conferred by Section 14 category by "
    "category, the moral rights of paternity and integrity under Section 57, and the "
    "reasons why the rights of performers, producers of sound recordings and "
    "broadcasting organisations are treated as related or neighbouring rights.",
    "Identified and classified the works protected by copyright \u2014 literary, "
    "dramatic, musical and artistic works, cinematograph films, sound recordings, "
    "software, databases, maps and technical drawings, labels and advertisements, and "
    "multimedia products \u2014 and marked the boundary against ideas, facts, methods "
    "and titles.",
    "Differentiated authorship under Section 2(d) from first ownership under Section "
    "17, worked through the employment, commissioning, speech, Government and public "
    "undertaking situations, and explained why ownership is transferable while "
    "authorship is not.",
    "Interpreted the duration of protection under Sections 22 to 29, including the "
    "calendar-year computation rule, the position of joint, anonymous and posthumous "
    "works, the revised treatment of photographs, and the shorter terms attaching to "
    "performances and broadcasts.",
    "Applied these concepts through decided cases \u2014 Amar Nath Sehgal, Neha "
    "Bhasin, Eastern Book Company v. Modak, R. G. Anand, IPRS v. EIMPA, V. T. Thomas, "
    "the Tagore public domain episode and UTV Software v. 1337x \u2014 to see how the "
    "statutory language behaves under litigation.",
    "Evaluated the ethical use of protected material by working through the Section 52 "
    "fair dealing exceptions, the registration and enforcement machinery, and the "
    "administrative structure of the Copyright Office under DPIIT.",
])

# ------------------------------------------------------------------ output
out = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                   "Experiment_1.4_Copyright_Mohammad_Saood.pdf")
n = d.save(out)

problems = d.validate()
print("pages: %d" % n)
print("output: %s (%d bytes)" % (out, os.path.getsize(out)))
if M.missing:
    print("MISSING GLYPHS: %r" % sorted(M.missing))
if problems:
    print("LAYOUT PROBLEMS (%d):" % len(problems))
    for p in problems[:40]:
        print("  " + p)
    sys.exit(1)
print("layout OK")

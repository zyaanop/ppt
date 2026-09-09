"""
medjar.corpus — a small, versioned, evidence-graded knowledge corpus.

In deployment this layer is backed by licensed guideline and reference text.
Here we ship a compact, paraphrased corpus so the prototype is runnable and
self-contained; each passage carries the metadata the retriever and the
consensus engine actually use (grade, year, specialty scope).

NOTE: passage text is original paraphrase written for this prototype, not
verbatim guideline text, and is illustrative only — not clinical guidance.
"""
from __future__ import annotations

from typing import List

from .schemas import Passage

_P = [
    # ---------------- imaging / radiology ----------------
    ("RAD-001", "Thoracic Imaging Reference", "Solitary pulmonary nodule", 2023, "textbook",
     ("radiology", "oncology"),
     "A solitary pulmonary nodule with spiculated margins carries a high pretest probability of "
     "malignancy; spiculation reflects desmoplastic reaction and interlobular septal invasion. "
     "Upper-lobe location and larger diameter further increase malignant likelihood."),
    ("RAD-002", "Thoracic Imaging Reference", "Benign nodule morphology", 2023, "textbook",
     ("radiology",),
     "Smooth well-circumscribed margins, diffuse or central calcification, and intralesional fat "
     "favour a benign nodule such as granuloma or hamartoma. Absence of growth over two years of "
     "imaging surveillance supports benignity."),
    ("RAD-003", "Imaging Appropriateness Criteria", "Nodule characterization", 2022, "IIa-B",
     ("radiology", "oncology"),
     "For an indeterminate solid pulmonary nodule with intermediate-to-high malignancy risk, "
     "FDG PET-CT is appropriate for characterization and nodal staging prior to tissue sampling."),
    ("RAD-004", "Thoracic Imaging Reference", "Pericardial effusion on CT", 2021, "textbook",
     ("radiology", "cardiology"),
     "Pericardial fluid is well seen on contrast CT; CT cannot establish haemodynamic significance. "
     "Effusion in a patient with suspected thoracic malignancy raises concern for pericardial "
     "involvement but is not itself diagnostic of malignant aetiology."),

    # ---------------- cardiology ----------------
    ("CAR-001", "Pericardial Disease Guideline", "Tamponade diagnosis", 2023, "I-B",
     ("cardiology",),
     "Cardiac tamponade is a clinical and echocardiographic diagnosis. Supportive features include "
     "sinus tachycardia, pulsus paradoxus, elevated jugular venous pressure, and on echocardiography "
     "right ventricular diastolic collapse with respirophasic septal shift. Transthoracic "
     "echocardiography is indicated urgently when tamponade is suspected."),
    ("CAR-002", "Pericardial Disease Guideline", "Effusion aetiology", 2023, "I-A",
     ("cardiology", "oncology"),
     "Determining the aetiology of a pericardial effusion requires fluid analysis. Cytological "
     "examination of pericardial fluid is required to establish a malignant effusion; imaging "
     "appearance alone is insufficient for that determination."),
    ("CAR-003", "Myocardial Injury Consensus", "Troponin interpretation", 2022, "I-A",
     ("cardiology",),
     "Detection of troponin above the 99th percentile indicates myocardial injury but is not "
     "specific for atherothrombotic infarction. A rise-and-fall pattern with ischaemic symptoms or "
     "ECG change supports acute coronary syndrome; a stable minor elevation without these features "
     "more often reflects non-ischaemic or supply-demand mismatch injury."),
    ("CAR-004", "Myocardial Injury Consensus", "Type 2 myocardial infarction", 2022, "IIa-B",
     ("cardiology",),
     "Type 2 myocardial infarction arises from oxygen supply-demand imbalance without acute plaque "
     "rupture, and is commonly precipitated by tachycardia, hypoxaemia, anaemia, sepsis or "
     "malignancy. Management targets the precipitating condition rather than urgent revascularization."),
    ("CAR-005", "Acute Coronary Syndrome Guideline", "ACS presentation", 2023, "I-A",
     ("cardiology",),
     "Acute coronary syndrome typically presents with ischaemic chest discomfort accompanied by "
     "dynamic ECG changes and a rising troponin. Absence of ischaemic symptoms and of dynamic ECG "
     "change substantially lowers the probability of an acute coronary syndrome."),
    ("CAR-006", "Pulmonary Embolism Guideline", "PE risk assessment", 2023, "I-B",
     ("cardiology",),
     "Pulmonary embolism should be considered in unexplained dyspnoea, particularly with active "
     "malignancy, which is an established prothrombotic risk factor. Validated clinical probability "
     "scoring should be combined with D-dimer or CT pulmonary angiography."),
    ("CAR-007", "Pericardial Disease Guideline", "Acute pericarditis", 2023, "I-B",
     ("cardiology",),
     "Acute pericarditis is suggested by pleuritic chest pain relieved by sitting forward, a "
     "pericardial friction rub, widespread ST elevation with PR depression, and often a viral "
     "prodrome. It is frequently self-limiting."),
    ("CAR-008", "Heart Failure Guideline", "Natriuretic peptides", 2022, "I-A",
     ("cardiology",),
     "Natriuretic peptide measurement is recommended when heart failure is suspected as a cause of "
     "dyspnoea; a low value in an untreated patient makes heart failure unlikely."),

    # ---------------- oncology ----------------
    ("ONC-001", "Lung Cancer Staging Manual", "Pericardial involvement", 2023, "I-A",
     ("oncology",),
     "Malignant pericardial effusion in lung carcinoma is classified as M1a disease, denoting "
     "advanced-stage classification with prognostic and treatment implications. Cytological or "
     "histological confirmation is required before assigning this category."),
    ("ONC-002", "Lung Cancer Guideline", "Tissue diagnosis", 2023, "I-A",
     ("oncology",),
     "Definitive management of suspected lung carcinoma requires histological confirmation. Tissue "
     "acquisition should be planned to provide adequate material for both histological subtyping "
     "and molecular biomarker testing."),
    ("ONC-003", "Lung Cancer Guideline", "Constitutional symptoms", 2022, "review",
     ("oncology", "general"),
     "Unintentional weight loss exceeding five per cent of body mass over six months, together with "
     "fatigue and anorexia, is a constitutional symptom pattern associated with advanced malignancy "
     "and warrants expedited investigation."),
    ("ONC-004", "Lung Cancer Guideline", "Molecular testing", 2023, "I-B",
     ("oncology",),
     "Comprehensive biomarker profiling is recommended for advanced non-small-cell lung carcinoma "
     "to identify actionable alterations before initiating systemic therapy."),
    ("ONC-005", "Oncologic Emergencies Review", "Malignant effusion management", 2021, "IIa-B",
     ("oncology", "cardiology"),
     "Symptomatic malignant pericardial effusion may require pericardiocentesis, which serves both "
     "to relieve haemodynamic compromise and to obtain fluid for cytological analysis."),

    # ---------------- infectious / other ----------------
    ("INF-001", "Tuberculosis Reference", "Pulmonary tuberculosis", 2022, "review",
     ("infectious", "radiology"),
     "Pulmonary tuberculosis can mimic malignancy, producing upper-lobe opacity, cavitation, weight "
     "loss and night sweats. Microbiological confirmation by sputum testing or nucleic acid "
     "amplification is required."),
    ("INF-002", "Pneumonia Guideline", "Community-acquired pneumonia", 2021, "I-B",
     ("infectious",),
     "Community-acquired pneumonia usually presents acutely with fever, productive cough and focal "
     "consolidation. A subacute course with weight loss and a discrete nodule is atypical."),
    ("GEN-001", "Sarcoidosis Review", "Thoracic sarcoidosis", 2020, "review",
     ("general", "radiology"),
     "Thoracic sarcoidosis characteristically produces bilateral hilar lymphadenopathy with "
     "perilymphatic nodularity, and may involve the pericardium. Histology showing non-caseating "
     "granulomas supports the diagnosis."),
    ("GEN-002", "Diagnostic Reasoning Review", "Anchoring and closure", 2019, "review",
     ("general",),
     "Diagnostic error is frequently attributable to premature closure, in which a plausible early "
     "hypothesis terminates the search before competing explanations are excluded. Deliberate "
     "consideration of alternatives mitigates this failure."),
]


def load_corpus() -> List[Passage]:
    """Return the indexed corpus."""
    return [
        Passage(pid=pid, source=src, section=sec, publish_year=yr,
                evidence_grade=grade, specialty_tags=tags, text=txt)
        for (pid, src, sec, yr, grade, tags, txt) in _P
    ]

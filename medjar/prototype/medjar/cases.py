"""
medjar.cases — synthetic, de-identified demonstration cases.

These are constructed for the prototype. They are not real patient data and
carry no clinical authority.
"""
from __future__ import annotations

from typing import Dict, List

from .schemas import CCO

CASE_001 = CCO(
    case_id="CASE-001",
    age=58, sex="F",
    presentation=(
        "Progressive exertional dyspnoea over three months with unintentional weight loss of "
        "7 kg. Contrast CT thorax shows a 2.4 cm spiculated nodule in the right upper lobe and a "
        "small pericardial effusion. High-sensitivity troponin mildly elevated and stable on "
        "repeat; ECG shows sinus tachycardia without dynamic ischaemic change. No chest pain."
    ),
    findings=(
        "dyspnea", "weight_loss", "spiculated_nodule", "upper_lobe", "smoking_history",
        "troponin_elevated", "pericardial_effusion", "tachycardia", "no_chest_pain",
        "static_ecg", "known_malignancy_risk",
    ),
    absent=("cytology_positive", "echo_rv_collapse", "ischemic_chest_pain",
            "dynamic_ecg_change", "hypotension", "raised_jvp"),
    vitals={"hr": 104.0, "sbp": 118.0, "spo2": 94.0, "rr": 20.0, "temp": 36.8},
    labs=[
        {"loinc": "67151-1", "name": "hs-troponin T", "value": 38, "unit": "ng/L",
         "ref": "<14", "flag": "H"},
        {"loinc": "33762-6", "name": "NT-proBNP", "value": 210, "unit": "pg/mL",
         "ref": "<300", "flag": "N"},
        {"loinc": "718-7", "name": "Haemoglobin", "value": 11.4, "unit": "g/dL",
         "ref": "12.0-15.5", "flag": "L"},
    ],
    imaging=[{"modality": "CT", "region": "thorax",
              "finding": "2.4 cm spiculated RUL nodule; small pericardial effusion; "
                         "no mediastinal lymphadenopathy",
              "impression": "Indeterminate nodule, malignancy not excluded"}],
    gold_dx="Primary lung malignancy",
)

CASE_002 = CCO(
    case_id="CASE-002",
    age=71, sex="M",
    presentation=(
        "Mild exertional dyspnoea. Incidental 9 mm densely calcified nodule in the left lower "
        "lobe, unchanged in size across two years of prior imaging. Weight stable, no "
        "constitutional symptoms."
    ),
    findings=("dyspnea", "calcified_nodule", "stable_two_years"),
    absent=("weight_loss", "spiculated_nodule", "pericardial_effusion", "troponin_elevated"),
    vitals={"hr": 76.0, "sbp": 132.0, "spo2": 97.0, "rr": 16.0, "temp": 36.6},
    labs=[{"loinc": "33762-6", "name": "NT-proBNP", "value": 88, "unit": "pg/mL",
           "ref": "<300", "flag": "N"}],
    imaging=[{"modality": "CT", "region": "thorax",
              "finding": "9 mm densely calcified LLL nodule, stable over 24 months",
              "impression": "Features favour benign granuloma"}],
    gold_dx="Benign pulmonary granuloma",
)

CASE_003 = CCO(
    case_id="CASE-003",
    age=64, sex="M",
    presentation=(
        "Acute severe central chest pain with diaphoresis. ECG shows dynamic ST depression in "
        "the lateral leads; high-sensitivity troponin rising on serial sampling. No nodule or "
        "effusion on imaging."
    ),
    findings=("ischemic_chest_pain", "dynamic_ecg_change", "troponin_elevated", "tachycardia",
              "dyspnea"),
    absent=("weight_loss", "spiculated_nodule", "pericardial_effusion", "no_chest_pain",
            "static_ecg"),
    vitals={"hr": 98.0, "sbp": 142.0, "spo2": 96.0, "rr": 18.0, "temp": 36.7},
    labs=[{"loinc": "67151-1", "name": "hs-troponin T", "value": 640, "unit": "ng/L",
           "ref": "<14", "flag": "H"}],
    imaging=[{"modality": "CXR", "region": "thorax", "finding": "No acute abnormality",
              "impression": "Normal"}],
    gold_dx="Acute coronary syndrome",
)

ALL_CASES: List[CCO] = [CASE_001, CASE_002, CASE_003]


def by_id() -> Dict[str, CCO]:
    return {c.case_id: c for c in ALL_CASES}

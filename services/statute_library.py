"""
services/statute_library.py
=============================

Seed reference data for the "Elements & Proof Map" feature. This feeds the
charge_elements table that already exists in schema.sql but, before this
patch, had no UI or population path.

SCOPE / HONESTY NOTE:
This is a small, hand-curated starter set, not a comprehensive or
continuously-updated statutory database. Building real nationwide coverage
(50 states + DC + federal + territories, kept current) requires an ongoing
ingestion pipeline against official sources — see README.md's "Extending
the library" section. Every entry below is marked with a source_note and
should be re-confirmed against the current official text before any
element here is relied on in an actual filing.
"""

from __future__ import annotations

LIBRARY: dict[str, dict] = {
    "18_usc_922g1": {
        "jurisdiction_code": "US",
        "citation": "18 U.S.C. § 922(g)(1)",
        "short_name": "Felon in Possession of a Firearm",
        "case_type": "CRIMINAL",
        "class_or_grade": "Federal felony",
        "max_penalty": "Up to 15 years imprisonment (18 U.S.C. § 924(a)(8)) — confirm current text.",
        "jury_instruction": "Circuit Model Criminal Jury Instructions (varies by circuit) — confirm the operative version for the trial circuit.",
        "burden": "beyond a reasonable doubt",
        "source_note": "SEED DATA — verify against current 18 U.S.C. § 922(g)(1) text and Rehaif v. United States, 588 U.S. 225 (2019), before relying on this.",
        "elements": [
            "Defendant had been previously convicted of a crime punishable by imprisonment for a term exceeding one year.",
            "Defendant knowingly possessed a firearm (actual or constructive possession).",
            "The firearm was in or affecting interstate or foreign commerce.",
            "MENS REA: Defendant knew of the status that made possession unlawful (knowledge of prohibited status) — Rehaif v. United States.",
        ],
    },
    "mi_mcl_750_110a": {
        "jurisdiction_code": "MI",
        "citation": "MCL 750.110a",
        "short_name": "Home Invasion",
        "case_type": "CRIMINAL",
        "class_or_grade": "Varies by degree (1st/2nd/3rd) under MCL 750.110a",
        "max_penalty": "Varies by degree — confirm current MCL 750.110a and sentencing guidelines.",
        "jury_instruction": "Michigan Model Criminal Jury Instructions (M Crim JI) — confirm current numbered instruction for the charged degree.",
        "burden": "beyond a reasonable doubt",
        "source_note": "SEED DATA — verify against current MCL 750.110a text and the operative M Crim JI for the specific degree charged.",
        "elements": [
            "Defendant broke and entered a dwelling, or entered without permission, or entered/remained without permission.",
            "At the time of entry (or while entering/present/exiting, depending on degree), defendant intended to commit a felony, larceny, or assault, or actually committed one.",
            "MENS REA: The specific intent element must be tied to the moment required by the charged degree — confirm timing requirement in the current M Crim JI.",
        ],
    },
    "mi_mcl_750_520b": {
        "jurisdiction_code": "MI",
        "citation": "MCL 750.520b",
        "short_name": "Criminal Sexual Conduct — First Degree",
        "case_type": "CRIMINAL",
        "class_or_grade": "Felony",
        "max_penalty": "Confirm current MCL 750.520b and sentencing guidelines — penalties are severe and fact/aggravating-circumstance dependent.",
        "jury_instruction": "Michigan Model Criminal Jury Instructions (M Crim JI 20.x series) — confirm current numbered instruction matching the specific subsection charged.",
        "burden": "beyond a reasonable doubt",
        "source_note": "SEED DATA — this statute has multiple alternative theories under different subsections; confirm exactly which subsection is charged and pull that specific element set from the current M Crim JI.",
        "elements": [
            "Defendant engaged in sexual penetration with the complainant.",
            "One or more statutory aggravating circumstances specific to the charged subsection was present (e.g., relationship, force/coercion, weapon, injury, age — confirm which subsection applies).",
            "MENS REA / additional elements vary significantly by subsection — do not rely on this generic list; pull the exact subsection's elements from the current M Crim JI before use.",
        ],
    },
    "ca_penal_459": {
        "jurisdiction_code": "CA",
        "citation": "Cal. Penal Code § 459",
        "short_name": "Burglary",
        "case_type": "CRIMINAL",
        "class_or_grade": "Felony or misdemeanor depending on degree (Cal. Penal Code § 460)",
        "max_penalty": "Varies by degree — confirm current Cal. Penal Code §§ 461, 1170.",
        "jury_instruction": "CALCRIM No. 1700 series",
        "burden": "beyond a reasonable doubt",
        "source_note": "SEED DATA — verify against current Cal. Penal Code § 459 and CALCRIM 1700.",
        "elements": [
            "Defendant entered a building, room, structure, or specified locked vehicle.",
            "At the time of entry, defendant intended to commit a felony or theft.",
            "MENS REA: Specific intent to commit theft or a felony must exist at the moment of entry.",
        ],
    },
    "common_law_negligence": {
        "jurisdiction_code": None,
        "citation": "Common-law tort (confirm any state statutory modification, e.g., comparative-fault statutes)",
        "short_name": "Negligence",
        "case_type": "CIVIL",
        "class_or_grade": "Civil cause of action",
        "max_penalty": None,
        "jury_instruction": "State civil pattern jury instructions (varies by state)",
        "burden": "preponderance of the evidence",
        "source_note": "SEED DATA — confirm the forum state's current pattern instruction and any statutory modification (e.g., comparative negligence rules).",
        "elements": [
            "Defendant owed a legal duty of care to plaintiff.",
            "Defendant breached that duty.",
            "The breach was the actual and proximate cause of plaintiff's harm.",
            "Plaintiff suffered legally cognizable damages.",
        ],
    },
}


def list_keys() -> list[str]:
    return list(LIBRARY.keys())


def get(key: str) -> dict | None:
    return LIBRARY.get(key)


def find_by_citation(text: str):
    """
    Loose match against a free-text statute/charge string a user typed into
    the charge form (e.g. "MCL 750.110a", "922(g)(1)", "home invasion").
    Returns (key, entry) or (None, None). Not a substitute for confirming
    the actual charged statute against the charging document.
    """
    if not text:
        return None, None
    norm = "".join(ch.lower() for ch in text if ch.isalnum())
    if not norm:
        return None, None
    for key, entry in LIBRARY.items():
        for candidate in (entry["citation"], entry["short_name"], key):
            cand_norm = "".join(ch.lower() for ch in candidate if ch.isalnum())
            if cand_norm and (cand_norm in norm or norm in cand_norm):
                return key, entry
    words = set(w for w in text.lower().replace("§", " ").replace(".", " ").split() if len(w) > 3)
    best_key, best_entry, best_score = None, None, 0
    for key, entry in LIBRARY.items():
        name_words = set(entry["short_name"].lower().split())
        score = len(words & name_words)
        if score > best_score:
            best_key, best_entry, best_score = key, entry, score
    if best_score > 0:
        return best_key, best_entry
    return None, None

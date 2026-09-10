"""
services/case_pipeline.py
============================

Fills in the "Elements & Proof Map" feature that schema.sql already had a
place for (charge_elements, element_evidence_links) but that had no route
or template before this patch.

What this does:
  1. sync_elements_from_library(db, charge) — if the charge's statute text
     matches a seed entry, insert its element rows into charge_elements
     (idempotent — skips element_numbers that already exist for that
     charge, so re-running or hand-edited elements are never clobbered).
  2. link_evidence(db, element_id, evidence_id, relationship, assessment) —
     record that a specific piece of already-uploaded case evidence is
     relevant to a specific element.
  3. get_pipeline_view(db, case, charge) — read everything back (elements,
     linked evidence, linked factual assertions, linked defense issues,
     the matching library entry if any) into one dict for the template.

Nothing here invents case-specific facts. Every fact shown is either (a)
already sitting in the case's own tables because the person put it there,
or (b) seed reference law explicitly marked as needing verification.
"""

from __future__ import annotations

from . import statute_library

BURDEN_EXPLAINERS = {
    "beyond a reasonable doubt": (
        "The prosecution's proof on EVERY element must be strong enough to eliminate "
        "reasonable doubt in the mind of a reasonable juror. The defense does not have to "
        "disprove anything — it only has to show that reasonable doubt exists as to at "
        "least one element."
    ),
    "preponderance of the evidence": (
        "The party with the burden must show it is more likely than not that each element "
        "is satisfied."
    ),
    "clear and convincing evidence": (
        "The party with the burden must show each element is highly probable, a higher bar "
        "than preponderance but lower than beyond a reasonable doubt."
    ),
}


def sync_elements_from_library(db, charge_row) -> tuple[str | None, int]:
    """
    Returns (matched_library_key, number_of_elements_inserted).
    Idempotent: only inserts element_numbers not already present for this charge.
    """
    key, entry = statute_library.find_by_citation(
        f"{charge_row['statute'] or ''} {charge_row['charge_name'] or ''}"
    )
    if not entry:
        return None, 0

    existing = {
        r["element_number"]
        for r in db.execute(
            "SELECT element_number FROM charge_elements WHERE charge_id=?",
            (charge_row["id"],),
        ).fetchall()
    }
    inserted = 0
    for i, element_text in enumerate(entry["elements"], start=1):
        if i in existing:
            continue
        db.execute(
            """INSERT INTO charge_elements(charge_id, element_number, element_text)
               VALUES(?,?,?)""",
            (charge_row["id"], i, f"[SEED — verify] {element_text}"),
        )
        inserted += 1
    db.commit()
    return key, inserted


ALLOWED_EVIDENCE_RELATIONSHIPS = {"RELEVANT", "SUPPORTS", "UNDERMINES", "AMBIGUOUS"}


def link_evidence(
    db,
    *,
    case_id: int,
    charge_id: int,
    element_id: int,
    evidence_id: int,
    relationship: str = "RELEVANT",
    assessment: str = "",
):
    """Link evidence only when the element and evidence belong to the same case/charge."""
    relationship = (relationship or "RELEVANT").upper()
    if relationship not in ALLOWED_EVIDENCE_RELATIONSHIPS:
        raise ValueError("Invalid evidence relationship")

    valid = db.execute(
        """SELECT 1
           FROM charge_elements el
           JOIN case_charges ch ON ch.id = el.charge_id
           JOIN case_evidence ev ON ev.case_id = ch.case_id
           WHERE ch.case_id=? AND ch.id=? AND el.id=? AND ev.id=?""",
        (case_id, charge_id, element_id, evidence_id),
    ).fetchone()
    if not valid:
        raise ValueError("Element and evidence do not belong to the same case/charge")

    db.execute(
        """INSERT INTO element_evidence_links(element_id, evidence_id, relationship, assessment)
           VALUES(?,?,?,?)""",
        (element_id, evidence_id, relationship, assessment or None),
    )
    db.commit()


def get_pipeline_view(db, case_row, charge_row) -> dict:
    key, entry = statute_library.find_by_citation(
        f"{charge_row['statute'] or ''} {charge_row['charge_name'] or ''}"
    )

    elements = db.execute(
        "SELECT * FROM charge_elements WHERE charge_id=? ORDER BY element_number",
        (charge_row["id"],),
    ).fetchall()

    elements_view = []
    for el in elements:
        links = db.execute(
            """SELECT eel.*, ce.evidence_type, ce.original_filename
               FROM element_evidence_links eel
               JOIN case_evidence ce ON ce.id = eel.evidence_id
               WHERE eel.element_id=?""",
            (el["id"],),
        ).fetchall()
        elements_view.append({
            "id": el["id"],
            "element_number": el["element_number"],
            "element_text": el["element_text"],
            "verification_status": el["verification_status"],
            "linked_evidence": [dict(l) for l in links],
        })

    case_evidence = db.execute(
        "SELECT * FROM case_evidence WHERE case_id=? ORDER BY id DESC",
        (case_row["id"],),
    ).fetchall()

    defense_issues = db.execute(
        """SELECT cdi.*, dic.issue_name FROM case_defense_issues cdi
           JOIN defense_issue_catalog dic ON dic.issue_code = cdi.issue_code
           WHERE cdi.case_id=? ORDER BY cdi.id DESC""",
        (case_row["id"],),
    ).fetchall()

    burden = entry["burden"] if entry else None

    return {
        "matched": entry is not None,
        "seed_key": key,
        "library_entry": entry,
        "burden": burden,
        "burden_explainer": BURDEN_EXPLAINERS.get(burden, ""),
        "elements": elements_view,
        "case_evidence": [dict(e) for e in case_evidence],
        "defense_issues": [dict(d) for d in defense_issues],
    }

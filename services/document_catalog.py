"""
services/document_catalog.py
==============================

Structural scaffolding for court documents: what sections a document type
needs, what has to be attached, and what a court rule generally requires —
NOT pre-written legal argument, and NOT case citations Claude/this app
invented. See document_assembly.py for the hard rule this catalog exists
to support: any case citation that ends up in a generated document must
already be sitting in this project's own legal_authorities table with
filing_ready=1 (i.e., it already went through YOUR verification workflow).
Nothing here fabricates a citation.

Every entry is deliberately conservative about specific rule numbers where
this app can't independently confirm them. Where a rule number IS asserted
(e.g., MCR 6.500 for Michigan post-conviction), it's because it already
appears elsewhere in this project's own seed data — not invented fresh here
— and it still carries a "confirm current numbering" note, because court
rules get renumbered and amended.
"""

from __future__ import annotations

DOCUMENT_TYPES: dict[str, dict] = {

    "mi_mcr6500_relief": {
        "title": "Motion for Relief from Judgment",
        "jurisdiction_code": "MI",
        "case_types": ["CRIMINAL"],
        "rule_note": (
            "Michigan MCR 6.500 series (post-conviction relief from judgment). "
            "Confirm current subrule numbering, page/format limits, and any "
            "recent amendments on the Michigan Courts website before filing."
        ),
        "deadline_note": (
            "MCR 6.500 motions are subject to procedural-default rules (a claim "
            "not raised on direct appeal generally needs 'good cause' for not "
            "raising it and 'actual prejudice' from the alleged error, unless an "
            "exception applies) and to successive-motion restrictions if this "
            "isn't the first such motion. There is not a simple fixed filing "
            "deadline the way there is for a direct appeal, but confirm the "
            "current standard — this changes how a claim must be framed."
        ),
        "required_attachments": [
            "Certified copy of the judgment of sentence",
            "Relevant transcript excerpts supporting each factual claim",
            "Any affidavits supporting facts outside the existing record",
            "Fee waiver / indigency request, if applicable",
        ],
        "sections": [
            {"key": "facts", "heading": "Statement of Facts",
             "guidance": "Chronological, record-cited. Pull only from case evidence and factual assertions already on file; anything unverified stays flagged as unverified."},
            {"key": "procedural_history", "heading": "Procedural History",
             "guidance": "Trial court, plea or verdict, sentence, direct appeal history (if any), and any prior post-conviction motions (a prior MCR 6.500 motion raises the successive-motion bar — say so if one exists)."},
            {"key": "grounds", "heading": "Grounds for Relief",
             "guidance": "State each ground for relief as its own numbered claim, one sentence identifying the specific constitutional or legal basis for each."},
            {"key": "argument", "heading": "Argument",
             "guidance": "For each ground: the legal standard (cite only filing-ready, verified authority from this project's own authority index — leave a [VERIFY CITATION] placeholder for anything not yet verified), how it applies to the facts above, and — if the issue was not raised on direct appeal — the required good-cause/actual-prejudice or newly-discovered-evidence showing."},
            {"key": "relief", "heading": "Relief Requested",
             "guidance": "State precisely what the court is being asked to do (vacate the conviction, order a new trial, resentence, hold an evidentiary hearing, etc.)."},
        ],
        "closing_requirements": [
            "Verification/oath in the form required by current court rule",
            "Certificate of service on the prosecuting attorney",
            "Signature block",
        ],
    },

    "generic_motion_to_suppress": {
        "title": "Motion to Suppress Evidence",
        "jurisdiction_code": None,
        "case_types": ["CRIMINAL"],
        "rule_note": (
            "Structure only — confirm the specific rule governing suppression "
            "motions (timing, required contents, hearing procedure) for the "
            "actual trial court and jurisdiction before filing."
        ),
        "deadline_note": "Suppression motions are frequently subject to a pretrial cutoff or omnibus-hearing deadline set by local rule or scheduling order — confirm the specific deadline in this case.",
        "required_attachments": [
            "Police report(s) or incident report(s) at issue",
            "Any warrant and supporting affidavit, if one was used",
            "Body-camera / dash-camera footage or transcript, if it exists",
        ],
        "sections": [
            {"key": "facts", "heading": "Statement of Facts",
             "guidance": "What happened, in the order it happened — the stop/search/seizure/interrogation at issue, drawn only from verified case evidence and assertions."},
            {"key": "legal_standard", "heading": "Legal Standard",
             "guidance": "The controlling constitutional/statutory standard for this type of search, seizure, or statement (e.g., warrant requirement and exceptions, Miranda, voluntariness). Cite only filing-ready verified authority; otherwise leave [VERIFY CITATION]."},
            {"key": "argument", "heading": "Argument",
             "guidance": "Apply the standard to the specific facts — why this stop/search/seizure/statement did not satisfy it."},
            {"key": "relief", "heading": "Relief Requested",
             "guidance": "The specific evidence or statements sought to be suppressed."},
        ],
        "closing_requirements": ["Signature block", "Certificate of service", "Notice of hearing, if required locally"],
    },

    "generic_motion_in_limine": {
        "title": "Motion in Limine",
        "jurisdiction_code": None,
        "case_types": ["CRIMINAL", "CIVIL"],
        "rule_note": "Structure only — confirm local rules on timing and format for motions in limine in the actual trial court.",
        "deadline_note": "Typically due before trial per a scheduling order or local rule — confirm the specific deadline in this case.",
        "required_attachments": ["Any exhibit or document the motion asks the court to exclude/admit"],
        "sections": [
            {"key": "issue", "heading": "Evidentiary Issue Presented",
             "guidance": "Identify precisely what evidence, testimony, or argument the motion addresses."},
            {"key": "legal_standard", "heading": "Legal Standard",
             "guidance": "The specific evidence rule or doctrine at issue (relevance, prejudice balancing, hearsay exception, character evidence, etc.). Cite only filing-ready verified authority."},
            {"key": "argument", "heading": "Argument",
             "guidance": "Why the standard requires exclusion (or admission) here."},
            {"key": "relief", "heading": "Relief Requested",
             "guidance": "The specific order requested."},
        ],
        "closing_requirements": ["Signature block", "Certificate of service"],
    },
}


def list_types(jurisdiction_code: str | None = None, case_type: str | None = None) -> list[str]:
    keys = []
    for key, entry in DOCUMENT_TYPES.items():
        if jurisdiction_code and entry["jurisdiction_code"] not in (None, jurisdiction_code):
            continue
        if case_type and case_type not in entry["case_types"]:
            continue
        keys.append(key)
    return keys


def get(key: str) -> dict | None:
    return DOCUMENT_TYPES.get(key)

from __future__ import annotations

import re

from . import statute_library


def _statute_hit(text: str) -> bool:
    key, entry = statute_library.find_by_citation(text)
    return entry is not None


def _rows(db, sql, args=()):
    return db.execute(sql, args).fetchall()


def _one(db, sql, args=()):
    return db.execute(sql, args).fetchone()


def _authority_hits(db, message: str, limit: int = 5):
    terms = [t for t in re.findall(r"[A-Za-z0-9§\.\-]+", message) if len(t) > 3]
    if not terms:
        return []
    clauses, args = [], []
    for term in terms[:4]:
        clauses.append("(title LIKE ? OR citation LIKE ? OR summary LIKE ?)")
        like = f"%{term}%"
        args.extend([like, like, like])
    sql = "SELECT id,title,citation,jurisdiction_code,summary,verification_status FROM legal_authorities WHERE " + " OR ".join(clauses)
    sql += " ORDER BY CASE verification_status WHEN 'VERIFIED' THEN 0 WHEN 'READY' THEN 1 ELSE 2 END, jurisdiction_code, title LIMIT ?"
    args.append(limit)
    return _rows(db, sql, tuple(args))


def _case_snapshot(db, case_id: int):
    case = _one(db, "SELECT * FROM case_workspaces WHERE id=?", (case_id,))
    if not case:
        return None
    counts = {
        "evidence": _one(db, "SELECT COUNT(*) n FROM case_evidence WHERE case_id=?", (case_id,))["n"],
        "assertions": _one(db, "SELECT COUNT(*) n FROM case_factual_assertions WHERE case_id=?", (case_id,))["n"],
        "discovery": _one(db, "SELECT COUNT(*) n FROM case_discovery_tracker WHERE case_id=?", (case_id,))["n"],
        "issues": _one(db, "SELECT COUNT(*) n FROM case_defense_issues WHERE case_id=?", (case_id,))["n"],
        "runs": _one(db, "SELECT COUNT(*) n FROM document_analysis_runs WHERE case_id=?", (case_id,))["n"],
    }
    return case, counts


def respond(db, message: str, *, case_id: int | None = None, private_ok: bool = False):
    text = (message or "").strip()
    lower = text.lower()

    result = {
        "assistant": "Finessa",
        "mode": "legal-information",
        "answer": "",
        "actions": [],
        "authorities": [],
        "notice": "Legal information only. Verify controlling law and official records; individual legal advice belongs with a licensed attorney.",
    }

    if not text:
        result["answer"] = "Tell me what you are trying to understand, organize, verify, or prepare. I can guide you to the right Finessa workspace."
        return result

    if any(k in lower for k in ["guilty", "not guilty", "no contest", "nolo", "plea"]):
        result["answer"] = (
            "Plea choices can change what the prosecution must prove, which rights are waived, and what issues remain available for appeal or later review. "
            "A not-guilty plea generally requires the prosecution to prove the charge under the governing burden of proof. A guilty plea is an admission that ordinarily waives trial rights after a valid colloquy. "
            "A no-contest or nolo contendere plea usually allows conviction without a factual admission in the same form as a guilty plea, but its availability and collateral effects vary by jurisdiction. "
            "Before choosing any plea, verify the exact charge, maximum penalties, collateral consequences, plea agreement, preserved issues, and the court's required colloquy."
        )
        result["actions"] = [
            {"label": "Research authorities", "href": "/authorities"},
            {"label": "Open jurisdiction guide", "href": "/jurisdictions"},
        ]
    elif any(k in lower for k in ["upload", "evidence", "document", "police report", "discovery"]):
        if private_ok and case_id:
            snap = _case_snapshot(db, case_id)
            if snap:
                case, counts = snap
                result["answer"] = (
                    f"For {case['case_name']}, the workspace currently contains {counts['evidence']} evidence item(s), "
                    f"{counts['discovery']} discovery-tracker item(s), and {counts['runs']} document-intelligence run(s). "
                    "A useful workflow is: preserve the original file, record provenance, run document intelligence, classify factual assertions, then connect verified evidence to issues and missing-record requests."
                )
                result["actions"] = [
                    {"label": "Case workspace", "href": f"/cases/{case_id}"},
                    {"label": "Document intelligence", "href": f"/cases/{case_id}/documents/intelligence"},
                    {"label": "Defense workspace", "href": f"/cases/{case_id}/defense"},
                ]
            else:
                result["answer"] = "I could not find that case workspace. Open Private Workspace and select the case you want me to use."
        else:
            result["answer"] = (
                "Use the private case workspace for legal documents. Finessa preserves the original filename, stores a SHA-256 digest, and can run document intelligence to identify classifications, findings, and record gaps. "
                "Case-specific material should stay behind authentication."
            )
            result["actions"] = [{"label": "Private Workspace", "href": "/cases"}]
    elif any(k in lower for k in ["element", "elements", "prove", "burden of proof", "reasonable doubt"]) or _statute_hit(text):
        key, entry = statute_library.find_by_citation(text)
        if entry:
            proving_party = "the government" if entry.get("case_type") == "CRIMINAL" else "the party bringing the claim"
            result["answer"] = (
                f"{entry['citation']} — {entry['short_name']}: {proving_party} has to prove {len(entry['elements'])} element(s) "
                f"to the standard of {entry['burden']}. This is seed reference data, not verified current law — {entry['source_note']}"
            )
            result["actions"] = [{"label": "Open Elements & Proof Map (from your charge)", "href": "/cases"}]
        else:
            result["answer"] = (
                "I don't have a seed element breakdown for that statute yet. If you've entered this charge on a case, "
                "open its Elements & Proof Map page — you can add elements there by hand and link your own evidence to each one."
            )
            result["actions"] = [{"label": "Private Workspace", "href": "/cases"}]
    elif any(k in lower for k in ["case", "citation", "authority", "statute", "precedent", "law"]):
        hits = _authority_hits(db, text)
        result["authorities"] = [dict(r) for r in hits]
        if hits:
            result["answer"] = (
                f"I found {len(hits)} potentially relevant authority record(s) in the local Justice Gateway legal index. "
                "Treat these as research leads until the citation, court, precedential status, current validity, and proposition are verified against an official or reliable primary source."
            )
        else:
            result["answer"] = (
                "I did not find a strong match in the current local authority index. Try the specific jurisdiction, statute number, case name, constitutional issue, or procedural rule."
            )
        result["actions"] = [{"label": "Authority search", "href": "/authorities"}, {"label": "Verification workbench", "href": "/verification-workbench"}]
    elif any(k in lower for k in ["motion", "appeal", "suppress", "brady", "franks", "ineffective", "post conviction", "post-conviction"]):
        result["answer"] = (
            "Start by separating the procedural vehicle from the factual theory. Identify the current posture, deadline, preservation requirements, governing burden, admissible supporting evidence, and requested relief. "
            "Finessa can organize issues and motion candidates, but a filing should be based on verified authorities and authenticated facts rather than an AI conclusion."
        )
        result["actions"] = [{"label": "Research", "href": "/research"}, {"label": "Verification", "href": "/verification-workbench"}]
    else:
        result["answer"] = (
            "I can help you use Finessa in four ways: research law and jurisdiction rules, organize a private case file, analyze uploaded records for structure and gaps, or build an attorney-facing issue and discovery checklist. "
            "Tell me the jurisdiction and what you want to accomplish next."
        )
        result["actions"] = [{"label": "Research law", "href": "/research"}, {"label": "Browse jurisdictions", "href": "/jurisdictions"}, {"label": "Private Workspace", "href": "/cases"}]

    if not result["authorities"] and len(text) > 8:
        result["authorities"] = [dict(r) for r in _authority_hits(db, text, limit=3)]
    return result

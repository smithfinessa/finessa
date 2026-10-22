from __future__ import annotations

from db import _connect
from providers import OFFICIAL_JURISDICTIONS


def seed():
    db = _connect()
    try:
        for code, info in OFFICIAL_JURISDICTIONS.items():
            verification_status = "VERIFIED" if info["coverage_status"] == "REFERENCE" else "UNVERIFIED"
            db.execute(
                """
                INSERT INTO jurisdictions(
                    code, name, kind, parent_code,
                    official_source_url, constitution_url, admin_code_url,
                    coverage_status, verification_status
                ) VALUES(?,?,?,?,?,?,?,?,?)
                ON CONFLICT(code) DO UPDATE SET
                    name=excluded.name,
                    kind=excluded.kind,
                    parent_code=excluded.parent_code,
                    official_source_url=excluded.official_source_url,
                    constitution_url=excluded.constitution_url,
                    admin_code_url=excluded.admin_code_url,
                    coverage_status=excluded.coverage_status,
                    verification_status=excluded.verification_status
                """,
                (
                    code,
                    info["name"],
                    info["kind"],
                    info["parent_code"],
                    info["official_source_url"],
                    info["constitution_url"],
                    info["admin_code_url"],
                    info["coverage_status"],
                    verification_status,
                ),
            )

        for topic in [
            "Criminal procedure",
            "Civil procedure",
            "Search and seizure",
            "Evidence",
            "Post-conviction",
            "Constitutional law",
            "Legislation",
        ]:
            db.execute("INSERT OR IGNORE INTO legal_topics(name) VALUES(?)", (topic,))

        issues = [
            ("SUPPRESSION", "Suppression / exclusion", "Potential constitutional or evidentiary exclusion issue."),
            ("DISCOVERY", "Discovery / disclosure", "Potential missing disclosure, discovery, or preservation issue."),
            ("IDENTITY", "Identity / attribution", "Whether the evidence reliably identifies or attributes conduct to the accused/party."),
            ("MENS_REA", "Mens rea / intent", "Whether the required mental state can be proven."),
            ("ELEMENT_FAILURE", "Element failure", "Whether proof is insufficient as to one or more required elements."),
            ("INEFFECTIVE_ASSISTANCE", "Counsel performance issue", "Potential attorney-performance issue requiring governing-law analysis."),
        ]
        for row in issues:
            db.execute(
                "INSERT OR IGNORE INTO defense_issue_catalog(issue_code, issue_name, description) VALUES(?,?,?)",
                row,
            )

        obligations = [
            ("POLICE_REPORTS", "Police / incident reports", "Collect primary and supplemental reports."),
            ("BODY_CAM", "Body-worn camera", "Identify and preserve available body-camera evidence."),
            ("FORENSICS", "Forensic reports / extraction", "Collect forensic reports and supporting chain-of-custody records."),
            ("WITNESS", "Witness statements", "Collect available statements, interviews, transcripts, and recordings."),
            ("EXCULPATORY", "Potential exculpatory/impeachment material", "Track potentially favorable or impeachment evidence; verify applicable disclosure law."),
        ]
        for row in obligations:
            db.execute(
                "INSERT OR IGNORE INTO discovery_obligations(obligation_code, obligation_name, description) VALUES(?,?,?)",
                row,
            )

        plans = [
            ("FREE", "Finessa Access", 0, None, 0, 3, 0, 0, 0),
            ("CASE", "Finessa Case", 999, 9900, 1, 50, 1, 1, 0),
            ("PLUS", "Finessa Plus", 1999, 19900, 5, 250, 1, 1, 0),
            ("PRO", "Finessa Professional", 4900, None, None, None, 1, 1, 1),
        ]
        for p in plans:
            db.execute("INSERT OR REPLACE INTO plan_entitlements VALUES(?,?,?,?,?,?,?,?,?)", p)

        seed_auth = [
            (
                "US",
                "case",
                "Rehaif v. United States",
                "588 U.S. 225 (2019)",
                "Federal firearm-status knowledge decision; verify proposition and current treatment before filing.",
                "https://supreme.justia.com/courts/supreme-court/",
                1,
                "binding",
                "2019-06-10",
                "SOURCE_VERIFIED",
                0,
            ),
            (
                "MI",
                "statute",
                "Michigan Compiled Laws — official portal",
                "MCL",
                "Primary-source portal for Michigan statutes; resolve exact section/subsection before reliance.",
                "https://www.legislature.mi.gov/Laws/MCL",
                1,
                "official",
                "2024-01-01",
                "SOURCE_VERIFIED",
                0,
            ),
        ]
        for a in seed_auth:
            db.execute(
                """
                INSERT INTO legal_authorities(
                    jurisdiction_code, authority_type, title, citation, summary, source_url,
                    official_source, precedential_status, decision_date, verification_status, filing_ready
                )
                SELECT ?,?,?,?,?,?,?,?,?,?,?
                WHERE NOT EXISTS (
                    SELECT 1 FROM legal_authorities WHERE jurisdiction_code=? AND title=?
                )
                """,
                a + (a[0], a[2]),
            )

        db.commit()
    finally:
        db.close()

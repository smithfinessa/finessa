"""Fail-closed authority selection for Finessa legal-information drafts.

No automated system can establish that an authority is good law from a flag alone.
This module checks internal verification records; human/source review remains required.
"""
from __future__ import annotations

STAGES = ('SOURCE_VERIFIED', 'CURRENCY_VERIFIED', 'JURISDICTION_VERIFIED', 'CITATION_VERIFIED')


def verification_state(records):
    """Most recent record per stage wins; failures revoke earlier passes."""
    latest = {}
    for row in records:
        stage, result = row['stage'], row['result']
        if stage in STAGES:
            latest[stage] = result == 'pass'
    return all(latest.get(stage, False) for stage in STAGES)


def candidate_authorities(db, jurisdiction_code):
    """Return candidates only when all four latest stage results pass."""
    if not jurisdiction_code:
        return []
    authorities = db.execute(
        'SELECT id, title, citation, proposition_text FROM legal_authorities '
        'WHERE jurisdiction_code=? AND filing_ready=1 ORDER BY title',
        (jurisdiction_code,),
    ).fetchall()
    selected = []
    for authority in authorities:
        rows = db.execute(
            'SELECT stage, result FROM authority_verification_records '
            'WHERE authority_id=? ORDER BY id', (authority['id'],)
        ).fetchall()
        if verification_state(rows):
            selected.append(authority)
    return selected

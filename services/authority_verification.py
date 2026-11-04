from __future__ import annotations
from .legal_release_gate import STAGES, verification_state


def record(db, authority_id: int, stage: str, passed: bool, note: str = ''):
    if stage not in STAGES:
        raise ValueError('Unknown verification stage')
    db.execute(
        'INSERT INTO authority_verification_records(authority_id,stage,result,note) VALUES(?,?,?,?)',
        (authority_id, stage, 'pass' if passed else 'fail', note or None),
    )
    rows = db.execute(
        'SELECT stage, result FROM authority_verification_records WHERE authority_id=? ORDER BY id',
        (authority_id,),
    ).fetchall()
    ready = verification_state(rows)
    db.execute(
        'UPDATE legal_authorities SET verification_status=?, filing_ready=? WHERE id=?',
        ('FILING_READY' if ready else 'RESEARCH_LEAD', 1 if ready else 0, authority_id),
    )
    db.commit()
    return ready

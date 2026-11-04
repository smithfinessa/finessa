from __future__ import annotations

STAGES = ('SOURCE_VERIFIED', 'CURRENCY_VERIFIED', 'JURISDICTION_VERIFIED', 'CITATION_VERIFIED')


def record(db, authority_id: int, stage: str, passed: bool, note: str = ''):
    if stage not in STAGES:
        raise ValueError('Unknown verification stage')

    db.execute(
        'INSERT INTO authority_verification_records(authority_id,stage,result,note) VALUES(?,?,?,?)',
        (authority_id, stage, 'pass' if passed else 'fail', note or None),
    )

    # The most recent check for each stage controls. An older successful check
    # cannot override a newer failure. SQLite rowid tracks insertion order.
    latest = {}
    for row in db.execute(
        'SELECT stage, result FROM authority_verification_records '
        'WHERE authority_id=? ORDER BY rowid DESC',
        (authority_id,),
    ).fetchall():
        if row['stage'] in STAGES and row['stage'] not in latest:
            latest[row['stage']] = row['result']

    ready = all(latest.get(required) == 'pass' for required in STAGES)
    status = 'FILING_READY' if ready else 'VERIFICATION_REQUIRED'
    db.execute(
        'UPDATE legal_authorities SET verification_status=?, filing_ready=? WHERE id=?',
        (status, 1 if ready else 0, authority_id),
    )
    db.commit()
    return ready

from __future__ import annotations
STAGES=('SOURCE_VERIFIED','CURRENCY_VERIFIED','JURISDICTION_VERIFIED','CITATION_VERIFIED')
def record(db, authority_id:int, stage:str, passed:bool, note:str=''):
    if stage not in STAGES: raise ValueError('Unknown verification stage')
    db.execute('INSERT INTO authority_verification_records(authority_id,stage,result,note) VALUES(?,?,?,?)',(authority_id,stage,'pass' if passed else 'fail',note or None))
    passed_stages={r['stage'] for r in db.execute("SELECT stage FROM authority_verification_records WHERE authority_id=? AND result='pass'",(authority_id,)).fetchall()}
    ready=all(s in passed_stages for s in STAGES)
    db.execute('UPDATE legal_authorities SET verification_status=?, filing_ready=? WHERE id=?',('FILING_READY' if ready else stage,1 if ready else 0,authority_id)); db.commit(); return ready

from __future__ import annotations

def initialize_discovery(db, case_id:int)->int:
    rows=db.execute('SELECT id FROM discovery_obligations').fetchall(); n=0
    for r in rows:
        cur=db.execute('INSERT OR IGNORE INTO case_discovery_obligations(case_id,obligation_id) VALUES(?,?)',(case_id,r['id']))
        n += 1 if cur.rowcount else 0
    db.commit(); return n

def add_defense_issue(db, case_id:int, issue_code:str, factual_basis:str=''):
    db.execute('INSERT INTO case_defense_issues(case_id,issue_code,factual_basis) VALUES(?,?,?)',(case_id,issue_code,factual_basis or None)); db.commit()

def add_motion_candidate(db, case_id:int, motion_type:str, issue_id=None, requested_relief:str=''):
    db.execute('INSERT INTO case_motion_candidates(case_id,motion_type,case_defense_issue_id,requested_relief) VALUES(?,?,?,?)',(case_id,motion_type,issue_id,requested_relief or None)); db.commit()

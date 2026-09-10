from __future__ import annotations
VALID_TYPES={'CRIMINAL','CIVIL','ADMINISTRATIVE','POST_CONVICTION','HABEAS'}
def resolve(db, *, case_id:int|None=None, jurisdiction_code:str|None=None, proceeding_type:str|None=None):
    if case_id is not None:
        row=db.execute('SELECT jurisdiction_code, proceeding_type, court_name FROM case_workspaces WHERE id=?',(case_id,)).fetchone()
        if not row: raise ValueError('Case not found')
        jurisdiction_code=jurisdiction_code or row['jurisdiction_code']; proceeding_type=proceeding_type or row['proceeding_type']; court=row['court_name']
    else: court=None
    code=(jurisdiction_code or 'US').upper(); j=db.execute('SELECT * FROM jurisdictions WHERE code=?',(code,)).fetchone()
    if not j: raise ValueError('Unsupported U.S. jurisdiction code')
    p=(proceeding_type or 'CRIMINAL').upper()
    if p not in VALID_TYPES: p='CRIMINAL' if p!='CIVIL' else 'CIVIL'
    return {'jurisdiction_code':code,'jurisdiction_name':j['name'],'proceeding_type':p,'court_name':court,'coverage_status':j['coverage_status']}

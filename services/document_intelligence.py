from __future__ import annotations
from pathlib import Path

def analyze_document(db, case_id:int, evidence_id:int)->int:
    row=db.execute('SELECT * FROM case_evidence WHERE id=? AND case_id=?',(evidence_id,case_id)).fetchone()
    if not row: raise ValueError('Evidence record not found')
    path=Path(__file__).resolve().parent.parent / row['stored_path']
    suffix=path.suffix.lower(); text=''
    if suffix in {'.txt','.md','.csv','.json','.log'}:
        text=path.read_text(encoding='utf-8',errors='replace')[:500000]
    elif suffix=='.pdf':
        text='PDF registered for analysis. Full PDF text extraction requires a configured parser in production.'
    else:
        text=f'File registered ({suffix or "unknown type"}). Automated extraction is not enabled for this format.'
    doc_class='LEGAL_DOCUMENT' if any(k in text.lower() for k in ['court','case no','plaintiff','defendant','statute','motion']) else 'UNCLASSIFIED'
    cur=db.execute('INSERT INTO document_analysis_runs(case_id,evidence_id,document_class,extracted_text) VALUES(?,?,?,?)',(case_id,evidence_id,doc_class,text))
    rid=cur.lastrowid
    if text:
        db.execute('INSERT INTO document_findings(analysis_run_id,finding_type,finding_text) VALUES(?,?,?)',(rid,'EXTRACTION',f'Extracted/registered {min(len(text),500000)} characters.'))
    db.commit(); return rid

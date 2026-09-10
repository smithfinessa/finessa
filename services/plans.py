from __future__ import annotations
def list_plans(db): return [dict(r) for r in db.execute('SELECT * FROM plan_entitlements ORDER BY monthly_cents').fetchall()]
def get_plan(db, code):
    r=db.execute('SELECT * FROM plan_entitlements WHERE plan_code=?',(code.upper(),)).fetchone(); return dict(r) if r else None

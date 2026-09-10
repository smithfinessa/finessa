from __future__ import annotations
HIGH_RISK=('plead guilty','plead not guilty','reject the plea','accept the plea','you should file','you must file','do not tell your lawyer','hide evidence','destroy evidence')
def assess(text:str, jurisdiction_code:str|None=None):
    lower=(text or '').lower()
    blocked=any(p in lower for p in ('hide evidence','destroy evidence','lie to the court','fabricate evidence'))
    individualized=any(p in lower for p in HIGH_RISK)
    if blocked:
        return {'decision':'BLOCK','reason':'Request involves concealment, destruction, fabrication, or deception.'}
    if individualized:
        return {'decision':'REFRAME','reason':'High-risk individualized legal direction should be presented as legal information/options, with attorney review recommended.'}
    return {'decision':'ALLOW','reason':'Permitted legal-information, research, organization, or self-help assistance.'}

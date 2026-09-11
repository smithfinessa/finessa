from __future__ import annotations
import hashlib, hmac, os, secrets
from pathlib import Path

from flask import Flask, abort, flash, redirect, render_template, request, session, url_for, send_file
from werkzeug.utils import secure_filename

from db import get_db, close_db, init_db
from seed import seed
from services.defense_intelligence import initialize_discovery, add_defense_issue, add_motion_candidate
from services.document_intelligence import analyze_document
from services.finessa import respond as finessa_respond
from services.case_pipeline import sync_elements_from_library, link_evidence, get_pipeline_view
from services import document_catalog
from services.document_assembly import build_docx
from services.external_legal_data import search as external_legal_search, provider_status as legal_provider_status
from services.compliance_gateway import assess as compliance_assess

BASE_DIR=Path(__file__).resolve().parent
STORAGE=BASE_DIR/"storage"

# Import configuration only after config.py has loaded the repository .env file.
from config import ACCESS_PASSWORD, DATABASE_PATH, HTTPS, SECRET_KEY

app=Flask(__name__)
app.config["SECRET_KEY"]=SECRET_KEY or secrets.token_hex(32)
app.config["SESSION_COOKIE_HTTPONLY"]=True
app.config["SESSION_COOKIE_SAMESITE"]="Lax"
app.config["SESSION_COOKIE_SECURE"]=HTTPS
app.config["MAX_CONTENT_LENGTH"]=100*1024*1024
app.teardown_appcontext(close_db)

# Idempotent bootstrap so WSGI/Gunicorn deployments do not depend on running app.py as __main__.
if not DATABASE_PATH.exists():
    init_db()
    seed()

PRIVATE_ENDPOINTS = {
    "cases","case_new","case_detail","add_charge","add_assertion","add_question",
    "add_discovery","upload_evidence","defense_workspace","defense_discovery_init",
    "defense_issue_add","motion_add","document_workspace","analyze_evidence","document_run",
    "charge_elements_view","charge_elements_sync","charge_elements_link_evidence",
    "document_draft_select","document_draft_generate"
}

def access_password():
    return ACCESS_PASSWORD

def csrf_token():
    token=session.get("csrf_token")
    if not token:
        token=secrets.token_urlsafe(32)
        session["csrf_token"]=token
    return token

app.jinja_env.globals["csrf_token"] = csrf_token

@app.before_request
def protect_private_workspace():
    if request.endpoint in PRIVATE_ENDPOINTS and access_password() and not session.get("authenticated"):
        return redirect(url_for("login", next=request.full_path if request.query_string else request.path))
    if request.method == "POST" and request.endpoint != "login":
        expected=session.get("csrf_token")
        supplied=request.headers.get("X-CSRF-Token", "") if request.is_json else request.form.get("csrf_token", "")
        if expected and not hmac.compare_digest(expected, supplied):
            abort(400, "Invalid form token")

@app.route("/login", methods=["GET","POST"])
def login():
    if not access_password():
        flash("Private access password is not configured; local-only mode is recommended.", "error")
        return redirect(url_for("home"))
    if request.method == "POST":
        if hmac.compare_digest(request.form.get("password", ""), access_password()):
            session.clear()
            session["authenticated"]=True
            csrf_token()
            target=request.form.get("next") or url_for("cases")
            if not target.startswith("/"):
                target=url_for("cases")
            return redirect(target)
        flash("Incorrect access password.", "error")
    return render_template("login.html", next=request.args.get("next", ""))

@app.post("/logout")
def logout():
    session.clear()
    return redirect(url_for("home"))

@app.get("/assistant")
def assistant():
    return render_template("assistant.html")

@app.post("/api/finessa/chat")
def finessa_chat():
    payload=request.get_json(silent=True) or {}
    message=str(payload.get("message", ""))[:4000]
    raw_case=payload.get("case_id")
    try:
        case_id=int(raw_case) if raw_case not in (None, "") else None
    except (TypeError, ValueError):
        case_id=None
    private_ok=bool(session.get("authenticated")) or not access_password()
    if case_id and not private_ok:
        case_id=None
    gate=compliance_assess(message)
    if gate["decision"]=="BLOCK":
        return {"assistant":"Finessa","mode":"legal-information","answer":"I can help with lawful legal research, evidence preservation, disclosure obligations, and procedural options, but not with concealing, destroying, or fabricating evidence or deceiving a court.","notice":"Legal information only.","compliance":gate,"actions":[],"authorities":[]}
    result=finessa_respond(get_db(), message, case_id=case_id, private_ok=private_ok)
    result["compliance"]=gate
    if gate["decision"]=="REFRAME":
        result["notice"]="This question calls for individualized legal judgment. Finessa can explain relevant law, consequences, and options, but the final legal decision should be reviewed with a licensed attorney in the applicable jurisdiction."
    return result

@app.get("/pricing")
def pricing():
    return render_template("pricing.html",
        case_url=os.environ.get("FINESSA_CASE_PAYMENT_URL", ""),
        plus_url=os.environ.get("FINESSA_PLUS_PAYMENT_URL", ""),
        pro_url=os.environ.get("FINESSA_PRO_PAYMENT_URL", ""), plans=q("SELECT * FROM plan_entitlements ORDER BY monthly_cents"))

@app.get("/legal-disclaimer")
def legal_disclaimer():
    return render_template("legal_disclaimer.html")

@app.get("/privacy")
def privacy():
    return render_template("privacy.html")

def q(sql,args=()):
    return get_db().execute(sql,args).fetchall()

def one(sql,args=()):
    return get_db().execute(sql,args).fetchone()

@app.get("/")
def home():
    return render_template("home.html",
        authority_count=one("SELECT COUNT(*) n FROM legal_authorities")["n"],
        case_count=one("SELECT COUNT(*) n FROM case_workspaces")["n"])

@app.get("/health")
def health():
    db=get_db()
    return {"status":"ok","integrity":db.execute("PRAGMA integrity_check").fetchone()[0]}

@app.get("/api/legal/providers")
def api_legal_providers():
    return {"providers": legal_provider_status()}

@app.get("/api/legal/search")
def api_legal_search():
    query=request.args.get("q", "").strip()
    jurisdiction=request.args.get("jurisdiction", "").strip().upper()
    doc_type=request.args.get("type", "all").strip().lower()
    court=request.args.get("court", "").strip() or None
    raw_case=request.args.get("case_id", "").strip()

    # A private case can supply jurisdiction automatically, but never expose case data
    # to unauthenticated requests merely because a numeric ID was supplied.
    if raw_case and (session.get("authenticated") or not access_password()):
        try:
            row=one("SELECT jurisdiction_code FROM case_workspaces WHERE id=?", (int(raw_case),))
        except ValueError:
            row=None
        if row and not jurisdiction:
            jurisdiction=row["jurisdiction_code"]

    jurisdiction=jurisdiction or "US"
    try:
        limit=int(request.args.get("limit", "10"))
        payload=external_legal_search(get_db(), query, jurisdiction, doc_type, limit, court=court, use_remote=True)
    except (ValueError, TypeError) as exc:
        return {"error": str(exc)}, 400
    return payload

@app.get("/authorities")
def authorities():
    term=request.args.get("q","").strip()
    jur=request.args.get("jurisdiction","").strip()
    sql="SELECT * FROM legal_authorities WHERE 1=1"; args=[]
    if term:
        sql+=" AND (title LIKE ? OR citation LIKE ? OR summary LIKE ?)"
        like=f"%{term}%"; args += [like,like,like]
    if jur:
        sql+=" AND jurisdiction_code=?"; args.append(jur)
    sql+=" ORDER BY jurisdiction_code,title"
    return render_template("authorities.html",authorities=q(sql,args),
                           jurisdictions=q("SELECT * FROM jurisdictions ORDER BY name"),
                           term=term,jur=jur)

@app.get("/research")
def research():
    return render_template("research.html",
        topics=q("SELECT * FROM legal_topics ORDER BY name"),
        authorities=q("SELECT * FROM legal_authorities ORDER BY jurisdiction_code,title"))

@app.get("/verification-workbench")
def verification_workbench():
    rows=q("""SELECT a.*, 
             SUM(CASE WHEN v.result='pass' THEN 1 ELSE 0 END) passed,
             COUNT(v.id) stages
             FROM legal_authorities a
             LEFT JOIN authority_verification_records v ON v.authority_id=a.id
             GROUP BY a.id ORDER BY a.jurisdiction_code,a.title""")
    return render_template("verification.html",authorities=rows)

@app.get("/jurisdictions")
def jurisdictions():
    return render_template("jurisdictions.html",jurisdictions=q("SELECT * FROM jurisdictions ORDER BY kind,name"))

@app.get("/jurisdiction/<code>")
def jurisdiction_detail(code):
    j=one("SELECT * FROM jurisdictions WHERE code=?",(code.upper(),))
    if not j: abort(404)
    return render_template("jurisdiction_detail.html",jurisdiction=j,
                           authorities=q("SELECT * FROM legal_authorities WHERE jurisdiction_code=? ORDER BY title",(j["code"],)))

@app.get("/cases")
def cases():
    return render_template("cases.html",cases=q("SELECT * FROM case_workspaces ORDER BY id DESC"))

@app.route("/cases/new",methods=["GET","POST"])
def case_new():
    if request.method=="POST":
        db=get_db()
        cur=db.execute("""INSERT INTO case_workspaces(case_name,jurisdiction_code,court_name,case_number,
                         proceeding_type,procedural_posture,notes)
                         VALUES(?,?,?,?,?,?,?)""",
            (request.form["case_name"],request.form["jurisdiction_code"],request.form.get("court_name"),
             request.form.get("case_number"),request.form.get("proceeding_type","CRIMINAL"),
             request.form.get("procedural_posture"),request.form.get("notes")))
        db.commit()
        return redirect(url_for("case_detail",case_id=cur.lastrowid))
    return render_template("case_new.html",jurisdictions=q("SELECT * FROM jurisdictions ORDER BY name"))

@app.get("/cases/<int:case_id>")
def case_detail(case_id):
    case=one("SELECT * FROM case_workspaces WHERE id=?",(case_id,))
    if not case: abort(404)
    return render_template("case_detail.html",case=case,
        charges=q("SELECT * FROM case_charges WHERE case_id=? ORDER BY id",(case_id,)),
        evidence=q("SELECT * FROM case_evidence WHERE case_id=? ORDER BY id DESC",(case_id,)),
        assertions=q("SELECT * FROM case_factual_assertions WHERE case_id=? ORDER BY id DESC",(case_id,)),
        questions=q("SELECT * FROM attorney_questions WHERE case_id=? ORDER BY id DESC",(case_id,)),
        discovery=q("SELECT * FROM case_discovery_tracker WHERE case_id=? ORDER BY id DESC",(case_id,)))

@app.post("/cases/<int:case_id>/charges")
def add_charge(case_id):
    db=get_db()
    db.execute("""INSERT INTO case_charges(case_id,statute,charge_name,count_number,notes)
                  VALUES(?,?,?,?,?)""",(case_id,request.form.get("statute"),request.form["charge_name"],
                  request.form.get("count_number") or None,request.form.get("notes")))
    db.commit()
    return redirect(url_for("case_detail",case_id=case_id))

@app.get("/cases/<int:case_id>/charges/<int:charge_id>/elements")
def charge_elements_view(case_id,charge_id):
    case=one("SELECT * FROM case_workspaces WHERE id=?",(case_id,))
    charge=one("SELECT * FROM case_charges WHERE id=? AND case_id=?",(charge_id,case_id))
    if not case or not charge: abort(404)
    return render_template("charge_elements.html",case=case,charge=charge,
                           pv=get_pipeline_view(get_db(),case,charge))

@app.post("/cases/<int:case_id>/charges/<int:charge_id>/elements/sync")
def charge_elements_sync(case_id,charge_id):
    charge=one("SELECT * FROM case_charges WHERE id=? AND case_id=?",(charge_id,case_id))
    if not charge: abort(404)
    key,n=sync_elements_from_library(get_db(),charge)
    if key:
        flash(f"Loaded {n} seed element(s) from the local library ({key}). Verify against current law before relying on them.","success")
    else:
        flash("This statute isn't in the local seed library yet. Add elements manually below, or add a verified entry to services/statute_library.py.","error")
    return redirect(url_for("charge_elements_view",case_id=case_id,charge_id=charge_id))

@app.post("/cases/<int:case_id>/charges/<int:charge_id>/elements/<int:element_id>/link-evidence")
def charge_elements_link_evidence(case_id,charge_id,element_id):
    evidence_id=request.form.get("evidence_id")
    if evidence_id:
        try:
            link_evidence(
                get_db(),
                case_id=case_id,
                charge_id=charge_id,
                element_id=element_id,
                evidence_id=int(evidence_id),
                relationship=request.form.get("relationship", "RELEVANT"),
                assessment=request.form.get("assessment", ""),
            )
        except (TypeError, ValueError):
            abort(400, "Invalid evidence-to-element link")
    return redirect(url_for("charge_elements_view",case_id=case_id,charge_id=charge_id))

@app.get("/cases/<int:case_id>/documents/draft")
def document_draft_select(case_id):
    case=one("SELECT * FROM case_workspaces WHERE id=?",(case_id,))
    if not case: abort(404)
    charges=q("SELECT * FROM case_charges WHERE case_id=?",(case_id,))
    proceeding = "CIVIL" if (case["proceeding_type"] or "").upper()=="CIVIL" else "CRIMINAL"
    types=[{"key":k,**document_catalog.get(k)} for k in document_catalog.list_types(case["jurisdiction_code"],proceeding)]
    return render_template("document_draft.html",case=case,charges=charges,doc_types=types)

@app.post("/cases/<int:case_id>/documents/draft")
def document_draft_generate(case_id):
    case=one("SELECT * FROM case_workspaces WHERE id=?",(case_id,))
    if not case: abort(404)
    doc_type_key=request.form.get("doc_type")
    charge_id=request.form.get("charge_id")
    charge=one("SELECT * FROM case_charges WHERE id=? AND case_id=?",(charge_id,case_id)) if charge_id else None
    entry=document_catalog.get(doc_type_key)
    if not entry: abort(404)
    buf=build_docx(get_db(),case,charge,doc_type_key)
    safe_name=secure_filename(f"{case['case_name']}_{entry['title']}_DRAFT")
    return send_file(buf,as_attachment=True,download_name=f"{safe_name}.docx",
                     mimetype="application/vnd.openxmlformats-officedocument.wordprocessingml.document")

@app.post("/cases/<int:case_id>/assertions")
def add_assertion(case_id):
    db=get_db()
    db.execute("""INSERT INTO case_factual_assertions(case_id,assertion_text,assertion_type,source_note)
                  VALUES(?,?,?,?)""",(case_id,request.form["assertion_text"],
                  request.form.get("assertion_type","USER_REPORTED"),request.form.get("source_note")))
    db.commit()
    return redirect(url_for("case_detail",case_id=case_id))

@app.post("/cases/<int:case_id>/questions")
def add_question(case_id):
    db=get_db()
    db.execute("INSERT INTO attorney_questions(case_id,question_text) VALUES(?,?)",
               (case_id,request.form["question_text"]))
    db.commit()
    return redirect(url_for("case_detail",case_id=case_id))

@app.post("/cases/<int:case_id>/discovery")
def add_discovery(case_id):
    db=get_db()
    db.execute("INSERT INTO case_discovery_tracker(case_id,item_name,notes) VALUES(?,?,?)",
               (case_id,request.form["item_name"],request.form.get("notes")))
    db.commit()
    return redirect(url_for("case_detail",case_id=case_id))

@app.post("/cases/<int:case_id>/evidence")
def upload_evidence(case_id):
    f=request.files.get("file")
    if not f or not f.filename:
        flash("Choose a file","error")
        return redirect(url_for("case_detail",case_id=case_id))
    dest_dir=STORAGE/"cases"/str(case_id)/"evidence"
    dest_dir.mkdir(parents=True,exist_ok=True)
    safe=secure_filename(f.filename) or "evidence.bin"
    dest=dest_dir/safe
    i=1
    while dest.exists():
        dest=dest_dir/f"{dest.stem}_{i}{dest.suffix}"; i+=1
    f.save(dest)
    digest=hashlib.sha256(dest.read_bytes()).hexdigest()
    rel=dest.relative_to(BASE_DIR)
    db=get_db()
    db.execute("""INSERT INTO case_evidence(case_id,evidence_type,original_filename,stored_path,sha256,source_description)
                  VALUES(?,?,?,?,?,?)""",(case_id,request.form.get("evidence_type","OTHER"),f.filename,
                  str(rel),digest,request.form.get("source_description")))
    db.commit()
    return redirect(url_for("case_detail",case_id=case_id))

@app.get("/cases/<int:case_id>/defense")
def defense_workspace(case_id):
    case=one("SELECT * FROM case_workspaces WHERE id=?",(case_id,))
    if not case: abort(404)
    return render_template("defense.html",case=case,
        issues=q("""SELECT cdi.*,dic.issue_name FROM case_defense_issues cdi
                    JOIN defense_issue_catalog dic ON dic.issue_code=cdi.issue_code
                    WHERE cdi.case_id=? ORDER BY cdi.id DESC""",(case_id,)),
        catalog=q("SELECT * FROM defense_issue_catalog ORDER BY issue_name"),
        motions=q("SELECT * FROM case_motion_candidates WHERE case_id=? ORDER BY id DESC",(case_id,)),
        obligations=q("""SELECT cdo.*,do.obligation_name,do.description,do.verification_status seed_status
                         FROM case_discovery_obligations cdo JOIN discovery_obligations do ON do.id=cdo.obligation_id
                         WHERE cdo.case_id=? ORDER BY do.obligation_name""",(case_id,)),
        evidence=q("SELECT * FROM case_evidence WHERE case_id=? ORDER BY id DESC",(case_id,)),
        conflicts=q("SELECT * FROM evidence_conflicts WHERE case_id=? ORDER BY id DESC",(case_id,)))

@app.post("/cases/<int:case_id>/discovery/initialize")
def defense_discovery_init(case_id):
    n=initialize_discovery(get_db(),case_id)
    flash(f"Initialized {n} discovery categories. Structural seeds require legal verification.","success")
    return redirect(url_for("defense_workspace",case_id=case_id))

@app.post("/cases/<int:case_id>/issues/add")
def defense_issue_add(case_id):
    add_defense_issue(get_db(),case_id,request.form["issue_code"],request.form.get("factual_basis",""))
    return redirect(url_for("defense_workspace",case_id=case_id))

@app.post("/cases/<int:case_id>/motions/add")
def motion_add(case_id):
    issue_id=request.form.get("case_defense_issue_id") or None
    add_motion_candidate(get_db(),case_id,request.form["motion_type"],issue_id,request.form.get("requested_relief",""))
    return redirect(url_for("defense_workspace",case_id=case_id))

@app.get("/cases/<int:case_id>/documents/intelligence")
def document_workspace(case_id):
    case=one("SELECT * FROM case_workspaces WHERE id=?",(case_id,))
    if not case: abort(404)
    return render_template("documents.html",case=case,
        evidence=q("""SELECT e.*,
             (SELECT document_class FROM document_analysis_runs r WHERE r.evidence_id=e.id ORDER BY r.id DESC LIMIT 1) latest_class,
             (SELECT id FROM document_analysis_runs r WHERE r.evidence_id=e.id ORDER BY r.id DESC LIMIT 1) latest_run
             FROM case_evidence e WHERE e.case_id=? ORDER BY e.id DESC""",(case_id,)),
        runs=q("SELECT * FROM document_analysis_runs WHERE case_id=? ORDER BY id DESC",(case_id,)))

@app.post("/cases/<int:case_id>/evidence/<int:evidence_id>/analyze")
def analyze_evidence(case_id,evidence_id):
    try:
        rid=analyze_document(get_db(),case_id,evidence_id)
    except Exception as exc:
        flash(str(exc),"error")
        return redirect(url_for("document_workspace",case_id=case_id))
    return redirect(url_for("document_run",case_id=case_id,run_id=rid))

@app.get("/cases/<int:case_id>/documents/intelligence/<int:run_id>")
def document_run(case_id,run_id):
    case=one("SELECT * FROM case_workspaces WHERE id=?",(case_id,))
    run=one("SELECT * FROM document_analysis_runs WHERE id=? AND case_id=?",(run_id,case_id))
    if not case or not run: abort(404)
    return render_template("document_run.html",case=case,run=run,
        findings=q("SELECT * FROM document_findings WHERE analysis_run_id=? ORDER BY page_number,id",(run_id,)),
        gaps=q("SELECT * FROM document_record_gaps WHERE analysis_run_id=? ORDER BY page_number,id",(run_id,)))

@app.get("/terms")
def terms():
    return render_template("terms.html")

@app.get("/eula")
def eula():
    return render_template("eula.html")

@app.get("/api/plans")
def api_plans():
    return {"plans": [dict(r) for r in q("SELECT * FROM plan_entitlements ORDER BY monthly_cents")]}

@app.get("/api/jurisdiction/resolve")
def api_jurisdiction_resolve():
    from services.jurisdiction_resolver import resolve
    raw_case=request.args.get("case_id","").strip()
    try:
        case_id=int(raw_case) if raw_case else None
        return resolve(get_db(), case_id=case_id, jurisdiction_code=request.args.get("jurisdiction"), proceeding_type=request.args.get("proceeding_type"))
    except (ValueError,TypeError) as exc:
        return {"error":str(exc)},400


if __name__=="__main__":
    host=os.environ.get("JG_HOST","127.0.0.1")
    port=int(os.environ.get("PORT","5000"))
    if host not in ("127.0.0.1","localhost") and not access_password():
        raise RuntimeError("Refusing public bind without FINESSA_ACCESS_PASSWORD")
    app.run(host=host,port=port,debug=False)

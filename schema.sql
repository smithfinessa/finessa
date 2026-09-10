PRAGMA foreign_keys=ON;
CREATE TABLE IF NOT EXISTS jurisdictions (
 code TEXT PRIMARY KEY, name TEXT NOT NULL, kind TEXT NOT NULL DEFAULT 'STATE', parent_code TEXT,
 official_source_url TEXT, coverage_status TEXT NOT NULL DEFAULT 'FRAMEWORK'
);
CREATE TABLE IF NOT EXISTS legal_topics (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT UNIQUE NOT NULL);
CREATE TABLE IF NOT EXISTS legal_authorities (
 id INTEGER PRIMARY KEY AUTOINCREMENT, jurisdiction_code TEXT, authority_type TEXT NOT NULL DEFAULT 'case',
 title TEXT NOT NULL, citation TEXT, summary TEXT, proposition_text TEXT, court_name TEXT, source_url TEXT, official_source INTEGER NOT NULL DEFAULT 0,
 precedential_status TEXT, effective_date TEXT, decision_date TEXT, verification_status TEXT NOT NULL DEFAULT 'RESEARCH_LEAD',
 filing_ready INTEGER NOT NULL DEFAULT 0, source_checked_at TEXT,
 FOREIGN KEY(jurisdiction_code) REFERENCES jurisdictions(code)
);
CREATE TABLE IF NOT EXISTS authority_verification_records (
 id INTEGER PRIMARY KEY AUTOINCREMENT, authority_id INTEGER NOT NULL, stage TEXT NOT NULL, result TEXT NOT NULL,
 note TEXT, verified_at TEXT DEFAULT CURRENT_TIMESTAMP, FOREIGN KEY(authority_id) REFERENCES legal_authorities(id) ON DELETE CASCADE
);
CREATE TABLE IF NOT EXISTS case_workspaces (
 id INTEGER PRIMARY KEY AUTOINCREMENT, case_name TEXT NOT NULL, jurisdiction_code TEXT NOT NULL DEFAULT 'US',
 court_name TEXT, case_number TEXT, proceeding_type TEXT NOT NULL DEFAULT 'CRIMINAL', procedural_posture TEXT, notes TEXT,
 created_at TEXT DEFAULT CURRENT_TIMESTAMP, FOREIGN KEY(jurisdiction_code) REFERENCES jurisdictions(code)
);
CREATE TABLE IF NOT EXISTS case_charges (
 id INTEGER PRIMARY KEY AUTOINCREMENT, case_id INTEGER NOT NULL, statute TEXT, charge_name TEXT NOT NULL,
 count_number INTEGER, notes TEXT, FOREIGN KEY(case_id) REFERENCES case_workspaces(id) ON DELETE CASCADE
);
CREATE TABLE IF NOT EXISTS charge_elements (
 id INTEGER PRIMARY KEY AUTOINCREMENT, charge_id INTEGER NOT NULL, element_number INTEGER NOT NULL, element_text TEXT NOT NULL,
 verification_status TEXT NOT NULL DEFAULT 'RESEARCH_LEAD', UNIQUE(charge_id, element_number),
 FOREIGN KEY(charge_id) REFERENCES case_charges(id) ON DELETE CASCADE
);
CREATE TABLE IF NOT EXISTS case_evidence (
 id INTEGER PRIMARY KEY AUTOINCREMENT, case_id INTEGER NOT NULL, evidence_type TEXT NOT NULL DEFAULT 'OTHER',
 original_filename TEXT NOT NULL, stored_path TEXT NOT NULL, sha256 TEXT NOT NULL, source_description TEXT,
 created_at TEXT DEFAULT CURRENT_TIMESTAMP, FOREIGN KEY(case_id) REFERENCES case_workspaces(id) ON DELETE CASCADE
);
CREATE TABLE IF NOT EXISTS element_evidence_links (
 id INTEGER PRIMARY KEY AUTOINCREMENT, element_id INTEGER NOT NULL, evidence_id INTEGER NOT NULL,
 relationship TEXT NOT NULL DEFAULT 'RELEVANT', assessment TEXT,
 FOREIGN KEY(element_id) REFERENCES charge_elements(id) ON DELETE CASCADE,
 FOREIGN KEY(evidence_id) REFERENCES case_evidence(id) ON DELETE CASCADE
);
CREATE TABLE IF NOT EXISTS case_factual_assertions (
 id INTEGER PRIMARY KEY AUTOINCREMENT, case_id INTEGER NOT NULL, assertion_text TEXT NOT NULL,
 assertion_type TEXT NOT NULL DEFAULT 'USER_REPORTED', source_note TEXT, verification_status TEXT NOT NULL DEFAULT 'UNVERIFIED', created_at TEXT DEFAULT CURRENT_TIMESTAMP,
 FOREIGN KEY(case_id) REFERENCES case_workspaces(id) ON DELETE CASCADE
);
CREATE TABLE IF NOT EXISTS attorney_questions (
 id INTEGER PRIMARY KEY AUTOINCREMENT, case_id INTEGER NOT NULL, question_text TEXT NOT NULL, created_at TEXT DEFAULT CURRENT_TIMESTAMP,
 FOREIGN KEY(case_id) REFERENCES case_workspaces(id) ON DELETE CASCADE
);
CREATE TABLE IF NOT EXISTS case_discovery_tracker (
 id INTEGER PRIMARY KEY AUTOINCREMENT, case_id INTEGER NOT NULL, item_name TEXT NOT NULL, notes TEXT, status TEXT DEFAULT 'REQUESTED',
 created_at TEXT DEFAULT CURRENT_TIMESTAMP, FOREIGN KEY(case_id) REFERENCES case_workspaces(id) ON DELETE CASCADE
);
CREATE TABLE IF NOT EXISTS defense_issue_catalog (
 issue_code TEXT PRIMARY KEY, issue_name TEXT NOT NULL, description TEXT, verification_status TEXT NOT NULL DEFAULT 'STRUCTURAL_SEED'
);
CREATE TABLE IF NOT EXISTS case_defense_issues (
 id INTEGER PRIMARY KEY AUTOINCREMENT, case_id INTEGER NOT NULL, issue_code TEXT NOT NULL, factual_basis TEXT,
 factual_support_status TEXT NOT NULL DEFAULT 'UNVERIFIED', authority_status TEXT NOT NULL DEFAULT 'RESEARCH_NEEDED', motion_readiness TEXT NOT NULL DEFAULT 'NOT_READY',
 created_at TEXT DEFAULT CURRENT_TIMESTAMP, FOREIGN KEY(case_id) REFERENCES case_workspaces(id) ON DELETE CASCADE,
 FOREIGN KEY(issue_code) REFERENCES defense_issue_catalog(issue_code)
);
CREATE TABLE IF NOT EXISTS case_motion_candidates (
 id INTEGER PRIMARY KEY AUTOINCREMENT, case_id INTEGER NOT NULL, motion_type TEXT NOT NULL, case_defense_issue_id INTEGER,
 requested_relief TEXT, status TEXT NOT NULL DEFAULT 'RESEARCH_ONLY', created_at TEXT DEFAULT CURRENT_TIMESTAMP,
 FOREIGN KEY(case_id) REFERENCES case_workspaces(id) ON DELETE CASCADE
);
CREATE TABLE IF NOT EXISTS discovery_obligations (
 id INTEGER PRIMARY KEY AUTOINCREMENT, obligation_code TEXT UNIQUE NOT NULL, obligation_name TEXT NOT NULL,
 description TEXT, verification_status TEXT NOT NULL DEFAULT 'STRUCTURAL_SEED'
);
CREATE TABLE IF NOT EXISTS case_discovery_obligations (
 id INTEGER PRIMARY KEY AUTOINCREMENT, case_id INTEGER NOT NULL, obligation_id INTEGER NOT NULL, status TEXT DEFAULT 'UNREVIEWED', notes TEXT,
 UNIQUE(case_id, obligation_id), FOREIGN KEY(case_id) REFERENCES case_workspaces(id) ON DELETE CASCADE,
 FOREIGN KEY(obligation_id) REFERENCES discovery_obligations(id)
);
CREATE TABLE IF NOT EXISTS evidence_conflicts (
 id INTEGER PRIMARY KEY AUTOINCREMENT, case_id INTEGER NOT NULL, description TEXT NOT NULL, source_a TEXT, source_b TEXT,
 created_at TEXT DEFAULT CURRENT_TIMESTAMP, FOREIGN KEY(case_id) REFERENCES case_workspaces(id) ON DELETE CASCADE
);
CREATE TABLE IF NOT EXISTS document_analysis_runs (
 id INTEGER PRIMARY KEY AUTOINCREMENT, case_id INTEGER NOT NULL, evidence_id INTEGER NOT NULL, document_class TEXT,
 extracted_text TEXT, status TEXT NOT NULL DEFAULT 'COMPLETE', created_at TEXT DEFAULT CURRENT_TIMESTAMP,
 FOREIGN KEY(case_id) REFERENCES case_workspaces(id) ON DELETE CASCADE, FOREIGN KEY(evidence_id) REFERENCES case_evidence(id) ON DELETE CASCADE
);
CREATE TABLE IF NOT EXISTS document_findings (
 id INTEGER PRIMARY KEY AUTOINCREMENT, analysis_run_id INTEGER NOT NULL, page_number INTEGER, finding_type TEXT, finding_text TEXT NOT NULL,
 FOREIGN KEY(analysis_run_id) REFERENCES document_analysis_runs(id) ON DELETE CASCADE
);
CREATE TABLE IF NOT EXISTS document_record_gaps (
 id INTEGER PRIMARY KEY AUTOINCREMENT, analysis_run_id INTEGER NOT NULL, page_number INTEGER, gap_type TEXT, gap_text TEXT NOT NULL,
 FOREIGN KEY(analysis_run_id) REFERENCES document_analysis_runs(id) ON DELETE CASCADE
);
CREATE TABLE IF NOT EXISTS plan_entitlements (
 plan_code TEXT PRIMARY KEY, display_name TEXT NOT NULL, monthly_cents INTEGER NOT NULL, annual_cents INTEGER,
 active_cases INTEGER, document_uploads_per_month INTEGER, advanced_research INTEGER NOT NULL DEFAULT 0,
 draft_documents INTEGER NOT NULL DEFAULT 0, professional_tools INTEGER NOT NULL DEFAULT 0
);
CREATE TABLE IF NOT EXISTS compliance_events (
 id INTEGER PRIMARY KEY AUTOINCREMENT, event_type TEXT NOT NULL, jurisdiction_code TEXT, input_excerpt TEXT,
 decision TEXT NOT NULL, reason TEXT, created_at TEXT DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS idx_auth_jur ON legal_authorities(jurisdiction_code);
CREATE INDEX IF NOT EXISTS idx_case_jur ON case_workspaces(jurisdiction_code);

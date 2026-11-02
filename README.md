# Finessa

Finessa is a controlled-access legal-research and case-intelligence platform for jurisdiction-aware legal information, evidence organization, and self-help document workflows. It is not a law firm and is not a substitute for legal advice.

Finessa is designed to help users organize case facts, track discovery, search legal information, and prepare support materials. It does not guarantee legal outcomes or claim complete nationwide authority coverage unless each jurisdiction is independently verified.

The product is intended for self-represented litigants, people working with a public defender or private attorney, and legal professionals who need a structured place to organize facts, review procedural materials, and compare jurisdiction-specific legal sources before acting. It is a research and workflow aid, not a final legal determination or legal recommendation by itself.

## Public launch posture

The project is a controlled-access legal-research product, not a complete legal authority database. Coverage is jurisdiction-specific and must be verified before it is treated as authoritative or used in a filing.

The product should be described as:

- legal research and case organization technology
- evidence and document workflow support
- jurisdiction-aware legal information tooling
- not a substitute for attorney review or legal advice
- not a complete nationwide legal authority database for every state and territory

## Legal-use honesty and compliance posture

Finessa may assist users with:

- locating relevant jurisdictional authorities and official-source links
- organizing case facts, evidence, discovery, and procedural checklists
- reviewing procedural context, court structure, and filing-related workflows
- preparing draft documents and motion outlines that require independent legal review before filing

Finessa does not:

- provide legal advice or legal representation
- determine a user's legal rights, plea strategy, trial position, or outcome
- guarantee the correctness of any jurisdiction-specific rule, deadline, or filing requirement without independent verification
- replace the judgment of a licensed attorney, public defender, or court clerk

Users remain responsible for confirming the current law, local court rules, deadlines, procedural requirements, and factual accuracy for their matter with their own counsel or official sources before taking legal action.

## V1 capabilities

- U.S. jurisdiction registry: federal + 50 states + DC + territories
- Nationwide federated research through public legal-data providers
- Local authority index with explicit verification states
- Reference coverage model for verified jurisdictions; remaining jurisdictions remain framework-only until official-source adapters are validated
- Criminal/civil case workspaces
- Elements & Proof Map
- Evidence-to-element links with integrity checks
- Discovery and issue tracking
- Basic document intelligence and provenance hashing
- Draft DOCX assembly that only uses `filing_ready=1` authorities as citations
- Finessa chat interface with a compliance gateway
- Free / Case / Plus / Professional price entitlements

## Quick start (Linux / Termux)

```bash
git clone https://github.com/smithfinessa/finessa.git
cd finessa
python -m venv .venv
. .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
cp .env.example .env
python scripts/init_db.py
python app.py
```

Open `http://127.0.0.1:5000`.

## Environment

Required for a public/private case workspace:

- `FINESSA_SECRET`
- `FINESSA_ACCESS_PASSWORD`
- `FINESSA_HTTPS=1` when behind HTTPS

Legal-provider keys:

- `COURTLISTENER_API_TOKEN` (optional for some CourtListener access)
- `LEGISCAN_API_KEY`
- `GOVINFO_API_KEY`

Never commit production credentials.

## Coverage honesty

No single public REST API provides every current codified state statute, regulation, court rule, jury instruction, municipal ordinance, and precedential decision for every U.S. jurisdiction. Finessa therefore uses a provider/adaptor model and records coverage status for every jurisdiction.

A jurisdiction is only treated as reference or verified when its primary legal source and verification record have been reviewed. Framework-only jurisdictions remain marked as such and must not be represented as complete or authoritative.

## Production blockers before public launch

1. Counsel review of Terms/EULA/privacy/UPL and marketing claims.
2. Production user authentication and per-user authorization.
3. Payment-provider integration plus webhook-backed subscription state.
4. PostgreSQL migration for production multi-user use.
5. Encryption/retention/audit controls for sensitive case files.
6. Live API-key integration tests and provider license/redistribution review.
7. Official-source adapters and verification for jurisdictions advertised as authoritative.
8. Security review, abuse controls, backups, monitoring, and incident response.

## Tests

```bash
python -m unittest discover -s tests -v
```

Tests requiring Flask/python-docx need dependencies installed. `tests/test_schema.py` uses only the Python standard library.

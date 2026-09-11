# Finessa V1

**Finessa** is the primary product. **Justice Gateway** is the legal-data and authority-verification infrastructure beneath it.

Finessa is designed as legal research, case intelligence, evidence organization, and self-help document technology. It is not a law firm and is not represented as a substitute for licensed counsel.

## V1 capabilities

- U.S. jurisdiction registry: federal + 50 states + DC
- Nationwide federated REST research through CourtListener, LegiScan, and GovInfo
- Local authority index with explicit verification states
- Federal + Michigan reference coverage model; remaining states marked framework until official-source adapters are validated
- Criminal/civil case workspaces
- Elements & Proof Map
- Evidence-to-element links with cross-case integrity validation
- Discovery and issue tracking
- Basic document intelligence and provenance hashing
- Draft DOCX assembly that only uses `filing_ready=1` authorities as citations
- Finessa chat interface with a compliance gateway
- Free / Case / Plus / Professional price entitlements
- Launch-draft Terms, EULA, Privacy, AI disclosure, source register, UPL matrix, and attorney escalation policy

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

For Termux, install Python first:

```bash
pkg update
pkg install python git clang libxml2 libxslt
git clone https://github.com/smithfinessa/finessa.git
cd finessa
bash scripts/termux_setup.sh
```

Then use the commands above. Keep the default `JG_HOST=127.0.0.1` until authentication and HTTPS are correctly configured.

To update an existing Termux installation after a release:

```bash
cd ~/finessa
git pull --ff-only origin main
. .venv/bin/activate
python -m pip install -r requirements.txt
python scripts/init_db.py
python app.py
```

Docker stores SQLite data in `/data`; mount a persistent volume and pass the environment file:

```bash
docker build -t finessa:local .
docker run --rm -p 5000:5000 -v finessa-data:/data --env-file .env finessa:local
```

## Environment

The application accepts new Finessa names while preserving older Justice Gateway secret names for backward compatibility.

Required for a public/private case workspace:

- `FINESSA_SECRET`
- `FINESSA_ACCESS_PASSWORD`
- `FINESSA_HTTPS=1` when behind HTTPS

Legal-provider keys:

- `COURTLISTENER_API_TOKEN` (optional for some CourtListener access)
- `LEGISCAN_API_KEY`
- `GOVINFO_API_KEY`

Never commit production credentials.

## REST

Provider status:

```text
GET /api/legal/providers
```

Jurisdiction resolver:

```text
GET /api/jurisdiction/resolve?jurisdiction=MI&proceeding_type=CRIMINAL
GET /api/jurisdiction/resolve?case_id=1
```

Legal research:

```text
GET /api/legal/search?q=search+warrant&jurisdiction=MI&type=case
GET /api/legal/search?q=criminal+procedure&jurisdiction=MI&type=legislation
GET /api/legal/search?q=privacy&jurisdiction=US&type=law
GET /api/legal/search?q=search+warrant&type=case&case_id=1
```

Plans:

```text
GET /api/plans
```

## Authority lifecycle

Remote results are research leads. A source is not filing-ready merely because an API returned it.

```text
RESEARCH_LEAD
  -> SOURCE_VERIFIED
  -> CURRENCY_VERIFIED
  -> JURISDICTION_VERIFIED
  -> CITATION_VERIFIED
  -> FILING_READY
```

`services/authority_verification.py` implements the local verification gate. The document generator selects only `filing_ready=1` authorities.

## Coverage honesty

No single public REST API provides every current codified state statute, regulation, court rule, jury instruction, municipal ordinance, and precedential decision for every U.S. jurisdiction. Finessa therefore uses a provider/adaptor architecture and records coverage status. The product must not market framework jurisdictions as complete authoritative coverage.

Federal and Michigan are reference jurisdictions for the deeper adapter work. Other states can be added without changing the public API.

## Pricing model

- Finessa Access — $0
- Finessa Case — $9.99/month; $99/year target
- Finessa Plus — $19.99/month; $199/year target
- Finessa Professional — $49/user/month target
- Attorney review — separate licensed-attorney service, if implemented

The repository contains entitlements, not a hard-coded payment processor. Checkout URLs are configured by environment variables so Stripe or another provider can be connected without storing payment credentials in source code.

## Production blockers before taking paying customers

1. Counsel review of Terms/EULA/privacy/UPL and marketing claims.
2. Production user authentication and per-user authorization (the V1 private password is suitable for controlled testing, not a multi-tenant commercial service).
3. Payment-provider integration plus webhook-backed subscription state.
4. PostgreSQL migration for production multi-user use.
5. Encryption/retention/audit controls for sensitive case files.
6. Live API-key integration tests and provider licence/redistribution review.
7. Official-source adapters and coverage verification for jurisdictions advertised as authoritative.
8. Security review, abuse controls, backups, monitoring, and incident response.

## Tests

```bash
python -m unittest discover -s tests -v
```

Tests requiring Flask/python-docx need dependencies installed. `tests/test_schema.py` uses only the Python standard library.

# Finessa

Finessa is a controlled-access legal research and case-workflow prototype built to help organize legal facts, research material, evidence, document drafting, and discovery work in a single local system.

This project is not a law firm, not a substitute for legal advice, and not a complete nationwide legal authority database. It is also not a public-facing product without additional legal review, production security hardening, and deployment validation.

## Product truth

Finessa is best described as:

- a legal research and case organization tool
- a workspace for evidence, issues, charges, and discovery tracking
- a document drafting and case-prep aid for attorneys, litigants, and researchers
- a framework for jurisdiction-aware legal information, with explicit verification states
- a local-first prototype that is intentionally conservative about claims and legal authority

It is not:

- a complete legal database for every jurisdiction
- a substitute for attorney review or legal judgment
- a public legal advice product that can safely operate without review and configuration controls
- a production-ready service without operational, legal, and security validation

## What is inside this repository

The repository contains a Python/Flask application with a SQLite-backed local database and a number of legal workflow features, including:

- jurisdiction-aware authority indexing
- legal topic and authority search
- case workspace management for charges, evidence, and assertions
- discovery and defense issue tracking
- document analysis and drafting support
- compliance-aware assistant interactions
- local document generation for case-ready outputs

## Current status

This repository is currently a controlled-access prototype and framework for review, not a fully launched public legal platform. The README and app configuration intentionally reflect a cautious release posture.

Production use should only happen after:

- legal/compliance review of privacy, terms, and claims
- secure deployment configuration is in place
- secrets are explicitly set for the target environment
- database, storage, and authentication controls are validated
- external data providers are reviewed for quality and licensing

## Repository layout

- `app.py` — Flask application entry point and routes
- `config.py` — runtime configuration and production validation
- `db.py` and `schema.sql` — database bootstrap and schema
- `services/` — legal research, document, and workflow logic
- `providers/` — official source adapter boundary and integration notes
- `templates/` and `static/` — UI assets
- `tests/` — application and validation tests
- `docs/` — deployment and policy materials

## Quick start

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

Then open:

- http://127.0.0.1:5000

## Required environment variables

Minimum local configuration:

- `FINESSA_SECRET` for signing and session security
- `FINESSA_ACCESS_PASSWORD` for private workspace access
- `FINESSA_HTTPS=1` when behind HTTPS
- `DATABASE_PATH` for the local SQLite database

Example values are in `.env.example`.

Production mode should be declared explicitly:

```bash
export FINESSA_ENV=production
export FINESSA_SECRET="<strong-random-secret>"
export FINESSA_ACCESS_PASSWORD="<strong-password>"
export FINESSA_HTTPS=1
```

The application now fails fast in production when placeholders or empty values remain in place.

## Production deployment checklist

For deployment steps and hardening guidance, see:

- `docs/DEPLOYMENT_CHECKLIST.md`

## Testing

```bash
python -m unittest discover -s tests -v
```

## Legal and coverage honesty

No single public API provides a complete, current, fully verified legal authority corpus for every jurisdiction. This codebase recognizes that reality and explicitly treats authority coverage as jurisdiction-specific and verification-driven.

The project is built around careful source tracking, evidence handling, and workflow structure rather than claiming universal legal completeness.

## License and support

This repository is provided as a prototype and operational framework. It is not a replacement for legal advice, regulatory review, or production legal technology operations.

Always validate the output against current law, applicable rules, and your actual jurisdiction before relying on it for legal decisions or filings.

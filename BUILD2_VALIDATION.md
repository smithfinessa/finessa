# Finessa Launch Build 2 — Validation Baseline

This patch begins Launch Build 2 without placing real client/case material in the public repository.

## What changed

- Replaces the minimal V1 homepage with a product-oriented Finessa dashboard.
- Aligns the base navigation with the working application: Finessa, My Case, Research, Verification, Jurisdictions, Pricing.
- Adds two sanitized synthetic fixtures inspired by complex Michigan post-conviction and active Colorado misdemeanor workflows.
- Establishes explicit acceptance expectations for fact classification, evidence conflicts, discovery gaps, authority verification, and attorney-review outputs.

## Privacy rule

Never commit real discovery, emails, voice samples, credentials, database files, private uploads, personal identifiers, or case exhibits to the public repository. Sanitized fixtures are structural tests only.

## Build 2 acceptance principle

Finessa must distinguish:

1. DOCUMENTED_RECORD
2. PROSECUTION_ASSERTION
3. DEFENSE_ASSERTION
4. DISPUTED
5. INFERENCE
6. MISSING_EVIDENCE
7. GOVERNING_LAW

Neither a police report nor a defense statement becomes an established fact merely because it appears in the workspace.

## Test command

```bash
python -m pytest -q
```

## Development branch

Apply this patch only to `develop/finessa-launch-build-2` until it passes review and testing.

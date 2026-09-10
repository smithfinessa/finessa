# Justice Gateway Patch — Merge Review

## Status

This package is a merge-ready overlay derived from the uploaded `justice_gateway_patch.zip`.
Python syntax compilation passes for `app.py` and every file in `services/`.

## GitHub comparison limitation

The connected GitHub account exposed zero repository installations during this review, and both previously known repository names returned 404 through the GitHub connector. Therefore a true three-way diff against the current remote branch could not be completed or committed remotely in this session.

Do **not** overwrite the repository's `app.py`, `services/finessa.py`, templates, CSS, or JavaScript until they are diffed against the current branch. New files are lower-risk; replacement files may contain prior project changes not represented in this overlay.

## Patch capabilities retained

- Elements & Proof Map
- Statute seed library
- Case-aware Finessa statute branch
- Evidence-to-element mapping
- Document drafting scaffold
- Filing-ready-authority-only citation insertion
- Draft warnings and pre-filing checklist
- UI/template updates

## Hardening applied during this review

The uploaded version allowed an arbitrary `element_id` and `evidence_id` to be linked without verifying that both belonged to the requested case/charge. That could create cross-case data contamination if IDs were manipulated. The merge-ready version now:

1. verifies the element belongs to the specified charge;
2. verifies the charge belongs to the specified case;
3. verifies the evidence belongs to the same case; and
4. restricts relationship values to `RELEVANT`, `SUPPORTS`, `UNDERMINES`, or `AMBIGUOUS`.

Invalid links now return HTTP 400 instead of being committed.

## Items requiring remote-base verification before production merge

- Confirm `schema.sql` contains every column/table assumed by `case_pipeline.py` and `document_assembly.py`, especially `charge_elements.verification_status`, `element_evidence_links.assessment`, `legal_authorities.filing_ready`, and defense-intelligence fields.
- Diff all replacement files against the current branch before applying them.
- Run the repository's existing tests plus Flask route tests after the remote merge.
- Confirm `python-docx` is already represented in the dependency manifest rather than relying only on an ad-hoc `pip install` command.
- Treat statute-library entries as seed/reference material only until each is verified against current official statutory text and the applicable current jury instruction.
- Expand Michigan charge mapping by exact statute subsection and M Crim JI rather than generic offense-level matching before presenting the engine as charge-complete.

## Recommended remote merge method

Create a dedicated branch such as `merge/elements-proof-document-drafting`, compare each overlay path to the default branch, merge non-conflicting new files first, manually reconcile replacement files, run tests, then open a pull request. Avoid direct overwrite of the default branch.

# Provider adapters

Finessa uses a federated model. `services/external_legal_data.py` currently implements CourtListener, LegiScan, and GovInfo. This directory is the stable adapter boundary for official state sources. Federal and Michigan are the reference jurisdictions; remaining states should implement the same categories without changing the user-facing API.

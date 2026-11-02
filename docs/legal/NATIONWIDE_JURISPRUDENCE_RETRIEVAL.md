# Nationwide jurisprudence retrieval

Finessa can perform national opinion searches against the case-law collection exposed by CourtListener. State, territory, and District of Columbia searches are scoped using explicit CourtListener court IDs; Finessa does not infer a court from a state-name keyword because that can return misleading results.

## Configure jurisdiction scope

Set `COURTLISTENER_API_TOKEN` to a provider token for authenticated access and higher provider rate limits. It is optional for requests allowed by CourtListener without authentication.

For state/territory-specific search, set `FINESSA_COURTLISTENER_COURTS_JSON` to a JSON object mapping jurisdiction codes to the CourtListener court IDs intended for that jurisdiction. For example:

```sh
export FINESSA_COURTLISTENER_COURTS_JSON='{"CA":["cal","calctapp"],"MI":["mich"]}'
```

Populate this mapping from the current CourtListener courts directory (`https://www.courtlistener.com/api/rest/v4/courts/`) and review it for the intended scope. Do not copy the example as a comprehensive mapping: it is illustrative only. Include only IDs confirmed in the provider directory. `US` means a national search without a court restriction; it does not certify complete nationwide coverage.

## Termux / Linux usage

From the repository root:

```sh
python scripts/search_jurisprudence.py --jurisdiction US --query 'search and seizure' --limit 50
python scripts/search_jurisprudence.py --jurisdiction MI --query 'motion to suppress' --date-filed-min 2020-01-01
```

State-specific searches fail closed if the court-ID mapping is missing. Search results are research leads. The CLI reports indexed opinions; it does not establish that the collection is exhaustive, that law remains current, or that a result is controlling. Verify citations, court, subsequent history, precedential status, and current law using official sources and qualified legal review before reliance.

## Operational notes

- Cursor pagination is followed only on the CourtListener HTTPS host and is bounded with `--max-pages-per-court`.
- `--limit` caps the number of results returned; `more_available` indicates that the configured page bound or result cap prevented full traversal.
- The adapter does not mark results filing-ready and does not provide legal advice.
- Respect provider terms, rate limits, and redistribution restrictions. The application has not been independently validated for complete, continuous, all-court nationwide retrieval.

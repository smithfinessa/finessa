"""Jurisdiction-scoped opinion retrieval from the CourtListener search API.

This adapter deliberately requires explicit CourtListener court IDs for
non-federal jurisdiction filtering. It never silently substitutes a state-name
keyword for a court filter, which can create misleading jurisdiction matches.
"""
from __future__ import annotations

import json
import os
import urllib.error
import urllib.parse
import urllib.request
from typing import Any

API_ROOT = "https://www.courtlistener.com/api/rest/v4"
COURT_IDS_ENV = "FINESSA_COURTLISTENER_COURTS_JSON"


class JurisprudenceProviderError(RuntimeError):
    """The provider could not return a usable opinion-search response."""


def configured_courts(jurisdiction: str) -> list[str]:
    """Get a reviewed set of CourtListener court IDs for a jurisdiction.

    The JSON environment variable maps jurisdiction codes to arrays of CourtListener
    court IDs, for example: {"CA": ["cal", "calctapp"]}. Codes and IDs are
    normalized, and malformed or empty mappings fail closed.
    """
    code = (jurisdiction or "US").strip().upper()
    raw = os.environ.get(COURT_IDS_ENV, "").strip()
    if not raw:
        raise JurisprudenceProviderError(
            f"{COURT_IDS_ENV} must map {code} to reviewed CourtListener court IDs"
        )
    try:
        mapping = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise JurisprudenceProviderError(f"{COURT_IDS_ENV} is not valid JSON") from exc
    if not isinstance(mapping, dict):
        raise JurisprudenceProviderError(f"{COURT_IDS_ENV} must be a JSON object")
    value = mapping.get(code)
    if not isinstance(value, list) or not value:
        raise JurisprudenceProviderError(
            f"No CourtListener court IDs are configured for {code}"
        )
    courts = list(dict.fromkeys(str(item).strip().lower() for item in value if str(item).strip()))
    if not courts:
        raise JurisprudenceProviderError(f"No usable CourtListener court IDs are configured for {code}")
    return courts


def _get_json(url: str, *, timeout: int = 20) -> dict[str, Any]:
    headers = {"Accept": "application/json", "User-Agent": "Finessa/1.0 legal-research"}
    token = os.environ.get("COURTLISTENER_API_TOKEN", "").strip()
    if token:
        headers["Authorization"] = f"Token {token}"
    request = urllib.request.Request(url, headers=headers)
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            payload = json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        raise JurisprudenceProviderError(f"CourtListener returned HTTP {exc.code}") from exc
    except (urllib.error.URLError, TimeoutError, json.JSONDecodeError) as exc:
        raise JurisprudenceProviderError(f"CourtListener request failed: {exc}") from exc
    if not isinstance(payload, dict):
        raise JurisprudenceProviderError("CourtListener returned an unexpected response")
    return payload


def _search_url(query: str, *, court: str | None, date_filed_min: str | None,
                date_filed_max: str | None) -> str:
    params: dict[str, str] = {
        "q": query,
        "type": "o",
        "order_by": "score desc",
    }
    if court:
        params["court"] = court
    if date_filed_min:
        params["date_filed_min"] = date_filed_min
    if date_filed_max:
        params["date_filed_max"] = date_filed_max
    return f"{API_ROOT}/search/?{urllib.parse.urlencode(params)}"


def _safe_next_url(value: str | None) -> str | None:
    """Only follow provider pagination URLs on the expected HTTPS host."""
    if not value:
        return None
    parsed = urllib.parse.urlparse(value)
    if parsed.scheme != "https" or parsed.hostname != "www.courtlistener.com":
        raise JurisprudenceProviderError("CourtListener returned an unexpected pagination URL")
    return value


def search_opinions(query: str, *, jurisdiction: str = "US", limit: int = 50,
                    max_pages_per_court: int = 3, date_filed_min: str | None = None,
                    date_filed_max: str | None = None) -> dict[str, Any]:
    """Retrieve opinion search results nationally or from configured court IDs.

    `US` searches the provider's available opinion index nationally. Other
    jurisdiction codes require an explicit court-ID mapping. Pagination is
    cursor-based and bounded to avoid unintentional unbounded API usage.
    Results remain research leads and are not a completeness or validity claim.
    """
    query = (query or "").strip()
    code = (jurisdiction or "US").strip().upper()
    if not query:
        raise ValueError("query must not be empty")
    if not 1 <= int(limit) <= 500:
        raise ValueError("limit must be between 1 and 500")
    if not 1 <= int(max_pages_per_court) <= 20:
        raise ValueError("max_pages_per_court must be between 1 and 20")
    if date_filed_min and date_filed_max and date_filed_min > date_filed_max:
        raise ValueError("date_filed_min must be on or before date_filed_max")

    courts: list[str | None] = [None] if code == "US" else configured_courts(code)
    results: list[dict[str, Any]] = []
    seen: set[str] = set()
    pages_fetched = 0
    more_available = False

    for court in courts:
        url: str | None = _search_url(
            query, court=court, date_filed_min=date_filed_min,
            date_filed_max=date_filed_max,
        )
        page_count = 0
        while url and page_count < max_pages_per_court and len(results) < limit:
            payload = _get_json(url)
            pages_fetched += 1
            page_count += 1
            items = payload.get("results") or []
            if not isinstance(items, list):
                raise JurisprudenceProviderError("CourtListener returned malformed search results")
            for item in items:
                if not isinstance(item, dict):
                    continue
                external_id = str(item.get("cluster_id") or item.get("id") or item.get("absolute_url") or "")
                if not external_id or external_id in seen:
                    continue
                seen.add(external_id)
                absolute = item.get("absolute_url")
                source_url = urllib.parse.urljoin("https://www.courtlistener.com", absolute) if absolute else None
                results.append({
                    "provider": "courtlistener",
                    "jurisdiction_code": code,
                    "court_id": str(item.get("court") or court or ""),
                    "external_id": external_id,
                    "title": str(item.get("caseName") or item.get("case_name") or item.get("caseNameFull") or "Untitled opinion"),
                    "citation": item.get("citation") or item.get("citations"),
                    "source_url": source_url,
                    "published_date": item.get("dateFiled") or item.get("date_filed"),
                    "source_status": "RESEARCH_LEAD",
                })
                if len(results) >= limit:
                    break
            next_url = _safe_next_url(payload.get("next"))
            if next_url and page_count >= max_pages_per_court:
                more_available = True
            url = next_url if page_count < max_pages_per_court and len(results) < limit else None
        if len(results) >= limit:
            more_available = more_available or court != courts[-1]
            break

    return {
        "query": query,
        "jurisdiction": code,
        "results": results,
        "pages_fetched": pages_fetched,
        "more_available": more_available,
        "coverage_note": (
            "Results are limited to opinions indexed by CourtListener and the courts selected by the request. "
            "They are research leads, not a complete official reporter, current-validity check, or legal advice. "
            "Verify the opinion, citation, subsequent history, precedential status, and governing court rules against authoritative sources."
        ),
    }

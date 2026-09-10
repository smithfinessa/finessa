"""Federated REST legal-data search for Justice Gateway.

Providers:
- CourtListener: U.S. case-law search.
- LegiScan: state + federal current legislation.
- GovInfo: federal U.S. Code, CFR, public laws, bills and related primary documents.

This module intentionally does NOT mark remote material as filing-ready. Remote
results are cached as RESEARCH_LEAD records until Justice Gateway's authority
verification workflow confirms citation, court, current validity and proposition.
"""
from __future__ import annotations

import json
import os
import time
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass, asdict
from typing import Any

STATE_NAMES = {
    "AL":"Alabama","AK":"Alaska","AZ":"Arizona","AR":"Arkansas","CA":"California","CO":"Colorado",
    "CT":"Connecticut","DE":"Delaware","DC":"District of Columbia","FL":"Florida","GA":"Georgia","HI":"Hawaii",
    "ID":"Idaho","IL":"Illinois","IN":"Indiana","IA":"Iowa","KS":"Kansas","KY":"Kentucky","LA":"Louisiana",
    "ME":"Maine","MD":"Maryland","MA":"Massachusetts","MI":"Michigan","MN":"Minnesota","MS":"Mississippi",
    "MO":"Missouri","MT":"Montana","NE":"Nebraska","NV":"Nevada","NH":"New Hampshire","NJ":"New Jersey",
    "NM":"New Mexico","NY":"New York","NC":"North Carolina","ND":"North Dakota","OH":"Ohio","OK":"Oklahoma",
    "OR":"Oregon","PA":"Pennsylvania","RI":"Rhode Island","SC":"South Carolina","SD":"South Dakota","TN":"Tennessee",
    "TX":"Texas","UT":"Utah","VT":"Vermont","VA":"Virginia","WA":"Washington","WV":"West Virginia",
    "WI":"Wisconsin","WY":"Wyoming","US":"Federal"
}

ALLOWED_TYPES = {"all", "case", "legislation", "law", "regulation"}


@dataclass
class LegalResult:
    provider: str
    jurisdiction_code: str
    doc_type: str
    external_id: str
    title: str
    citation: str | None = None
    summary: str | None = None
    source_url: str | None = None
    published_date: str | None = None
    updated_at: str | None = None
    source_status: str = "RESEARCH_LEAD"

    def public(self) -> dict[str, Any]:
        return asdict(self)


class ProviderError(RuntimeError):
    pass


def _json_request(url: str, *, headers: dict[str, str] | None = None,
                  method: str = "GET", body: dict | None = None,
                  timeout: int = 12) -> dict:
    data = None
    hdrs = {"Accept": "application/json", "User-Agent": "JusticeGateway/1.0"}
    if headers:
        hdrs.update(headers)
    if body is not None:
        data = json.dumps(body).encode("utf-8")
        hdrs["Content-Type"] = "application/json"
    req = urllib.request.Request(url, data=data, headers=hdrs, method=method)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        detail = exc.read(1000).decode("utf-8", "replace")
        raise ProviderError(f"HTTP {exc.code} from provider: {detail}") from exc
    except (urllib.error.URLError, TimeoutError, json.JSONDecodeError) as exc:
        raise ProviderError(str(exc)) from exc


def ensure_schema(db) -> None:
    db.execute("""
        CREATE TABLE IF NOT EXISTS external_legal_documents (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            provider TEXT NOT NULL,
            jurisdiction_code TEXT NOT NULL,
            doc_type TEXT NOT NULL,
            external_id TEXT NOT NULL,
            citation TEXT,
            title TEXT NOT NULL,
            summary TEXT,
            source_url TEXT,
            published_date TEXT,
            source_updated_at TEXT,
            verification_status TEXT NOT NULL DEFAULT 'RESEARCH_LEAD',
            fetched_at INTEGER NOT NULL,
            raw_json TEXT,
            UNIQUE(provider, external_id)
        )
    """)
    db.execute("CREATE INDEX IF NOT EXISTS idx_external_legal_jur_type ON external_legal_documents(jurisdiction_code, doc_type)")
    db.execute("CREATE INDEX IF NOT EXISTS idx_external_legal_title ON external_legal_documents(title)")
    db.commit()


def _cache(db, result: LegalResult, raw: dict | None = None) -> None:
    ensure_schema(db)
    db.execute("""
        INSERT INTO external_legal_documents(
            provider,jurisdiction_code,doc_type,external_id,citation,title,summary,
            source_url,published_date,source_updated_at,verification_status,fetched_at,raw_json
        ) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?)
        ON CONFLICT(provider,external_id) DO UPDATE SET
            jurisdiction_code=excluded.jurisdiction_code,
            doc_type=excluded.doc_type,
            citation=excluded.citation,
            title=excluded.title,
            summary=excluded.summary,
            source_url=excluded.source_url,
            published_date=excluded.published_date,
            source_updated_at=excluded.source_updated_at,
            fetched_at=excluded.fetched_at,
            raw_json=excluded.raw_json
    """, (
        result.provider, result.jurisdiction_code, result.doc_type, result.external_id,
        result.citation, result.title, result.summary, result.source_url,
        result.published_date, result.updated_at, result.source_status, int(time.time()),
        json.dumps(raw, separators=(",", ":"), ensure_ascii=False) if raw else None,
    ))
    db.commit()


def courtlistener_search(query: str, jurisdiction: str, limit: int = 10,
                         court: str | None = None) -> list[tuple[LegalResult, dict]]:
    params: dict[str, str | int] = {"q": query, "type": "o", "order_by": "score desc"}
    if court:
        params["court"] = court
    elif jurisdiction in STATE_NAMES and jurisdiction != "US":
        # CourtListener's search API is court-centric rather than state-code-centric.
        # Adding the full state name improves state relevance while preserving broad coverage.
        params["q"] = f'{query} "{STATE_NAMES[jurisdiction]}"'
    url = "https://www.courtlistener.com/api/rest/v4/search/?" + urllib.parse.urlencode(params)
    headers = {}
    token = os.environ.get("COURTLISTENER_API_TOKEN", "").strip()
    if token:
        headers["Authorization"] = f"Token {token}"
    payload = _json_request(url, headers=headers)
    out: list[tuple[LegalResult, dict]] = []
    for item in (payload.get("results") or [])[:limit]:
        cluster_id = str(item.get("cluster_id") or item.get("id") or item.get("absolute_url") or "")
        absolute = item.get("absolute_url")
        source_url = urllib.parse.urljoin("https://www.courtlistener.com", absolute) if absolute else None
        citation = None
        cites = item.get("citation") or item.get("citations")
        if isinstance(cites, list):
            citation = "; ".join(str(x) for x in cites[:3])
        elif cites:
            citation = str(cites)
        title = item.get("caseName") or item.get("case_name") or item.get("caseNameFull") or "Untitled opinion"
        summary = item.get("snippet") or item.get("status")
        result = LegalResult(
            provider="courtlistener", jurisdiction_code=jurisdiction, doc_type="case",
            external_id=cluster_id, title=str(title), citation=citation,
            summary=str(summary)[:2000] if summary else None, source_url=source_url,
            published_date=item.get("dateFiled") or item.get("date_filed"),
            updated_at=item.get("dateModified") or item.get("date_modified"),
        )
        out.append((result, item))
    return out


def legiscan_search(query: str, jurisdiction: str, limit: int = 10) -> list[tuple[LegalResult, dict]]:
    key = os.environ.get("LEGISCAN_API_KEY", "").strip()
    if not key:
        raise ProviderError("LEGISCAN_API_KEY is not configured")
    state = "US" if jurisdiction == "US" else jurisdiction
    params = {"op": "search", "state": state, "query": query, "key": key}
    payload = _json_request("https://api.legiscan.com/?" + urllib.parse.urlencode(params))
    searchresult = payload.get("searchresult") or {}
    rows = []
    if isinstance(searchresult, dict):
        rows = [v for k, v in searchresult.items() if str(k).isdigit() and isinstance(v, dict)]
    out: list[tuple[LegalResult, dict]] = []
    for item in rows[:limit]:
        bill_id = str(item.get("bill_id") or item.get("bill_number") or "")
        title = item.get("title") or item.get("description") or item.get("bill_number") or "Untitled bill"
        source_url = item.get("url") or item.get("state_link")
        result = LegalResult(
            provider="legiscan", jurisdiction_code=jurisdiction, doc_type="legislation",
            external_id=bill_id, title=str(title), citation=item.get("bill_number"),
            summary=item.get("description"), source_url=source_url,
            published_date=item.get("last_action_date") or item.get("status_date"),
            updated_at=item.get("last_action_date"),
        )
        out.append((result, item))
    return out


def govinfo_search(query: str, doc_type: str = "law", limit: int = 10) -> list[tuple[LegalResult, dict]]:
    key = os.environ.get("GOVINFO_API_KEY", "").strip()
    if not key:
        raise ProviderError("GOVINFO_API_KEY is not configured")
    collection = {
        "law": "(USCODE OR PLAW)",
        "regulation": "(CFR OR FR)",
        "legislation": "(BILLS OR BILLSTATUS)",
    }.get(doc_type)
    q = query if not collection else f"({query}) collection:{collection}"
    body = {
        "query": q,
        "pageSize": str(min(max(limit, 1), 100)),
        "offsetMark": "*",
        "sorts": [{"field": "score", "sortOrder": "DESC"}],
        "historical": True,
    }
    url = "https://api.govinfo.gov/search?" + urllib.parse.urlencode({"api_key": key})
    payload = _json_request(url, method="POST", body=body)
    out: list[tuple[LegalResult, dict]] = []
    for item in (payload.get("results") or [])[:limit]:
        ext = str(item.get("granuleId") or item.get("packageId") or item.get("resultLink") or "")
        download = item.get("download") or {}
        source_url = download.get("htmlLink") or download.get("pdfLink") or item.get("resultLink")
        collection_code = str(item.get("collectionCode") or "")
        inferred = "regulation" if collection_code in {"CFR", "FR"} else ("legislation" if collection_code in {"BILLS", "BILLSTATUS"} else "law")
        result = LegalResult(
            provider="govinfo", jurisdiction_code="US", doc_type=inferred,
            external_id=ext, title=str(item.get("title") or ext), citation=None,
            summary=None, source_url=source_url,
            published_date=item.get("dateIssued"), updated_at=item.get("lastModified"),
        )
        out.append((result, item))
    return out


def local_cache_search(db, query: str, jurisdiction: str, doc_type: str, limit: int = 20) -> list[dict]:
    ensure_schema(db)
    sql = "SELECT * FROM external_legal_documents WHERE jurisdiction_code=?"
    args: list[Any] = [jurisdiction]
    if doc_type != "all":
        sql += " AND doc_type=?"
        args.append(doc_type)
    if query:
        sql += " AND (title LIKE ? OR citation LIKE ? OR summary LIKE ?)"
        like = f"%{query}%"
        args += [like, like, like]
    sql += " ORDER BY fetched_at DESC LIMIT ?"
    args.append(limit)
    return [dict(r) for r in db.execute(sql, tuple(args)).fetchall()]


def search(db, query: str, jurisdiction: str, doc_type: str = "all", limit: int = 10,
           court: str | None = None, use_remote: bool = True) -> dict[str, Any]:
    jurisdiction = (jurisdiction or "US").upper().strip()
    if jurisdiction not in STATE_NAMES:
        raise ValueError("jurisdiction must be US, DC, or a two-letter U.S. state code")
    doc_type = (doc_type or "all").lower().strip()
    if doc_type not in ALLOWED_TYPES:
        raise ValueError(f"type must be one of {sorted(ALLOWED_TYPES)}")
    query = (query or "").strip()[:500]
    limit = min(max(int(limit), 1), 25)

    results: list[LegalResult] = []
    errors: list[dict[str, str]] = []

    if use_remote and query:
        providers = []
        if doc_type in {"all", "case"}:
            providers.append(("courtlistener", lambda: courtlistener_search(query, jurisdiction, limit, court=court)))
        if doc_type in {"all", "legislation"}:
            providers.append(("legiscan", lambda: legiscan_search(query, jurisdiction, limit)))
            if jurisdiction == "US":
                providers.append(("govinfo", lambda: govinfo_search(query, "legislation", limit)))
        if jurisdiction == "US" and doc_type in {"all", "law", "regulation"}:
            if doc_type in {"all", "law"}:
                providers.append(("govinfo-law", lambda: govinfo_search(query, "law", limit)))
            if doc_type in {"all", "regulation"}:
                providers.append(("govinfo-regulation", lambda: govinfo_search(query, "regulation", limit)))

        seen: set[tuple[str, str]] = set()
        for name, fn in providers:
            try:
                for result, raw in fn():
                    key = (result.provider, result.external_id)
                    if key in seen:
                        continue
                    seen.add(key)
                    _cache(db, result, raw)
                    results.append(result)
            except ProviderError as exc:
                errors.append({"provider": name, "error": str(exc)})

    cached = local_cache_search(db, query, jurisdiction, doc_type, limit=limit)
    if not results:
        # Cache fallback means the research page remains useful during provider outages.
        results = [LegalResult(
            provider=r["provider"], jurisdiction_code=r["jurisdiction_code"], doc_type=r["doc_type"],
            external_id=r["external_id"], title=r["title"], citation=r["citation"], summary=r["summary"],
            source_url=r["source_url"], published_date=r["published_date"], updated_at=r["source_updated_at"],
            source_status=r["verification_status"],
        ) for r in cached]

    return {
        "query": query,
        "jurisdiction": jurisdiction,
        "type": doc_type,
        "results": [r.public() for r in results[:limit]],
        "errors": errors,
        "coverage_note": (
            "Case law uses CourtListener; current legislation uses LegiScan; federal code/regulation/public-law documents use GovInfo. "
            "No single public REST API provides complete codified statutes and local ordinances for every U.S. jurisdiction. "
            "All remote results are research leads until independently verified."
        ),
    }


def provider_status() -> list[dict[str, Any]]:
    return [
        {"provider": "courtlistener", "covers": "U.S. case law", "configured": bool(os.environ.get("COURTLISTENER_API_TOKEN")), "key_optional": True},
        {"provider": "legiscan", "covers": "Current legislation: 50 states + Congress", "configured": bool(os.environ.get("LEGISCAN_API_KEY")), "key_optional": False},
        {"provider": "govinfo", "covers": "Federal USC/CFR/public laws/bills and federal documents", "configured": bool(os.environ.get("GOVINFO_API_KEY")), "key_optional": False},
    ]

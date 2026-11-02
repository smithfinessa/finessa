"""CLI for CourtListener nationwide or configured-court opinion retrieval.

Example (Termux/Linux):
  python scripts/search_jurisprudence.py --jurisdiction US --query 'search and seizure'
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from services.nationwide_jurisprudence import search_opinions  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description="Search CourtListener opinions for Finessa legal research")
    parser.add_argument("--query", required=True, help="Opinion full-text search query")
    parser.add_argument("--jurisdiction", default="US", help="US for national search, or a code with configured court IDs")
    parser.add_argument("--limit", type=int, default=50)
    parser.add_argument("--max-pages-per-court", type=int, default=3)
    parser.add_argument("--date-filed-min", help="YYYY-MM-DD")
    parser.add_argument("--date-filed-max", help="YYYY-MM-DD")
    args = parser.parse_args()
    try:
        response = search_opinions(
            args.query,
            jurisdiction=args.jurisdiction,
            limit=args.limit,
            max_pages_per_court=args.max_pages_per_court,
            date_filed_min=args.date_filed_min,
            date_filed_max=args.date_filed_max,
        )
    except (ValueError, RuntimeError) as exc:
        parser.error(str(exc))
    print(json.dumps(response, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

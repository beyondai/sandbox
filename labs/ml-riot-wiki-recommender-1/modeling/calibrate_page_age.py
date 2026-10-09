"""Map dates to enwiki page ids, so page id can stand in for creation date.

Page ids are given out in creation order. For each date D, binary-search
the smallest page id whose first revision is on or after D, using the
public MediaWiki API (one page per call, first revision only). The result
is small and goes in git: modeling/page_id_dates.json.

Proxy only. Riot has `wiki.pages.created` and needs none of this.

Run: uv run python3 modeling/calibrate_page_age.py   (from the project folder)
"""

from __future__ import annotations

import bz2
import json
import subprocess
import time
import urllib.parse
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import polars as pl

DATES = [
    "2026-06-01", "2026-07-01", "2026-07-18", "2026-08-01",
    "2026-08-18", "2026-09-01", "2026-10-01",
]
API = "https://en.wikipedia.org/w/api.php"
UA = "riot-wiki-proxy-research/0.1 (sandbox research; contact via repo owner)"
HERE = Path(__file__).resolve().parent
PAGES = HERE.parents[2] / "data" / "wikipedia-clickstream" / "pages"
INDEX = PAGES / "enwiki-20261001-pages-articles-multistream-index.txt.bz2"
IDS = PAGES / "page_ids.parquet"


def first_rev(pid: int) -> datetime:
    """First revision time of an existing page id."""
    q = urllib.parse.urlencode({
        "action": "query", "format": "json", "pageids": pid, "prop": "revisions",
        "rvprop": "timestamp", "rvdir": "newer", "rvlimit": 1,
    })
    for attempt in range(8):
        # curl, not urllib: the local Python has no CA bundle configured.
        r = subprocess.run(["curl", "-sS", "-w", "\n%{http_code}", "-A", UA, f"{API}?{q}"],
                           capture_output=True, text=True)
        body, _, code = r.stdout.rpartition("\n")
        time.sleep(1.0)
        if code == "200":
            page = json.loads(body)["query"]["pages"][str(pid)]
            ts = page["revisions"][0]["timestamp"]
            return datetime.fromisoformat(ts.replace("Z", "+00:00"))
        time.sleep(5 * (attempt + 1))
    raise RuntimeError(f"API failed for page id {pid}")


def load_ids() -> np.ndarray:
    """Article page ids from the 2026-10-01 dump index (offset:id:title)."""
    if not IDS.exists():
        ids, titles = [], []
        with bz2.open(INDEX, "rt", encoding="utf-8") as f:
            for line in f:
                _, pid, title = line.rstrip("\n").split(":", 2)
                ids.append(int(pid))
                titles.append(title.replace(" ", "_"))
        pl.DataFrame({"page_id": ids, "title": titles}).write_parquet(IDS)
    return np.sort(pl.read_parquet(IDS)["page_id"].to_numpy())


def id_for(date: str, ids: np.ndarray) -> int:
    """Smallest existing page id whose first revision is on or after date."""
    d = datetime.fromisoformat(date).replace(tzinfo=timezone.utc)
    lo, hi = 0, len(ids) - 1
    while lo < hi:
        mid = (lo + hi) // 2
        if first_rev(int(ids[mid])) >= d:
            hi = mid
        else:
            lo = mid + 1
    return int(ids[lo])


def main() -> None:
    ids = load_ids()
    print(f'{len(ids):,} page ids, max {ids[-1]:,}', flush=True)
    out = {}
    for d in DATES:
        out[d] = id_for(d, ids)
        print(d, out[d], flush=True)
    ids = list(out.values())
    assert ids == sorted(ids), "page ids must grow with date"
    (HERE / "page_id_dates.json").write_text(json.dumps(out, indent=2))


if __name__ == "__main__":
    main()

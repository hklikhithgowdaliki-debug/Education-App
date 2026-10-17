"""Verify every PDF link in data/sources/*.json and drop dead ones.

A link is dead when its server answers 404/410 or returns something that is not a PDF.
Hosts that cannot be reached at all (network errors) are kept, so a temporary outage or
geo-block never wipes a whole board. Run before tools/build_catalog.py.
"""
import concurrent.futures as cf
import json
import sys
import urllib.error
import urllib.request
from pathlib import Path

SOURCES = Path(__file__).resolve().parent.parent / "data" / "sources"


def status(url):
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0", "Range": "bytes=0-7"})
    try:
        with urllib.request.urlopen(req, timeout=40) as r:
            return "ok" if r.read(5).startswith(b"%PDF") else "dead"
    except urllib.error.HTTPError as e:
        return "dead" if e.code in (404, 410) else "unknown"
    except Exception:
        return "unknown"


def main():
    files = [SOURCES / f for f in sys.argv[1:]] or sorted(SOURCES.glob("*.json"))
    for f in files:
        entries = json.loads(f.read_text())
        urls = sorted({e["url"] for e in entries})
        with cf.ThreadPoolExecutor(16) as ex:
            result = dict(zip(urls, ex.map(status, urls)))
        kept = [e for e in entries if result[e["url"]] != "dead"]
        f.write_text(json.dumps(kept, indent=1, ensure_ascii=False))
        counts = {s: list(result.values()).count(s) for s in ("ok", "dead", "unknown")}
        print(f"{f.name}: {counts} -> kept {len(kept)}/{len(entries)} entries", file=sys.stderr)


if __name__ == "__main__":
    main()

"""Merge every data/sources/*.json file into data/catalog.json (the app's database).

The app downloads data/catalog.json from GitHub on launch, so adding papers only needs
an edit to a source file + running this script + pushing. A copy is bundled in the app
(app/assets/catalog.json) for first launch / offline use.
"""
import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SOURCES = ROOT / "data" / "sources"
OUT = ROOT / "data" / "catalog.json"
ASSET = ROOT / "app" / "assets" / "catalog.json"
REQUIRED = ("board", "stream", "subject", "url")
BOARD_ORDER = {"Karnataka SSLC": 0, "Karnataka 2nd PUC": 1, "VTU Engineering": 2}


def main():
    papers, seen, errors = [], set(), []
    for f in sorted(SOURCES.glob("*.json")):
        for i, e in enumerate(json.loads(f.read_text())):
            missing = [k for k in REQUIRED if not e.get(k)]
            if missing:
                errors.append(f"{f.name}[{i}] missing {missing}")
                continue
            if not e["url"].startswith("https://"):
                errors.append(f"{f.name}[{i}] url must be https")
                continue
            key = (e["url"], e.get("stream", ""), e.get("group", ""), e.get("semester", ""))
            if key in seen:
                continue
            seen.add(key)
            e["id"] = hashlib.sha1("|".join(key).encode()).hexdigest()[:12]
            papers.append(e)
    papers.sort(key=lambda e: (BOARD_ORDER.get(e["board"], 9), e.get("stream", ""),
                               -int(e.get("year") or 0), e.get("semester", ""), e["subject"]))
    catalog = {
        "version": 1,
        "generated": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "count": len(papers),
        "papers": papers,
    }
    text = json.dumps(catalog, ensure_ascii=False, separators=(",", ":"))
    for path in (OUT, ASSET):
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text)
    for err in errors:
        print("WARN", err, file=sys.stderr)
    print(f"catalog: {len(papers)} papers -> {OUT.relative_to(ROOT)}", file=sys.stderr)


if __name__ == "__main__":
    main()

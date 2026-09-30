from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from app.data_loader import AssetLoadError, normalize_deeplinks, normalize_records


def read_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8-sig"))


def main() -> None:
    parser = argparse.ArgumentParser(description="Validate and normalize the official GuideRail starter assets")
    parser.add_argument("source", type=Path, help="Folder containing queries.json, siis_responses.json, and deeplinks.json")
    parser.add_argument("output", type=Path, help="Destination folder for normalized runtime assets")
    parser.add_argument("--version", default="official-v1", help="Catalog/data version written to version.txt")
    args = parser.parse_args()

    required = ["queries.json", "deeplinks.json"]
    missing = [name for name in required if not (args.source / name).exists()]
    if missing:
        raise SystemExit(f"Missing required file(s): {', '.join(missing)}")
    siis = read_json(args.source / "siis_responses.json") if (args.source / "siis_responses.json").exists() else None
    try:
        deeplinks = normalize_deeplinks(read_json(args.source / "deeplinks.json"))
        records = normalize_records(read_json(args.source / "queries.json"), siis)
    except AssetLoadError as exc:
        raise SystemExit(str(exc)) from exc

    catalog_ids = {entry["id"] for entry in deeplinks}
    unknown = sorted({
        action.get("deeplink_id")
        for record in records
        for action in record.get("actions", [])
        if action.get("category") == "auto" and action.get("deeplink_id") not in catalog_ids
    })
    if unknown:
        raise SystemExit(f"Auto actions reference unknown catalog IDs: {', '.join(unknown)}")

    args.output.mkdir(parents=True, exist_ok=True)
    (args.output / "knowledge.json").write_text(json.dumps(records, ensure_ascii=False, indent=2), encoding="utf-8")
    (args.output / "deeplinks.json").write_text(json.dumps(deeplinks, ensure_ascii=False, indent=2), encoding="utf-8")
    (args.output / "version.txt").write_text(args.version + "\n", encoding="utf-8")
    report = {
        "source": str(args.source.resolve()),
        "output": str(args.output.resolve()),
        "records": len(records),
        "deeplinks": len(deeplinks),
        "version": args.version,
        "status": "ready",
    }
    (args.output / "import_report.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()

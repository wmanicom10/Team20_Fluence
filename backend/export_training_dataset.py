from __future__ import annotations

import argparse
import json
from pathlib import Path

from app import create_app
from ai_dataset_export import dataset_to_csv, export_training_dataset


def main() -> int:
    parser = argparse.ArgumentParser(description="Export Fluence AI training dataset from verified case data.")
    parser.add_argument("--start-date", dest="start_date", help="Filter rows on or after YYYY-MM-DD")
    parser.add_argument("--end-date", dest="end_date", help="Filter rows on or before YYYY-MM-DD")
    parser.add_argument("--disease", help="Optional disease name filter")
    parser.add_argument("--verified-only", default="true", help="true/false, default true")
    parser.add_argument("--format", choices=["json", "csv"], default="json")
    parser.add_argument("--output", required=True, help="Output file path")
    args = parser.parse_args()

    app = create_app()
    with app.app_context():
        dataset = export_training_dataset(app, {
            "start_date": args.start_date,
            "end_date": args.end_date,
            "disease": args.disease,
            "verified_only": args.verified_only,
        })

    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    if args.format == "json":
        output_path.write_text(json.dumps(dataset, indent=2), encoding="utf-8")
    else:
        output_path.write_text(dataset_to_csv(dataset), encoding="utf-8")

    print(f"Wrote {args.format.upper()} dataset to {output_path}")
    print(json.dumps(dataset["meta"], indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

from __future__ import annotations

import argparse
import json
from datetime import datetime
from pathlib import Path
from typing import Any


DEFAULT_REGIONS = (
    "전주",
    "군산",
    "익산",
    "남원",
    "김제",
    "정읍",
    "완주",
    "진안",
    "무주",
    "장수",
    "임실",
    "순창",
    "고창",
    "부안",
)


def build_fallback_weather(reference_date: str) -> dict[str, Any]:
    records = [
        {
            "date": reference_date,
            "region": region,
            "weather_code": "unknown",
            "temperature_c": None,
            "precipitation_mm": None,
            "is_estimated": True,
            "source": {
                "provider": "기상청",
                "reference_date": reference_date,
                "updated_at": datetime.now().isoformat(),
                "is_estimated": True,
            },
        }
        for region in DEFAULT_REGIONS
    ]

    return {
        "generated_at": datetime.now().isoformat(),
        "reference_date": reference_date,
        "records": records,
        "meta": {
            "mode": "fallback",
            "message": "KMA weather integration placeholder until the exact endpoint is finalized.",
        },
    }


def write_weather(output_path: Path, reference_date: str) -> dict[str, Any]:
    payload = build_fallback_weather(reference_date)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return payload


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Create SafeTrip JB daily weather records")
    parser.add_argument("command", nargs="?", default="write", choices=("write",))
    parser.add_argument("--output", default="data/processed/weather_daily.json")
    parser.add_argument("--reference-date", default=datetime.now().date().isoformat())
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    payload = write_weather(Path(args.output), args.reference_date)
    print(f"Wrote {len(payload['records'])} weather records to {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

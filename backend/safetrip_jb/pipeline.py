from __future__ import annotations

import argparse
import csv
import json
from collections import defaultdict
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

from .weather import write_weather


REGION_ID_BY_NAME = {
    "전체": "jeonbuk",
    "전북": "jeonbuk",
    "전라북도": "jeonbuk",
    "전북특별자치도": "jeonbuk",
    "전주": "jeonju",
    "전주시": "jeonju",
    "군산": "gunsan",
    "군산시": "gunsan",
    "익산": "iksan",
    "익산시": "iksan",
    "남원": "namwon",
    "남원시": "namwon",
    "김제": "gimje",
    "김제시": "gimje",
    "정읍": "jeongeup",
    "정읍시": "jeongeup",
    "완주": "wanju",
    "완주군": "wanju",
    "진안": "jinan",
    "진안군": "jinan",
    "무주": "muju",
    "무주군": "muju",
    "장수": "jangsu",
    "장수군": "jangsu",
    "임실": "imsil",
    "임실군": "imsil",
    "순창": "sunchang",
    "순창군": "sunchang",
    "고창": "gochang",
    "고창군": "gochang",
    "부안": "buan",
    "부안군": "buan",
}

MOJIBAKE_REGION_BY_ID = {
    "jeonbuk": {"?꾩껜"},
    "jeonju": {"?꾩＜??"},
    "gunsan": {"援곗궛??"},
    "iksan": {"?듭궛??"},
    "namwon": {"?⑥썝??"},
    "gimje": {"源?쒖떆"},
    "jeongeup": {"?뺤쓭??"},
    "wanju": {"?꾩＜援?"},
    "jinan": {"吏꾩븞援?"},
    "muju": {"臾댁＜援?"},
    "jangsu": {"?μ닔援?"},
    "imsil": {"?꾩떎援?"},
    "sunchang": {"?쒖갹援?"},
    "gochang": {"怨좎갹援?"},
    "buan": {"遺?덇뎔"},
}

REGION_LABEL_BY_ID = {
    "jeonbuk": "전체",
    "jeonju": "전주",
    "gunsan": "군산",
    "iksan": "익산",
    "namwon": "남원",
    "gimje": "김제",
    "jeongeup": "정읍",
    "wanju": "완주",
    "jinan": "진안",
    "muju": "무주",
    "jangsu": "장수",
    "imsil": "임실",
    "sunchang": "순창",
    "gochang": "고창",
    "buan": "부안",
}


def log_event(log_path: Path, task: str, status: str, **extra: Any) -> None:
    log_path.parent.mkdir(parents=True, exist_ok=True)
    event = {
        "timestamp": datetime.now().isoformat(),
        "task": task,
        "status": status,
        **extra,
    }
    with log_path.open("a", encoding="utf-8") as file:
        file.write(json.dumps(event, ensure_ascii=False) + "\n")


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def parse_number(value: Any) -> int:
    if isinstance(value, int):
        return value
    if isinstance(value, float):
        return round(value)
    text = str(value or "").replace(",", "")
    try:
        return round(float(text))
    except ValueError:
        return 0


def normalized_visitor_count(record: dict[str, Any]) -> int:
    raw = record.get("raw") if isinstance(record.get("raw"), dict) else {}
    return parse_number(
        raw.get("touNum")
        or raw.get("visitor_count")
        or raw.get("visitorCount")
        or record.get("visitor_count")
    )


def normalize_region_id(value: str) -> str:
    text = str(value or "").strip()
    if text in REGION_ID_BY_NAME:
        return REGION_ID_BY_NAME[text]
    for region_id, aliases in MOJIBAKE_REGION_BY_ID.items():
        if text in aliases:
            return region_id
    compact = text.removesuffix("시").removesuffix("군")
    return REGION_ID_BY_NAME.get(compact, text)


def region_label(region_id: str, fallback: str) -> str:
    return REGION_LABEL_BY_ID.get(region_id, fallback)


def saturation_status(visitor_count: int) -> str:
    if visitor_count >= 300_000:
        return "crowded"
    if visitor_count >= 150_000:
        return "caution"
    if visitor_count >= 50_000:
        return "normal"
    return "safe"


def iter_dates(start: str, end: str) -> list[str]:
    start_date = datetime.strptime(start, "%Y-%m-%d").date()
    end_date = datetime.strptime(end, "%Y-%m-%d").date()
    if end_date < start_date:
        start_date, end_date = end_date, start_date
    dates = []
    cursor = start_date
    while cursor <= end_date:
        dates.append(cursor.isoformat())
        cursor += timedelta(days=1)
    return dates


def load_festival_days(csv_path: Path) -> dict[str, set[str]]:
    if not csv_path.exists():
        return {}

    festival_days: dict[str, set[str]] = defaultdict(set)
    with csv_path.open("r", encoding="utf-8-sig", newline="") as file:
        reader = csv.DictReader(file)
        for row in reader:
            region_id = normalize_region_id(row.get("administrative_level", ""))
            opening = row.get("opening_date", "").strip()
            closing = row.get("closing_date", "").strip() or opening
            if not region_id or not opening:
                continue
            for date in iter_dates(opening, closing):
                festival_days[region_id].add(date)
    return festival_days


def record_is_estimated(source_rows: list[dict[str, Any]], region_id: str, date: str) -> bool:
    matched = [
        row
        for row in source_rows
        if normalize_region_id(str(row.get("region") or "")) == region_id and row.get("date") == date
    ]
    if not matched:
        return True
    return any(row.get("source_endpoint") == "sample" or row.get("is_estimated") for row in matched)


def build_dashboard_features(visitor_input: Path, festival_csv: Path, output_path: Path) -> dict[str, Any]:
    visitor_payload = read_json(visitor_input)
    festival_days = load_festival_days(festival_csv)
    grouped: dict[tuple[str, str], int] = defaultdict(int)
    source_rows = visitor_payload.get("records", [])

    for record in source_rows:
        region_id = normalize_region_id(str(record.get("region") or ""))
        date = str(record.get("date") or "")
        if not region_id or not date:
            continue
        grouped[(region_id, date)] += normalized_visitor_count(record)

    baseline_values: dict[str, list[int]] = defaultdict(list)
    for (region_id, date), count in grouped.items():
        if date not in festival_days.get(region_id, set()):
            baseline_values[region_id].append(count)

    baselines: dict[str, int] = {}
    for region_id in {region_id for region_id, _date in grouped}:
        values = baseline_values.get(region_id) or [
            count for (candidate_region, _date), count in grouped.items() if candidate_region == region_id
        ]
        baselines[region_id] = round(sum(values) / len(values)) if values else 0

    records = []
    for (region_id, date), count in sorted(grouped.items()):
        has_festival = date in festival_days.get(region_id, set())
        status = saturation_status(count)
        baseline = baselines.get(region_id, 0)
        growth_rate = round(((count - baseline) / baseline) * 100, 1) if baseline else 0.0
        is_estimated = bool(record_is_estimated(source_rows, region_id, date))
        records.append(
            {
                "date": date,
                "region_id": region_id,
                "region": region_label(region_id, region_id),
                "visitor_count": count,
                "weekday": datetime.strptime(date, "%Y-%m-%d").strftime("%a"),
                "has_festival": has_festival,
                "baseline_visitor_count": baseline,
                "festival_baseline_growth_rate": growth_rate if has_festival else 0.0,
                "weather_code": "unknown",
                "traffic_congestion_level": status,
                "tourist_spot_congestion_level": status,
                "restaurant_wait_index": round(min(count / 300_000, 1.0), 2),
                "saturation_status": status,
                "is_estimated": is_estimated,
                "source": {
                    "provider": "한국관광공사",
                    "reference_date": date,
                    "updated_at": visitor_payload.get("generated_at") or datetime.now().isoformat(),
                    "is_estimated": is_estimated,
                },
            }
        )

    payload = {
        "generated_at": datetime.now().isoformat(),
        "records": records,
        "summary": {
            "record_count": len(records),
            "regions": sorted({record["region"] for record in records}),
        },
    }
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return payload


def run_pipeline(args: argparse.Namespace) -> int:
    log_path = Path(args.log)

    try:
        weather_payload = write_weather(Path(args.weather_output), args.reference_date)
        log_event(log_path, "weather", "success", records=len(weather_payload["records"]), retry_count=0)
    except Exception as error:
        log_event(log_path, "weather", "failed", error=str(error), retry_count=0)
        raise

    try:
        payload = build_dashboard_features(
            visitor_input=Path(args.visitor_input),
            festival_csv=Path(args.festival_csv),
            output_path=Path(args.output),
        )
        log_event(log_path, "derive-dashboard-features", "success", records=len(payload["records"]), retry_count=0)
    except Exception as error:
        log_event(log_path, "derive-dashboard-features", "failed", error=str(error), retry_count=0)
        raise

    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run SafeTrip JB MVP data pipeline tasks")
    subparsers = parser.add_subparsers(dest="command")

    derive = subparsers.add_parser("derive", help="Build dashboard features from processed data")
    derive.add_argument("--visitor-input", default="data/processed/jeonbuk_visitors_daily.json")
    derive.add_argument("--festival-csv", default="data/processed/historical_festivals_en.csv")
    derive.add_argument("--output", default="data/processed/dashboard_features.json")
    derive.set_defaults(
        func=lambda args: build_dashboard_features(
            Path(args.visitor_input),
            Path(args.festival_csv),
            Path(args.output),
        )
    )

    run = subparsers.add_parser("run", help="Run local MVP pipeline with fallback-capable tasks")
    run.add_argument("--visitor-input", default="data/processed/jeonbuk_visitors_daily.json")
    run.add_argument("--festival-csv", default="data/processed/historical_festivals_en.csv")
    run.add_argument("--weather-output", default="data/processed/weather_daily.json")
    run.add_argument("--output", default="data/processed/dashboard_features.json")
    run.add_argument("--reference-date", default=datetime.now().date().isoformat())
    run.add_argument("--log", default="data/logs/pipeline/local.jsonl")
    run.set_defaults(func=run_pipeline)

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if not hasattr(args, "func"):
        parser.print_help()
        return 1
    result = args.func(args)
    return result if isinstance(result, int) else 0


if __name__ == "__main__":
    raise SystemExit(main())

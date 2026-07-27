from __future__ import annotations

import argparse
import json
import re
import sys
from collections import defaultdict
from datetime import datetime
from pathlib import Path
from typing import Any
from urllib.parse import urlencode
from urllib.request import Request, urlopen
from xml.etree import ElementTree

from .festival_history import get_setting, load_env_settings, mask_url


KTO_ENDPOINTS = {
    "metro": "/metcoRegnVisitrDDList",
    "local": "/locgoRegnVisitrDDList",
}

JEONBUK_NAMES = (
    "전북",
    "전라북",
    "전북특별자치도",
    "전라북도",
    "Jeonbuk",
    "Jeollabuk",
)

JEONBUK_LOCAL_NAMES = {
    "전주",
    "전주시",
    "군산",
    "군산시",
    "익산",
    "익산시",
    "정읍",
    "정읍시",
    "남원",
    "남원시",
    "김제",
    "김제시",
    "완주",
    "완주군",
    "진안",
    "진안군",
    "무주",
    "무주군",
    "장수",
    "장수군",
    "임실",
    "임실군",
    "순창",
    "순창군",
    "고창",
    "고창군",
    "부안",
    "부안군",
}

VISITOR_FIELDS = (
    "visitor_count",
    "visitorCount",
    "visitrCnt",
    "visitorCnt",
    "touNum",
    "touNumCnt",
    "totCnt",
    "ttCnt",
    "cnt",
)

DATE_FIELDS = ("baseYmd", "baseDate", "stdYmd", "date", "ymd")
REGION_FIELDS = ("signguNm", "sigunguNm", "locgoRegnNm", "areaNm", "sidoNm", "regionName", "regnNm")


def build_kto_url(env: dict[str, str], endpoint: str, start_ymd: str, end_ymd: str, page_no: int, rows: int) -> str:
    base_url = get_setting("KTO_DATALAB_BASE_URL", env, "https://apis.data.go.kr/B551011/DataLabService").rstrip("/")
    service_key = get_setting("KTO_SERVICE_KEY", env) or get_setting("KTO_DATALAB_SERVICE_KEY", env)
    mobile_os = get_setting("KTO_MOBILE_OS", env, "ETC")
    mobile_app = get_setting("KTO_MOBILE_APP", env, "SafeTrip")
    response_type = get_setting("KTO_RESPONSE_TYPE", env, "json")

    if not service_key:
        raise ValueError("KTO_SERVICE_KEY is empty. Add your Korea Tourism Organization API key to .env.")

    query = {
        "numOfRows": rows,
        "pageNo": page_no,
        "MobileOS": mobile_os,
        "MobileApp": mobile_app,
        "serviceKey": service_key,
        "startYmd": start_ymd,
        "endYmd": end_ymd,
        "_type": response_type,
    }
    return f"{base_url}{endpoint}?{urlencode(query)}"


def fetch_kto_records(env_path: Path, start_ymd: str, end_ymd: str, rows: int, page_no: int) -> list[dict[str, Any]]:
    env, resolved = load_env_settings(env_path)
    all_records: list[dict[str, Any]] = []

    for name, endpoint in KTO_ENDPOINTS.items():
        url = build_kto_url(env, endpoint, start_ymd=start_ymd, end_ymd=end_ymd, page_no=page_no, rows=rows)
        if resolved:
            print(f"Loaded env from {resolved}", file=sys.stderr)
        print(f"Requesting {name} {mask_url(url)}", file=sys.stderr)
        request = Request(url, headers={"Accept": "application/json, application/xml;q=0.9"})
        with urlopen(request, timeout=30) as response:
            body = response.read()
        records = parse_response(body)
        for record in records:
            record["_source_endpoint"] = name
        all_records.extend(records)

    return all_records


def parse_response(body: bytes) -> list[dict[str, Any]]:
    text = body.decode("utf-8-sig")
    stripped = text.lstrip()
    if stripped.startswith("{") or stripped.startswith("["):
        return records_from_json(json.loads(text))
    if stripped.startswith("<"):
        return records_from_xml(text)
    raise ValueError("Unsupported KTO response format.")


def records_from_json(payload: Any) -> list[dict[str, Any]]:
    if isinstance(payload, list):
        return [item for item in payload if isinstance(item, dict)]

    body = payload.get("response", {}).get("body", {}) if isinstance(payload, dict) else {}
    items = body.get("items", {}).get("item") if isinstance(body.get("items"), dict) else body.get("items")
    if isinstance(items, list):
        return [item for item in items if isinstance(item, dict)]
    if isinstance(items, dict):
        return [items]

    for key in ("data", "items", "records"):
        value = payload.get(key) if isinstance(payload, dict) else None
        if isinstance(value, list):
            return [item for item in value if isinstance(item, dict)]
    return []


def records_from_xml(text: str) -> list[dict[str, Any]]:
    root = ElementTree.fromstring(text)
    records: list[dict[str, Any]] = []
    for item in root.iter():
        if strip_namespace(item.tag) != "item":
            continue
        row = {strip_namespace(child.tag): (child.text or "").strip() for child in list(item)}
        if row:
            records.append(row)
    return records


def strip_namespace(tag: str) -> str:
    return tag.rsplit("}", 1)[-1] if "}" in tag else tag


def normalize_records(records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    normalized: list[dict[str, Any]] = []
    for record in records:
        region = pick_region(record)
        date_value = pick_first(record, DATE_FIELDS)
        visitors = pick_number(record, VISITOR_FIELDS)

        if not region or not date_value:
            continue
        if not is_jeonbuk_record(record, region):
            continue

        source_endpoint = str(record.get("_source_endpoint", ""))
        region_name = "전체" if source_endpoint == "metro" and is_jeonbuk_record(record, region) else normalize_region_name(region)

        normalized.append(
            {
                "date": normalize_ymd(date_value),
                "region": region_name,
                "visitor_count": visitors,
                "source_endpoint": source_endpoint,
                "raw": record,
            }
        )
    return sorted(normalized, key=lambda item: (item["region"], item["date"]))


def pick_region(record: dict[str, Any]) -> str:
    for field in REGION_FIELDS:
        value = record.get(field)
        if value not in (None, ""):
            return str(value).strip()
    for key, value in record.items():
        if key.endswith("Nm") and value not in (None, ""):
            return str(value).strip()
    return ""


def pick_first(record: dict[str, Any], fields: tuple[str, ...]) -> str:
    for field in fields:
        value = record.get(field)
        if value not in (None, ""):
            return str(value).strip()
    return ""


def pick_number(record: dict[str, Any], fields: tuple[str, ...]) -> int:
    for field in fields:
        value = record.get(field)
        if value not in (None, ""):
            return parse_int(value)

    numeric_candidates = []
    for key, value in record.items():
        key_lower = key.lower()
        if "num" in key_lower or "cnt" in key_lower or "count" in key_lower:
            numeric_candidates.append(parse_int(value))
    return max(numeric_candidates) if numeric_candidates else 0


def parse_int(value: Any) -> int:
    if isinstance(value, int):
        return value
    if isinstance(value, float):
        return int(round(value))
    text = str(value or "")
    digits = re.search(r"-?\d+(?:\.\d+)?", text.replace(",", ""))
    if not digits:
        return 0
    return int(round(float(digits.group(0))))


def is_jeonbuk_record(record: dict[str, Any], region: str) -> bool:
    haystack = " ".join(str(value) for value in record.values() if value is not None)
    if any(name in haystack for name in JEONBUK_NAMES):
        return True
    return normalize_region_name(region) in JEONBUK_LOCAL_NAMES


def normalize_region_name(value: str) -> str:
    text = value.strip()
    if text in JEONBUK_NAMES:
        return "전북특별자치도"
    return text


def normalize_ymd(value: str) -> str:
    text = re.sub(r"[^0-9]", "", value)
    if len(text) == 8:
        return datetime.strptime(text, "%Y%m%d").date().isoformat()
    return value


def summarize(records: list[dict[str, Any]]) -> dict[str, Any]:
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for record in records:
        grouped[record["region"]].append(record)

    summaries = {region: summarize_region(region, rows) for region, rows in grouped.items()}
    if "전체" not in summaries:
        all_daily: dict[str, int] = defaultdict(int)
        for record in records:
            all_daily[record["date"]] += record["visitor_count"]
        all_records = [{"date": date, "visitor_count": count} for date, count in sorted(all_daily.items())]
        summaries["전체"] = summarize_region("전체", all_records)

    return {
        "regions": sorted(summaries.keys(), key=lambda value: (value != "전체", value)),
        "default_region": "전체",
        "summaries": summaries,
    }


def summarize_region(region: str, records: list[dict[str, Any]]) -> dict[str, Any]:
    sorted_records = sorted(records, key=lambda item: item["date"])
    cumulative = sum(int(record["visitor_count"]) for record in sorted_records)
    midpoint = max(len(sorted_records) // 2, 1)
    previous = sum(int(record["visitor_count"]) for record in sorted_records[:midpoint])
    current = sum(int(record["visitor_count"]) for record in sorted_records[midpoint:])
    growth_rate = ((current - previous) / previous * 100) if previous else 0
    peak = max(sorted_records, key=lambda item: int(item["visitor_count"])) if sorted_records else {"date": "-", "visitor_count": 0}

    return {
        "region": region,
        "cumulative_visitors": cumulative,
        "growth_rate": round(growth_rate, 1),
        "peak_date": peak["date"],
        "peak_visitors": int(peak["visitor_count"]),
        "daily": [
            {
                "date": record["date"],
                "visitor_count": int(record["visitor_count"]),
            }
            for record in sorted_records
        ],
    }


def fetch_and_write(env_path: Path, output_path: Path, start_ymd: str, end_ymd: str, rows: int, page_no: int) -> dict[str, Any]:
    raw_records = fetch_kto_records(env_path, start_ymd=start_ymd, end_ymd=end_ymd, rows=rows, page_no=page_no)
    normalized = normalize_records(raw_records)
    payload = {
        "generated_at": datetime.now().isoformat(),
        "start_ymd": start_ymd,
        "end_ymd": end_ymd,
        "records": normalized,
        **summarize(normalized),
    }
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return payload


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Fetch and summarize KTO DataLab visitor data for Jeonbuk")
    parser.add_argument("fetch", nargs="?")
    parser.add_argument("--env", default=".env")
    parser.add_argument("--output", default="data/processed/jeonbuk_visitors_daily.json")
    parser.add_argument("--start-ymd", required=True)
    parser.add_argument("--end-ymd", required=True)
    parser.add_argument("--rows", type=int, default=1000)
    parser.add_argument("--page-no", type=int, default=1)
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    try:
        payload = fetch_and_write(
            env_path=Path(args.env),
            output_path=Path(args.output),
            start_ymd=args.start_ymd,
            end_ymd=args.end_ymd,
            rows=args.rows,
            page_no=args.page_no,
        )
        print(f"Wrote {len(payload['records'])} Jeonbuk visitor records to {args.output}")
        return 0
    except Exception as error:
        print(f"Error: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())

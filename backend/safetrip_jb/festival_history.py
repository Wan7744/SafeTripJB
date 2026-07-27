from __future__ import annotations

import argparse
import csv
import json
import math
import os
import re
import statistics
import sys
from dataclasses import dataclass
from datetime import date, datetime
from pathlib import Path
from typing import Any
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit
from urllib.request import Request, urlopen
from xml.etree import ElementTree

MODULE_ROOT = Path(__file__).resolve().parents[2]
BACKEND_ROOT = MODULE_ROOT / "backend"
DEFAULT_ENV_NAMES = (".env", ".env.local", ".env.development")

COLUMN_MAP = {
    "번호": "serial_number",
    "구분": "administrative_level",
    "축제명": "festival_name",
    "개막일": "opening_date",
    "폐막일": "closing_date",
    "관광객수": "visitor_count",
    "관광객수(명)": "visitor_count",
    "관광객수 (명)": "visitor_count",
    "비고": "notes",
}

OUTPUT_COLUMNS = [
    "serial_number",
    "administrative_level",
    "festival_name",
    "opening_date",
    "closing_date",
    "visitor_count",
    "notes",
]

NOTE_TRANSLATIONS = {
    "": "",
    "-": "",
    "없음": "None",
    "해당없음": "Not applicable",
    "자료없음": "No data",
    "미집계": "Not counted",
    "집계중": "Counting in progress",
    "추정": "Estimated",
    "잠정": "Preliminary",
    "취소": "Cancelled",
    "미개최": "Not held",
    "연기": "Postponed",
    "순연": "Delayed",
    "우천취소": "Cancelled due to rain",
    "온라인": "Held online",
    "온라인 개최": "Held online",
    "코로나19": "COVID-19",
    "코로나": "COVID-19",
    "코로나19로 취소": "Cancelled due to COVID-19",
    "코로나19로 미개최": "Not held due to COVID-19",
    "코로나로 취소": "Cancelled due to COVID-19",
    "관광객수 미집계": "Visitor count not collected",
}


@dataclass(frozen=True)
class FestivalRecord:
    serial_number: str
    administrative_level: str
    festival_name: str
    opening_date: str
    closing_date: str
    visitor_count: int
    notes: str

    @property
    def opening(self) -> date | None:
        return parse_date(self.opening_date)

    @property
    def closing(self) -> date | None:
        return parse_date(self.closing_date)

    @property
    def duration_days(self) -> int:
        if self.opening is None or self.closing is None:
            return 1
        return max((self.closing - self.opening).days + 1, 1)

    @property
    def visitors_per_day(self) -> float:
        return self.visitor_count / self.duration_days if self.duration_days else float(self.visitor_count)


def read_env(path: Path) -> dict[str, str]:
    if not path.exists():
        return {}

    values: dict[str, str] = {}
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        values[key.strip()] = value.strip().strip('"').strip("'")
    return values


def resolve_env_path(path: Path) -> Path:
    candidates: list[Path] = []

    env_override = os.environ.get("SAFETRIP_ENV_FILE")
    if env_override:
        override_path = Path(env_override).expanduser()
        candidates.extend(_expand_env_candidate(override_path))

    candidates.extend(_expand_env_candidate(path))

    if path == Path(".env"):
        for base in (Path.cwd(), MODULE_ROOT, BACKEND_ROOT):
            for ancestor in (base, *base.parents):
                for name in DEFAULT_ENV_NAMES:
                    candidates.append(ancestor / name)

    seen: set[str] = set()
    for candidate in candidates:
        resolved = candidate.expanduser()
        key = str(resolved.resolve()) if resolved.exists() else str(resolved)
        if key in seen:
            continue
        seen.add(key)
        if resolved.exists():
            return resolved
    return path


def _expand_env_candidate(path: Path) -> list[Path]:
    if path.is_absolute():
        return [path]
    return [
        path,
        Path.cwd() / path,
        MODULE_ROOT / path,
        BACKEND_ROOT / path,
    ]


def load_env_settings(path: Path) -> tuple[dict[str, str], Path | None]:
    resolved = resolve_env_path(path)
    if resolved.exists():
        return read_env(resolved), resolved
    return {}, None


def get_setting(name: str, env: dict[str, str], default: str = "") -> str:
    return os.environ.get(name) or env.get(name, default)


def build_odcloud_url(env: dict[str, str], page: int | None = None, per_page: int | None = None) -> str:
    base_url = get_setting("ODCLOUD_BASE_URL", env, "https://api.odcloud.kr/api").rstrip("/")
    namespace = get_setting("ODCLOUD_NAMESPACE", env, "15055596/v1").strip("/")
    resource_path = get_setting("ODCLOUD_RESOURCE_PATH", env).strip()
    service_key = get_setting("ODCLOUD_SERVICE_KEY", env)
    response_format = get_setting("ODCLOUD_RESPONSE_FORMAT", env, "json")

    if not service_key:
        raise ValueError("ODCLOUD_SERVICE_KEY is empty. Add your public data portal key to .env.")
    if not resource_path:
        raise ValueError("ODCLOUD_RESOURCE_PATH is empty. Add the Swagger API path to .env.")

    query = {
        "page": page or int(get_setting("ODCLOUD_DEFAULT_PAGE", env, "1")),
        "perPage": per_page or int(get_setting("ODCLOUD_DEFAULT_PER_PAGE", env, "100")),
        "serviceKey": service_key,
        "returnType": response_format,
    }
    return append_query(build_odcloud_endpoint(base_url, namespace, resource_path), query)


def build_odcloud_endpoint(base_url: str, namespace: str, resource_path: str) -> str:
    if resource_path.startswith(("http://", "https://")):
        if "infuser.odcloud.kr/oas/docs" in resource_path:
            raise ValueError("ODCLOUD_RESOURCE_PATH must be an API path, not the Swagger docs URL.")
        return resource_path

    cleaned_path = resource_path.strip()
    namespace = namespace.strip("/")

    if cleaned_path.startswith("/api/"):
        api_root = base_url.removesuffix("/api")
        return f"{api_root}{cleaned_path}"

    if cleaned_path.startswith("/"):
        return f"{base_url}{cleaned_path}"

    if namespace and cleaned_path.startswith(f"{namespace}/"):
        return f"{base_url}/{cleaned_path}"

    return f"{base_url}/{namespace}/{cleaned_path}" if namespace else f"{base_url}/{cleaned_path}"


def append_query(endpoint: str, query: dict[str, Any]) -> str:
    parts = urlsplit(endpoint)
    existing_query = dict(parse_qsl(parts.query, keep_blank_values=True))
    existing_query.update({key: str(value) for key, value in query.items() if value is not None})
    return urlunsplit((parts.scheme, parts.netloc, parts.path, urlencode(existing_query), parts.fragment))


def mask_url(url: str) -> str:
    parts = urlsplit(url)
    pairs = []
    for key, value in parse_qsl(parts.query, keep_blank_values=True):
        pairs.append((key, "***" if key.lower() == "servicekey" else value))
    return urlunsplit((parts.scheme, parts.netloc, parts.path, urlencode(pairs), parts.fragment))


def fetch_odcloud_data(env_path: Path, output_path: Path, page: int | None = None, per_page: int | None = None) -> Path:
    env, resolved_env_path = load_env_settings(env_path)
    url = build_odcloud_url(env, page=page, per_page=per_page)
    request = Request(url, headers={"Accept": "application/json, application/xml;q=0.9"})

    output_path.parent.mkdir(parents=True, exist_ok=True)
    if resolved_env_path is not None:
        print(f"Loaded env from {resolved_env_path}", file=sys.stderr)
    print(f"Requesting {mask_url(url)}", file=sys.stderr)
    with urlopen(request, timeout=30) as response:
        output_path.write_bytes(response.read())
    if resolved_env_path is None:
        print(f"Warning: could not find an env file for {env_path}", file=sys.stderr)
    return output_path


def load_records(input_path: Path) -> list[dict[str, Any]]:
    suffix = input_path.suffix.lower()
    content = input_path.read_text(encoding="utf-8-sig")

    if suffix == ".json":
        return records_from_json(json.loads(content))
    if suffix == ".xml":
        return records_from_xml(content)
    if suffix == ".csv":
        with input_path.open("r", encoding="utf-8-sig", newline="") as file:
            return list(csv.DictReader(file))

    stripped = content.lstrip()
    if stripped.startswith("{") or stripped.startswith("["):
        return records_from_json(json.loads(content))
    if stripped.startswith("<"):
        return records_from_xml(content)
    raise ValueError(f"Unsupported input file format: {input_path}")


def records_from_json(payload: Any) -> list[dict[str, Any]]:
    if isinstance(payload, list):
        return [record for record in payload if isinstance(record, dict)]
    if isinstance(payload, dict):
        for key in ("data", "items", "records", "rows"):
            value = payload.get(key)
            if isinstance(value, list):
                return [record for record in value if isinstance(record, dict)]
        nested = payload.get("response", {}).get("body", {}).get("items", {}).get("item")
        if isinstance(nested, list):
            return [record for record in nested if isinstance(record, dict)]
        if isinstance(nested, dict):
            return [nested]
    raise ValueError("Could not find a record list in the JSON payload.")


def records_from_xml(content: str) -> list[dict[str, Any]]:
    root = ElementTree.fromstring(content)
    candidates: list[dict[str, Any]] = []

    for element in root.iter():
        children = list(element)
        if not children:
            continue
        row = {strip_namespace(child.tag): (child.text or "").strip() for child in children if not list(child)}
        if any(key in row for key in COLUMN_MAP) or any(key in row for key in OUTPUT_COLUMNS):
            candidates.append(row)

    if not candidates:
        raise ValueError("Could not find festival records in the XML payload.")
    return candidates


def strip_namespace(tag: str) -> str:
    return tag.rsplit("}", 1)[-1] if "}" in tag else tag


def normalize_records(rows: list[dict[str, Any]]) -> list[FestivalRecord]:
    records: list[FestivalRecord] = []
    for row in rows:
        translated = {COLUMN_MAP.get(key, key): value for key, value in row.items()}
        visitor_count = parse_int(translated.get("visitor_count", 0))
        records.append(
            FestivalRecord(
                serial_number=str(translated.get("serial_number", "")).strip(),
                administrative_level=str(translated.get("administrative_level", "")).strip(),
                festival_name=str(translated.get("festival_name", "")).strip(),
                opening_date=normalize_date_text(translated.get("opening_date", "")),
                closing_date=normalize_date_text(translated.get("closing_date", "")),
                visitor_count=visitor_count,
                notes=translate_notes(str(translated.get("notes", "")).strip()),
            )
        )
    return records


def convert_to_english_csv(input_path: Path, output_path: Path) -> list[FestivalRecord]:
    records = normalize_records(load_records(input_path))
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with output_path.open("w", encoding="utf-8-sig", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=OUTPUT_COLUMNS)
        writer.writeheader()
        for record in records:
            writer.writerow(
                {
                    "serial_number": record.serial_number,
                    "administrative_level": record.administrative_level,
                    "festival_name": record.festival_name,
                    "opening_date": record.opening_date,
                    "closing_date": record.closing_date,
                    "visitor_count": record.visitor_count,
                    "notes": record.notes,
                }
            )
    return records


def translate_notes(text: str) -> str:
    compact = re.sub(r"\s+", " ", text.strip())
    if compact in NOTE_TRANSLATIONS:
        return NOTE_TRANSLATIONS[compact]

    translated = compact
    replacements = sorted(NOTE_TRANSLATIONS.items(), key=lambda item: len(item[0]), reverse=True)
    for korean, english in replacements:
        if korean and korean in translated:
            translated = translated.replace(korean, english)

    if translated != compact and not contains_korean(translated):
        return translated
    if not compact:
        return ""
    if not contains_korean(compact):
        return compact
    return f"Manual translation required: {compact}"


def contains_korean(text: str) -> bool:
    return bool(re.search(r"[가-힣]", text))


def normalize_date_text(value: Any) -> str:
    parsed = parse_date(str(value))
    return parsed.isoformat() if parsed else str(value or "").strip()


def parse_date(value: str) -> date | None:
    text = str(value or "").strip()
    if not text:
        return None

    text = re.sub(r"\([^)]*\)", "", text)
    text = text.replace("년", "-").replace("월", "-").replace("일", "")
    text = text.replace(".", "-").replace("/", "-").strip()
    text = re.sub(r"\s+", "", text)

    for pattern in ("%Y-%m-%d", "%Y-%m", "%Y%m%d"):
        try:
            parsed = datetime.strptime(text, pattern).date()
            return parsed
        except ValueError:
            continue
    return None


def parse_int(value: Any) -> int:
    if isinstance(value, int):
        return value
    if isinstance(value, float):
        return int(value)

    text = str(value or "")
    if not text.strip():
        return 0
    digits = re.sub(r"[^0-9-]", "", text)
    if not digits or digits == "-":
        return 0
    return int(digits)


def load_english_csv(input_path: Path) -> list[FestivalRecord]:
    with input_path.open("r", encoding="utf-8-sig", newline="") as file:
        rows = list(csv.DictReader(file))
    return normalize_records(rows)


def predict_visitors(
    records: list[FestivalRecord],
    opening_date: date,
    closing_date: date,
    administrative_level: str = "",
    festival_name: str = "",
) -> dict[str, Any]:
    target_duration = max((closing_date - opening_date).days + 1, 1)
    usable = [record for record in records if record.visitor_count > 0 and record.opening is not None]
    if not usable:
        raise ValueError("No historical records with visitor_count and opening_date were found.")

    scored = []
    for record in usable:
        assert record.opening is not None
        month_distance = min(abs(record.opening.month - opening_date.month), 12 - abs(record.opening.month - opening_date.month))
        month_score = 1 / (1 + month_distance)
        level_score = 1.25 if administrative_level and record.administrative_level == administrative_level else 1
        name_score = 1 + name_similarity(record.festival_name, festival_name)
        duration_score = 1 / (1 + abs(record.duration_days - target_duration))
        weight = month_score * level_score * name_score * (0.75 + duration_score)
        scored.append((record, weight))

    scored.sort(key=lambda item: item[1], reverse=True)
    top = scored[: min(8, len(scored))]
    weighted_daily = sum(record.visitors_per_day * weight for record, weight in top) / sum(weight for _, weight in top)
    estimate = int(round(weighted_daily * target_duration))
    spread = statistics.pstdev([record.visitors_per_day for record, _ in top]) if len(top) > 1 else 0
    confidence = confidence_label(len(top), weighted_daily, spread)

    return {
        "expected_visitor_count": estimate,
        "target_duration_days": target_duration,
        "confidence": confidence,
        "method": "weighted historical average by month, duration, administrative level, and festival name similarity",
        "based_on_records": [
            {
                "festival_name": record.festival_name,
                "opening_date": record.opening_date,
                "closing_date": record.closing_date,
                "visitor_count": record.visitor_count,
                "weight": round(weight, 4),
            }
            for record, weight in top
        ],
    }


def name_similarity(source: str, target: str) -> float:
    if not target:
        return 0
    source_tokens = set(re.findall(r"[A-Za-z0-9가-힣]+", source.lower()))
    target_tokens = set(re.findall(r"[A-Za-z0-9가-힣]+", target.lower()))
    if not source_tokens or not target_tokens:
        return 0
    return len(source_tokens & target_tokens) / math.sqrt(len(source_tokens) * len(target_tokens))


def confidence_label(sample_size: int, mean: float, spread: float) -> str:
    if sample_size < 3:
        return "low"
    if mean <= 0:
        return "low"
    variation = spread / mean
    if variation < 0.25:
        return "high"
    if variation < 0.6:
        return "medium"
    return "low"


def write_prediction(input_path: Path, output_path: Path, args: argparse.Namespace) -> dict[str, Any]:
    opening = parse_date(args.opening_date)
    closing = parse_date(args.closing_date)
    if opening is None or closing is None:
        raise ValueError("opening_date and closing_date must be valid dates.")
    if closing < opening:
        raise ValueError("closing_date must be the same as or later than opening_date.")

    result = predict_visitors(
        load_english_csv(input_path),
        opening_date=opening,
        closing_date=closing,
        administrative_level=args.administrative_level or "",
        festival_name=args.festival_name or "",
    )
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    return result


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="SafeTrip JB historical festival data tools")
    subparsers = parser.add_subparsers(dest="command", required=True)

    fetch = subparsers.add_parser("fetch", help="Fetch historical festival data from ODCLOUD")
    fetch.add_argument("--env", default=".env", help="Path to .env file")
    fetch.add_argument("--output", default="data/raw/historical_festivals.json")
    fetch.add_argument("--page", type=int)
    fetch.add_argument("--per-page", type=int)

    convert = subparsers.add_parser("convert", help="Translate columns and notes into a new English CSV")
    convert.add_argument("--input", required=True)
    convert.add_argument("--output", default="data/processed/historical_festivals_en.csv")

    predict = subparsers.add_parser("predict", help="Predict expected visitors from the English CSV")
    predict.add_argument("--input", default="data/processed/historical_festivals_en.csv")
    predict.add_argument("--output", default="data/processed/festival_visitor_prediction.json")
    predict.add_argument("--opening-date", required=True)
    predict.add_argument("--closing-date", required=True)
    predict.add_argument("--administrative-level", default="")
    predict.add_argument("--festival-name", default="")

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    try:
        if args.command == "fetch":
            path = fetch_odcloud_data(Path(args.env), Path(args.output), page=args.page, per_page=args.per_page)
            print(f"Fetched data to {path}")
        elif args.command == "convert":
            records = convert_to_english_csv(Path(args.input), Path(args.output))
            print(f"Wrote {len(records)} records to {args.output}")
        elif args.command == "predict":
            result = write_prediction(Path(args.input), Path(args.output), args)
            print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0
    except Exception as error:
        print(f"Error: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())

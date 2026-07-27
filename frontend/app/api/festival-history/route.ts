import { NextRequest, NextResponse } from "next/server";
import { readFile } from "node:fs/promises";
import path from "node:path";

export const dynamic = "force-dynamic";

type HistoricalFestivalRecord = {
  serialNumber: string;
  level: string;
  name: string;
  dates: string;
  visitors: number;
  notes: string;
};

type PredictionRecord = {
  festival_name: string;
  opening_date: string;
  closing_date: string;
  visitor_count: number;
  weight: number;
};

type PredictionPayload = {
  expected_visitor_count?: number;
  target_duration_days?: number;
  confidence?: string;
  method?: string;
  based_on_records?: PredictionRecord[];
};

const REGION_ALIASES: Record<string, string> = {
  all: "",
  전체: "",
  jeonju: "전주",
  gunsan: "군산",
  iksan: "익산",
  namwon: "남원"
};

const workspaceRoot = path.resolve(process.cwd(), "..");
const csvPath = path.join(workspaceRoot, "data", "processed", "historical_festivals_en.csv");
const predictionPath = path.join(workspaceRoot, "data", "processed", "festival_visitor_prediction.json");

export async function GET(request: NextRequest) {
  try {
    const regionFilter = normalizeRegion(request.nextUrl.searchParams.get("region") ?? "전체");
    const [csvText, predictionText] = await Promise.all([
      readFile(csvPath, "utf-8"),
      readFile(predictionPath, "utf-8").catch(() => "{}")
    ]);

    const rows = parseCsv(csvText);
    const records = rows
      .map(toHistoricalRecord)
      .filter((record): record is HistoricalFestivalRecord => record !== null)
      .filter((record) => matchesRegion(record.level, regionFilter));
    const prediction = normalizePrediction(JSON.parse(predictionText) as PredictionPayload);

    return NextResponse.json({
      success: true,
      data: {
        region: regionFilter || "전체",
        records,
        prediction,
        totalCount: records.length
      },
      meta: {
        generatedAt: new Date().toISOString(),
        source: "data/processed/historical_festivals_en.csv"
      }
    });
  } catch (error) {
    return NextResponse.json(
      {
        success: false,
        error: {
          code: "FESTIVAL_HISTORY_NOT_READY",
          message: error instanceof Error ? error.message : "Festival history data is not ready."
        }
      },
      { status: 500 }
    );
  }
}

function normalizeRegion(region: string) {
  return REGION_ALIASES[region] ?? region;
}

function matchesRegion(level: string, regionFilter: string) {
  if (!regionFilter) {
    return true;
  }

  return level.includes(regionFilter);
}

function parseCsv(text: string) {
  const [headerLine, ...lines] = text.trim().split(/\r?\n/);
  const headers = splitCsvLine(headerLine);

  return lines.map((line) => {
    const values = splitCsvLine(line);
    return Object.fromEntries(headers.map((header, index) => [header, values[index] ?? ""]));
  });
}

function splitCsvLine(line: string) {
  const values: string[] = [];
  let current = "";
  let inQuotes = false;

  for (let index = 0; index < line.length; index += 1) {
    const character = line[index];
    const next = line[index + 1];

    if (character === '"' && next === '"') {
      current += '"';
      index += 1;
    } else if (character === '"') {
      inQuotes = !inQuotes;
    } else if (character === "," && !inQuotes) {
      values.push(current);
      current = "";
    } else {
      current += character;
    }
  }

  values.push(current);
  return values;
}

function toHistoricalRecord(row: Record<string, string>) {
  if (!row.serial_number || !row.festival_name) {
    return null;
  }

  return {
    serialNumber: row.serial_number,
    level: row.administrative_level || "-",
    name: row.festival_name,
    dates: formatDateRange(row.opening_date, row.closing_date),
    visitors: Number(row.visitor_count || 0),
    notes: row.notes || "None"
  };
}

function normalizePrediction(payload: PredictionPayload) {
  return {
    expectedVisitorCount: payload.expected_visitor_count ?? 0,
    targetDurationDays: payload.target_duration_days ?? 0,
    confidence: payload.confidence ?? "unknown",
    method: payload.method ?? "No prediction has been generated yet.",
    basedOnRecords: (payload.based_on_records ?? []).map((record) => ({
      festivalName: record.festival_name,
      dates: formatDateRange(record.opening_date, record.closing_date),
      visitorCount: record.visitor_count,
      weight: record.weight
    }))
  };
}

function formatDateRange(openingDate: string, closingDate: string) {
  if (!openingDate && !closingDate) {
    return "-";
  }
  if (!closingDate || openingDate === closingDate) {
    return openingDate;
  }
  return `${openingDate} - ${closingDate}`;
}

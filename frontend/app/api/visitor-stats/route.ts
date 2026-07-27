import { NextRequest, NextResponse } from "next/server";
import { readFile } from "node:fs/promises";
import path from "node:path";

export const dynamic = "force-dynamic";

const REGION_ALIASES: Record<string, string> = {
  all: "전체",
  jeonju: "전주시",
  gunsan: "군산시",
  iksan: "익산시",
  namwon: "남원시"
};

const PERIOD_OPTIONS = new Set(["14", "30"]);

type VisitorRecord = {
  date: string;
  region: string;
  visitor_count: number;
  source_endpoint?: string;
  raw?: {
    touNum?: string;
    visitor_count?: string | number;
    visitorCount?: string | number;
    count?: string | number;
  };
};

type VisitorStatsPayload = {
  generated_at?: string;
  records?: VisitorRecord[];
};

type Summary = {
  region: string;
  cumulativeVisitors: number;
  growthRate: number;
  peakDate: string;
  peakVisitors: number;
  daily: Array<{
    date: string;
    visitorCount: number;
  }>;
};

const workspaceRoot = path.resolve(process.cwd(), "..");
const visitorStatsPath = path.join(workspaceRoot, "backend", "data", "processed", "jeonbuk_visitors_daily.json");

function resolveRegion(requestedRegion: string) {
  return REGION_ALIASES[requestedRegion] ?? requestedRegion;
}

function resolvePeriodDays(requestedPeriod: string | null) {
  if (requestedPeriod && PERIOD_OPTIONS.has(requestedPeriod)) {
    return Number(requestedPeriod);
  }
  return 14;
}

function normalizeCount(value: unknown) {
  if (typeof value === "number") {
    return Math.round(value);
  }

  if (typeof value === "string") {
    const parsed = Number.parseFloat(value.replace(/,/g, ""));
    return Number.isFinite(parsed) ? Math.round(parsed) : 0;
  }

  return 0;
}

function normalizeRecord(record: VisitorRecord) {
  const rawCount =
    record.raw?.touNum ??
    record.raw?.visitor_count ??
    record.raw?.visitorCount ??
    record.raw?.count ??
    record.visitor_count;

  return {
    ...record,
    visitor_count: normalizeCount(rawCount)
  };
}

function selectRegionRecords(records: VisitorRecord[], region: string) {
  const localRecords = records.filter((record) => record.source_endpoint !== "sample");

  if (region === "전체") {
    return localRecords.length > 0 ? localRecords : records;
  }

  const localRegionRecords = localRecords.filter((record) => record.region === region);
  if (localRegionRecords.length > 0) {
    return localRegionRecords;
  }

  return records.filter((record) => record.region === region);
}

function buildSummary(records: VisitorRecord[], region: string, requestedDays: number): { summary: Summary; monthKey: string } | null {
  const normalizedRecords = records.map(normalizeRecord);
  const regionRecords = selectRegionRecords(normalizedRecords, region);

  if (regionRecords.length === 0) {
    return null;
  }

  const sortedDates = [...new Set(regionRecords.map((record) => record.date))].sort();
  const windowDates = sortedDates.slice(-Math.min(requestedDays, sortedDates.length));
  const windowDateSet = new Set(windowDates);
  const latestDate = windowDates[windowDates.length - 1];
  const monthKey = latestDate.slice(0, 7);

  const dailyMap = new Map<string, number>();
  for (const record of regionRecords) {
    if (!windowDateSet.has(record.date)) {
      continue;
    }
    dailyMap.set(record.date, (dailyMap.get(record.date) ?? 0) + record.visitor_count);
  }

  const daily = windowDates.map((date) => ({
    date,
    visitorCount: dailyMap.get(date) ?? 0
  }));

  const monthlyVisitors = regionRecords
    .filter((record) => record.date.startsWith(monthKey))
    .reduce((sum, record) => sum + record.visitor_count, 0);

  const peak = daily.reduce(
    (current, row) => (row.visitorCount > current.visitorCount ? row : current),
    daily[0]
  );
  const midpoint = Math.max(Math.floor(daily.length / 2), 1);
  const firstHalf = daily.slice(0, midpoint);
  const secondHalf = daily.slice(midpoint);
  const firstAverage = average(firstHalf);
  const secondAverage = average(secondHalf.length > 0 ? secondHalf : firstHalf);
  const growthRate = firstAverage === 0 ? 0 : ((secondAverage - firstAverage) / firstAverage) * 100;

  return {
    monthKey,
    summary: {
      region,
      cumulativeVisitors: monthlyVisitors,
      growthRate,
      peakDate: peak.date,
      peakVisitors: peak.visitorCount,
      daily
    }
  };
}

function average(rows: Array<{ visitorCount: number }>) {
  if (rows.length === 0) {
    return 0;
  }
  return rows.reduce((sum, row) => sum + row.visitorCount, 0) / rows.length;
}

export async function GET(request: NextRequest) {
  try {
    const payload = JSON.parse(await readFile(visitorStatsPath, "utf-8")) as VisitorStatsPayload;
    const records = payload.records ?? [];
    const requestedRegion = resolveRegion(request.nextUrl.searchParams.get("region") ?? "전체");
    const requestedPeriod = request.nextUrl.searchParams.get("period");
    const periodDays = resolvePeriodDays(requestedPeriod);
    const result = buildSummary(records, requestedRegion, periodDays);

    if (!result) {
      return NextResponse.json(
        {
          success: false,
          error: {
            code: "VISITOR_REGION_NOT_FOUND",
            message: `No visitor summary exists for region: ${requestedRegion}`
          }
        },
        { status: 404 }
      );
    }

    return NextResponse.json({
      success: true,
      data: {
        region: requestedRegion,
        periodDays,
        windowDays: result.summary.daily.length,
        monthKey: result.monthKey,
        summary: result.summary
      },
      meta: {
        generatedAt: new Date().toISOString(),
        sourceUpdatedAt: payload.generated_at ?? null,
        source: "backend/data/processed/jeonbuk_visitors_daily.json"
      }
    });
  } catch (error) {
    return NextResponse.json(
      {
        success: false,
        error: {
          code: "VISITOR_STATS_NOT_READY",
          message: error instanceof Error ? error.message : "Visitor stats data is not ready."
        }
      },
      { status: 500 }
    );
  }
}

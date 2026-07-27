"use client";

import { useEffect, useState } from "react";

type VisitorStatsResponse = {
  success: boolean;
  data?: {
    region: string;
    periodDays: number;
    windowDays: number;
    monthKey: string;
    summary: {
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
  };
  error?: {
    message: string;
  };
};

export function VisitorStatsPanel({
  selectedRegion,
  selectedPeriod
}: {
  selectedRegion: string;
  selectedPeriod: string;
}) {
  const [state, setState] = useState<{
    status: "loading" | "ready" | "error";
    data?: VisitorStatsResponse["data"];
    message?: string;
  }>({ status: "loading" });

  useEffect(() => {
    let active = true;

    async function loadStats() {
      setState((current) => ({ ...current, status: "loading" }));

      try {
        const response = await fetch(
          `/api/visitor-stats?region=${encodeURIComponent(selectedRegion)}&period=${encodeURIComponent(selectedPeriod)}`,
          { cache: "no-store" }
        );
        const payload = (await response.json()) as VisitorStatsResponse;

        if (!active) {
          return;
        }

        if (!response.ok || !payload.success || !payload.data) {
          setState({
            status: "error",
            message: payload.error?.message ?? "방문객 통계 API를 불러오지 못했습니다."
          });
          return;
        }

        setState({ status: "ready", data: payload.data });
      } catch (error) {
        if (!active) {
          return;
        }
        setState({
          status: "error",
          message: error instanceof Error ? error.message : "방문객 통계 API를 불러오지 못했습니다."
        });
      }
    }

    void loadStats();

    return () => {
      active = false;
    };
  }, [selectedRegion, selectedPeriod]);

  const summary = state.data?.summary;
  const windowDays = state.data?.windowDays ?? summary?.daily.length ?? 0;
  const monthKey = state.data?.monthKey ?? "";
  const maxVisitors = Math.max(...(summary?.daily.map((row) => row.visitorCount) ?? [1]), 1);
  const periodLabel = selectedPeriod === "30" ? "최근 30일" : "최근 14일";
  const dailyTitle = `${selectedRegion} 최근 ${windowDays}일 일별 방문객 수`;

  return (
    <section className="visitor-stats-block">
      <div className="visitor-toolbar">
        <div>
          <span className="eyebrow">KTO DataLab</span>
          <h2>{selectedRegion} 방문객 현황</h2>
        </div>
      </div>

      {state.status === "error" ? <div className="api-state error">{state.message}</div> : null}

      {state.status !== "error" ? (
        <>
          <section className="metric-grid">
            <article className="metric-card">
              <div className="metric-topline">
                <span>방문객 증가율</span>
              </div>
              <strong>{formatPercent(summary?.growthRate ?? 0)}</strong>
              <p>{periodLabel} 기준 변화율입니다.</p>
            </article>
            <article className="metric-card">
              <div className="metric-topline">
                <span>월별 누적 방문객</span>
              </div>
              <strong>{formatNumber(summary?.cumulativeVisitors ?? 0)}</strong>
              <p>{monthKey ? `${monthKey} 기준` : "선택 월 기준"}</p>
            </article>
            <article className="metric-card">
              <div className="metric-topline">
                <span>최고 방문일</span>
              </div>
              <strong>{summary?.peakDate ?? "-"}</strong>
              <p>{formatNumber(summary?.peakVisitors ?? 0)}명 방문</p>
            </article>
            <article className="metric-card">
              <div className="metric-topline">
                <span>집계 일수</span>
              </div>
              <strong>{windowDays}일</strong>
              <p>{periodLabel} 중 실제 보유 데이터 기준</p>
            </article>
          </section>

          <section className="panel span-2 visitor-daily-panel">
            <div className="section-heading">
              <div>
                <span className="eyebrow">Daily Visitors</span>
                <h2>{dailyTitle}</h2>
              </div>
              <span className="panel-meta">해당 날짜 방문객 수</span>
            </div>
            <div className="visitor-daily-list">
              {(summary?.daily ?? []).map((row) => (
                <div className="visitor-daily-row" key={row.date}>
                  <span>{row.date}</span>
                  <div className="visitor-bar-track">
                    <div style={{ width: `${Math.max((row.visitorCount / maxVisitors) * 100, 2)}%` }} />
                  </div>
                  <strong>{formatNumber(row.visitorCount)}</strong>
                </div>
              ))}
            </div>
          </section>
        </>
      ) : null}
    </section>
  );
}

function formatNumber(value: number) {
  return new Intl.NumberFormat("ko-KR").format(value);
}

function formatPercent(value: number) {
  const prefix = value > 0 ? "+" : "";
  return `${prefix}${value.toFixed(1)}%`;
}

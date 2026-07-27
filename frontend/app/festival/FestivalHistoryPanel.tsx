"use client";

import { useEffect, useState } from "react";

type FestivalHistoryResponse = {
  success: boolean;
  data?: {
    region: string;
    records: HistoricalFestivalRecord[];
    prediction: {
      expectedVisitorCount: number;
      targetDurationDays: number;
      confidence: string;
      method: string;
      basedOnRecords: Array<{
        festivalName: string;
        dates: string;
        visitorCount: number;
        weight: number;
      }>;
    };
    totalCount: number;
  };
  error?: {
    message: string;
  };
};

type HistoricalFestivalRecord = {
  serialNumber: string;
  level: string;
  name: string;
  dates: string;
  visitors: number;
  notes: string;
};

const pipelineSteps = ["Load JSON/XML", "Translate columns", "Export CSV", "Predict visitors"];

export function FestivalHistoryPanel({ selectedRegion }: { selectedRegion: string }) {
  const [state, setState] = useState<{
    status: "loading" | "ready" | "error";
    data?: FestivalHistoryResponse["data"];
    message?: string;
  }>({ status: "loading" });

  useEffect(() => {
    let active = true;

    async function loadFestivalHistory() {
      setState((current) => ({ ...current, status: "loading" }));

      try {
        const response = await fetch(`/api/festival-history?region=${encodeURIComponent(selectedRegion)}`, {
          cache: "no-store"
        });
        const payload = (await response.json()) as FestivalHistoryResponse;

        if (!active) {
          return;
        }

        if (!response.ok || !payload.success || !payload.data) {
          setState({
            status: "error",
            message: payload.error?.message ?? "Festival history API failed."
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
          message: error instanceof Error ? error.message : "Festival history API failed."
        });
      }
    }

    void loadFestivalHistory();

    return () => {
      active = false;
    };
  }, [selectedRegion]);

  const records = state.data?.records.slice(0, 8) ?? [];
  const prediction = state.data?.prediction;
  const hasRecords = records.length > 0;

  return (
    <section className="panel span-2">
      <div className="section-heading">
        <div>
          <span className="eyebrow">Historical Data</span>
          <h2>{selectedRegion} 과거 축제 데이터</h2>
        </div>
        <span className="panel-meta">
          {state.status === "ready" ? `${state.data?.totalCount ?? 0} records` : "API"}
        </span>
      </div>

      <div className="pipeline-strip" aria-label="과거 축제 데이터 처리 단계">
        {pipelineSteps.map((step, index) => (
          <div className="pipeline-step" key={step}>
            <span>{index + 1}</span>
            <strong>{step}</strong>
          </div>
        ))}
      </div>

      {state.status === "loading" ? <div className="api-state">불러오는 중...</div> : null}
      {state.status === "error" ? <div className="api-state error">{state.message}</div> : null}

      {state.status === "ready" ? (
        hasRecords ? (
          <>
            <div className="historical-layout">
              <div className="import-dropzone">
                <span>JSON · XML · CSV</span>
                <strong>공공데이터포털 축제 데이터</strong>
                <p>선택한 지역의 과거 축제 데이터를 API로 불러와 운영본부 화면에 연결합니다.</p>
              </div>
              <div className="prediction-summary">
                <span>예상 방문객</span>
                <strong>{formatNumber(prediction?.expectedVisitorCount ?? 0)}명</strong>
                <p>
                  {prediction?.targetDurationDays ?? 0}일 기준 · confidence {prediction?.confidence ?? "unknown"}
                </p>
              </div>
            </div>

            <div className="historical-table" role="table" aria-label="과거 축제 CSV 미리보기">
              <div className="historical-row historical-head" role="row">
                <span>No.</span>
                <span>Level</span>
                <span>Festival</span>
                <span>Dates</span>
                <span>Visitors</span>
                <span>Notes</span>
              </div>
              {records.map((row) => (
                <div className="historical-row" role="row" key={`${row.serialNumber}-${row.name}`}>
                  <span>{row.serialNumber}</span>
                  <span>{row.level}</span>
                  <span>{row.name}</span>
                  <span>{row.dates}</span>
                  <span>{formatNumber(row.visitors)}</span>
                  <span>{row.notes}</span>
                </div>
              ))}
            </div>
          </>
        ) : (
          <div className="api-state">선택한 지역의 과거 축제 데이터가 없습니다.</div>
        )
      ) : null}
    </section>
  );
}

function formatNumber(value: number) {
  return new Intl.NumberFormat("ko-KR").format(value);
}

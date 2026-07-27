"use client";

import { useState } from "react";
import {
  AiInsightPanel,
  AppShell,
  FestivalList,
  PageHeader,
  SourcePanel
} from "../components";
import { FestivalHistoryPanel } from "./FestivalHistoryPanel";
import { VisitorStatsPanel } from "./VisitorStatsPanel";

const REGION_OPTIONS = [
  { value: "전체", label: "전체" },
  { value: "전주시", label: "전주시" },
  { value: "군산시", label: "군산시" },
  { value: "익산시", label: "익산시" },
  { value: "남원시", label: "남원시" }
];

const PERIOD_OPTIONS = [
  { value: "14", label: "최근 14일" },
  { value: "30", label: "최근 30일" }
];

export default function FestivalDashboardPage() {
  const [selectedRegion, setSelectedRegion] = useState("전체");
  const [selectedPeriod, setSelectedPeriod] = useState("14");

  return (
    <AppShell active="festival">
      <PageHeader
        eyebrow="Festival Office"
        title="축제 운영본부 리포트"
        description="축제 기간의 방문객 흐름과 지역별 축제 데이터를 한 화면에서 확인합니다."
        regionOptions={REGION_OPTIONS}
        selectedRegion={selectedRegion}
        onRegionChange={setSelectedRegion}
        periodOptions={PERIOD_OPTIONS}
        selectedPeriod={selectedPeriod}
        onPeriodChange={setSelectedPeriod}
      />

      <VisitorStatsPanel selectedRegion={selectedRegion} selectedPeriod={selectedPeriod} />

      <section className="content-grid">
        <FestivalHistoryPanel selectedRegion={selectedRegion} />
        <section className="panel">
          <div className="section-heading">
            <div>
              <span className="eyebrow">Performance</span>
              <h2>운영 성과</h2>
            </div>
          </div>
          <div className="report-preview">
            <div>
              <span>전년 대비</span>
              <strong>예상치 +42%</strong>
            </div>
            <div>
              <span>주요 유입 요인</span>
              <strong>공연, 체험, 먹거리</strong>
            </div>
            <div>
              <span>Export</span>
              <strong>CSV · Excel</strong>
            </div>
          </div>
        </section>
        <FestivalList />
        <AiInsightPanel detail="축제 기간 방문객 증가와 주말 유입이 겹치는 구간은 운영 인력과 동선 배치를 먼저 점검하는 편이 좋습니다." />
        <SourcePanel />
      </section>
    </AppShell>
  );
}

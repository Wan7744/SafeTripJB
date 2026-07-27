"use client";

import type { ChangeEvent } from "react";
import Link from "next/link";
import { festivals, sources, visitorTrend } from "./data";

type ShellProps = {
  active: "tourist" | "traffic" | "festival" | "admin";
  children: React.ReactNode;
};

type SelectOption = {
  value: string;
  label: string;
};

const navigation = [
  { key: "tourist", label: "관광객", href: "/" },
  { key: "traffic", label: "교통", href: "/traffic" },
  { key: "festival", label: "운영본부", href: "/festival" },
  { key: "admin", label: "관리자", href: "/admin" }
];

const defaultRegionOptions: SelectOption[] = [
  { value: "전체", label: "전체" },
  { value: "전주시", label: "전주시" },
  { value: "군산시", label: "군산시" },
  { value: "익산시", label: "익산시" },
  { value: "남원시", label: "남원시" }
];

export function AppShell({ active, children }: ShellProps) {
  return (
    <main className="app-shell">
      <aside className="sidebar">
        <div className="brand">
          <div className="brand-mark">S</div>
          <div>
            <strong>SafeTrip JB</strong>
            <span>Visitor Intelligence</span>
          </div>
        </div>
        <nav className="nav-list" aria-label="사용자 그룹">
          {navigation.map((item) => (
            <Link
              className={item.key === active ? "nav-item active" : "nav-item"}
              href={item.href}
              key={item.key}
            >
              {item.label}
            </Link>
          ))}
        </nav>
        <div className="side-note">
          <span>기준일</span>
          <strong>2026.07.27</strong>
        </div>
      </aside>
      <section className="workspace">{children}</section>
    </main>
  );
}

export function PageHeader({
  eyebrow,
  title,
  description,
  regionOptions = defaultRegionOptions,
  selectedRegion = "전체",
  onRegionChange,
  periodOptions = [
    { value: "14", label: "최근 14일" },
    { value: "30", label: "최근 30일" }
  ],
  selectedPeriod = "14",
  onPeriodChange
}: {
  eyebrow: string;
  title: string;
  description: string;
  regionOptions?: SelectOption[];
  selectedRegion?: string;
  onRegionChange?: (region: string) => void;
  periodOptions?: SelectOption[];
  selectedPeriod?: string;
  onPeriodChange?: (period: string) => void;
}) {
  const regionSelectProps = onRegionChange
    ? {
        value: selectedRegion,
        onChange: (event: ChangeEvent<HTMLSelectElement>) => onRegionChange(event.target.value)
      }
    : {
        defaultValue: selectedRegion
      };

  const periodSelectProps = onPeriodChange
    ? {
        value: selectedPeriod,
        onChange: (event: ChangeEvent<HTMLSelectElement>) => onPeriodChange(event.target.value)
      }
    : {
        defaultValue: selectedPeriod
      };

  return (
    <header className="page-header">
      <div>
        <span className="eyebrow">{eyebrow}</span>
        <h1>{title}</h1>
        <p>{description}</p>
      </div>
      <div className="header-actions" aria-label="대시보드 필터">
        <select aria-label="지역 선택" {...regionSelectProps}>
          {regionOptions.map((region) => (
            <option key={region.value} value={region.value}>
              {region.label}
            </option>
          ))}
        </select>
        <select aria-label="기간 선택" {...periodSelectProps}>
          {periodOptions.map((period) => (
            <option key={period.value} value={period.value}>
              {period.label}
            </option>
          ))}
        </select>
      </div>
    </header>
  );
}

export function MetricCard({
  label,
  value,
  detail,
  status
}: {
  label: string;
  value: string;
  detail: string;
  status?: "safe" | "normal" | "caution" | "crowded";
}) {
  return (
    <article className="metric-card">
      <div className="metric-topline">
        <span>{label}</span>
        {status ? <StatusBadge status={status} /> : null}
      </div>
      <strong>{value}</strong>
      <p>{detail}</p>
    </article>
  );
}

export function StatusBadge({
  status
}: {
  status: "safe" | "normal" | "caution" | "crowded";
}) {
  const labels = {
    safe: "안전",
    normal: "보통",
    caution: "주의",
    crowded: "혼잡"
  };

  return <span className={`status ${status}`}>{labels[status]}</span>;
}

export function TrendPanel() {
  return (
    <section className="panel span-2">
      <div className="section-heading">
        <div>
          <span className="eyebrow">Visitor Trend</span>
          <h2>최근 14일 방문객 추이</h2>
        </div>
        <span className="panel-meta">단위: 천 명</span>
      </div>
      <div className="bar-chart" aria-label="최근 14일 방문객 추이 그래프 묶음">
        {visitorTrend.map((item) => (
          <div className="bar-item" key={item.day}>
            <div className="bar-track">
              <span style={{ height: `${item.value}%` }} />
            </div>
            <small>{item.day}</small>
          </div>
        ))}
      </div>
    </section>
  );
}

export function FestivalList() {
  return (
    <section className="panel">
      <div className="section-heading">
        <div>
          <span className="eyebrow">Festival</span>
          <h2>진행 및 예정 축제</h2>
        </div>
      </div>
      <div className="list-stack">
        {festivals.map((festival) => (
          <article className="list-card" key={festival.name}>
            <div>
              <strong>{festival.name}</strong>
              <span>
                {festival.region} · {festival.period}
              </span>
            </div>
            <b>{festival.growth}</b>
          </article>
        ))}
      </div>
    </section>
  );
}

export function MapPanel() {
  return (
    <section className="panel map-panel">
      <div className="section-heading">
        <div>
          <span className="eyebrow">Map</span>
          <h2>전북 지역 혼잡 분포</h2>
        </div>
      </div>
      <div className="map-canvas" aria-label="지역 권역 묶음">
        <span className="map-pin pin-a">전주</span>
        <span className="map-pin pin-b">군산</span>
        <span className="map-pin pin-c">익산</span>
        <span className="map-pin pin-d">남원</span>
      </div>
    </section>
  );
}

export function AiInsightPanel({
  detail = "주말 방문객 증가와 축제 일정이 겹치는 구간은 혼잡이 빠르게 높아질 수 있습니다."
}) {
  return (
    <section className="panel">
      <div className="section-heading">
        <div>
          <span className="eyebrow">AI Insight</span>
          <h2>방문객 증가 경향</h2>
        </div>
      </div>
      <p className="insight-text">{detail}</p>
      <div className="factor-row">
        <span>주말</span>
        <span>축제</span>
        <span>날씨</span>
      </div>
    </section>
  );
}

export function SourcePanel() {
  return (
    <section className="panel">
      <div className="section-heading">
        <div>
          <span className="eyebrow">Source</span>
          <h2>데이터 출처</h2>
        </div>
      </div>
      <div className="source-grid">
        {sources.map((source) => (
          <article className="source-item" key={source.label}>
            <span>{source.label}</span>
            <strong>{source.provider}</strong>
            <small>{source.updated}</small>
          </article>
        ))}
      </div>
    </section>
  );
}

export function EmptyState({
  title,
  text
}: {
  title: string;
  text: string;
}) {
  return (
    <section className="empty-state">
      <strong>{title}</strong>
      <p>{text}</p>
    </section>
  );
}

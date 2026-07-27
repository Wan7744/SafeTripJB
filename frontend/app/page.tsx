import {
  AiInsightPanel,
  AppShell,
  FestivalList,
  MapPanel,
  MetricCard,
  PageHeader,
  SourcePanel,
  TrendPanel
} from "./components";

export default function TouristDashboardPage() {
  return (
    <AppShell active="tourist">
      <PageHeader
        eyebrow="Tourist Dashboard"
        title="전주시 방문 현황"
        description="지역 포화상태, 축제 일정, 방문객 변화, AI 요약을 한 화면에서 확인합니다."
      />

      <section className="metric-grid" aria-label="지역 주요 지표">
        <MetricCard label="현재 방문객" value="68,240명" detail="최근 14일 평균 대비 +18.4%" />
        <MetricCard label="지역 포화상태" value="주의" detail="한옥마을 권역 중심 상승" status="caution" />
        <MetricCard label="진행 축제" value="3건" detail="오늘 기준 진행 및 예정 포함" />
        <MetricCard label="음식점 대기지수" value="0.78" detail="주요 관광권역 평균" status="caution" />
      </section>

      <section className="content-grid">
        <TrendPanel />
        <MapPanel />
        <FestivalList />
        <AiInsightPanel />
        <SourcePanel />
      </section>
    </AppShell>
  );
}

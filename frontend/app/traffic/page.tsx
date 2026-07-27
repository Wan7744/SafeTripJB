import {
  AiInsightPanel,
  AppShell,
  MapPanel,
  MetricCard,
  PageHeader,
  SourcePanel,
  StatusBadge,
  TrendPanel
} from "../components";
import { congestionRows } from "../data";

export default function TrafficDashboardPage() {
  return (
    <AppShell active="traffic">
      <PageHeader
        eyebrow="Traffic Authority"
        title="혼잡 모니터링"
        description="교통기관과 경찰이 권역별 혼잡 수준과 급변 구간을 빠르게 확인하는 화면입니다."
      />

      <section className="metric-grid" aria-label="교통기관 주요 지표">
        <MetricCard label="교통 혼잡" value="주의" detail="객리단길 진입로 지연" status="caution" />
        <MetricCard label="관광지 혼잡" value="혼잡" detail="한옥마을 체류 밀도 상승" status="crowded" />
        <MetricCard label="혼잡 권역" value="2곳" detail="전주, 남원 집중" />
        <MetricCard label="예상 피크" value="18:00" detail="축제 야간 프로그램 전후" />
      </section>

      <section className="content-grid">
        <section className="panel span-2">
          <div className="section-heading">
            <div>
              <span className="eyebrow">Congestion</span>
              <h2>권역별 혼잡 상세</h2>
            </div>
          </div>
          <div className="table-like" role="table" aria-label="권역별 혼잡 상세 목업">
            <div className="table-row table-head" role="row">
              <span>권역</span>
              <span>교통</span>
              <span>관광지</span>
              <span>대기지수</span>
            </div>
            {congestionRows.map((row) => (
              <div className="table-row" role="row" key={row.area}>
                <span>{row.area}</span>
                <span>{row.traffic}</span>
                <span>{row.spot}</span>
                <span>{row.food}</span>
              </div>
            ))}
          </div>
        </section>
        <MapPanel />
        <TrendPanel />
        <section className="panel">
          <div className="section-heading">
            <div>
              <span className="eyebrow">Saturation</span>
              <h2>포화상태 범례</h2>
            </div>
          </div>
          <div className="legend-grid">
            <StatusBadge status="safe" />
            <StatusBadge status="normal" />
            <StatusBadge status="caution" />
            <StatusBadge status="crowded" />
          </div>
        </section>
        <AiInsightPanel detail="주요 도로의 유입량은 증가했지만 우회 가능 구간이 남아 있어, 축제 종료 시간대 전후 집중 관리가 필요합니다." />
        <SourcePanel />
      </section>
    </AppShell>
  );
}

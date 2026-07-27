import { AppShell, EmptyState, MetricCard, PageHeader, SourcePanel } from "../components";

const adminItems = [
  "지역 마스터 데이터",
  "축제 데이터",
  "외부 제공기관",
  "기관 계정",
  "권한 정책",
  "API 사용량"
];

export default function AdminDashboardPage() {
  return (
    <AppShell active="admin">
      <PageHeader
        eyebrow="Admin"
        title="관리자 워크스페이스"
        description="데이터 제공기관, 권한, 운영 상태를 관리하는 보호 라우트 화면입니다."
      />

      <section className="metric-grid" aria-label="관리자 주요 지표">
        <MetricCard label="외부 연동" value="3개" detail="관광공사, 기상청, 공공데이터포털" />
        <MetricCard label="기관 계정" value="12개" detail="교통기관 및 운영본부" />
        <MetricCard label="API 상태" value="정상" detail="최근 1시간 오류 없음" status="safe" />
        <MetricCard label="요청 한도" value="60/300" detail="Public/기관 req per min" />
      </section>

      <section className="content-grid">
        <section className="panel span-2">
          <div className="section-heading">
            <div>
              <span className="eyebrow">Management</span>
              <h2>관리 항목</h2>
            </div>
          </div>
          <div className="admin-grid">
            {adminItems.map((item) => (
              <article className="admin-card" key={item}>
                <strong>{item}</strong>
                <span>조회 · 수정 · 이력</span>
              </article>
            ))}
          </div>
        </section>
        <SourcePanel />
        <EmptyState
          title="운영 알림"
          text="외부 데이터 실패, Rate Limit 초과, 배치 지연 알림이 이 영역에 표시됩니다."
        />
      </section>
    </AppShell>
  );
}

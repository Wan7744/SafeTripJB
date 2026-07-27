# SafeTrip JB Frontend

SafeTrip JB PRD 체크리스트의 웹 프론트엔드 항목을 기준으로 만든 정적 화면 골격입니다. 현재는 API 호출, 인증, 상태 관리, 지도 SDK, 차트 라이브러리 연결 없이 페이지 레이아웃과 정보 구조만 포함합니다.

## Pages

- `/`: 관광객 대시보드
- `/traffic`: 교통기관/경찰 혼잡 모니터링
- `/festival`: 축제 운영본부 리포트
- `/admin`: 관리자 워크스페이스

## Run

```bash
npm install
npm run dev
```

## Checklist Coverage

- Next.js 프로젝트 구조
- 상태 색상 토큰: 안전, 보통, 주의, 혼잡
- 지역 선택, 기간 선택 UI
- 지역 현황 카드
- 최근 14일 방문객 추이 그래프 자리
- 축제 목록
- 혼잡 지수 및 포화상태 카드
- 지도 영역 자리
- AI 원인 분석 패널
- 데이터 출처 및 갱신일 표시
- 사용자 그룹별 화면 분기

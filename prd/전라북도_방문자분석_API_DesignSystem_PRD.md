# 전라북도 방문자 분석 API — Design System PRD

**문서 버전**: v0.1 (Draft)
**작성일**: 2026-07-21
**관련 서비스**: SafeTrip JB
**작성 목적**: SafeTrip JB 서비스가 소비하는 "전라북도 방문자 분석 API"의 설계 원칙, 리소스 구조, 요청/응답 규격, 에러 처리 기준을 정의하여 프론트엔드·백엔드·데이터 제공기관 간 일관된 개발 기준을 제공한다.

---

## 1. 문서 개요

### 1.1 배경
SafeTrip JB는 전북특별자치도 시·군별 방문객 수, 축제 일정, 날씨, 요일/공휴일 데이터를 결합해 지역별 혼잡도와 방문객 변화를 분석하는 서비스다. 이 서비스의 핵심 데이터 계층을 담당하는 것이 "전라북도 방문자 분석 API"이며, 관광객·교통기관·축제 운영본부라는 세 종류의 사용자가 서로 다른 화면에서 동일한 API를 소비한다.

이 문서는 해당 API를 설계·개발할 때 지켜야 할 **디자인 시스템(설계 규칙 집합)**을 정의한다. 여기서 "Design System"은 UI 컴포넌트가 아니라, API의 네이밍·구조·응답 포맷·에러 체계 등 **API 자체의 일관된 설계 언어**를 의미한다.

### 1.2 목적
- 여러 개발자가 API를 설계하더라도 동일한 규칙을 따르도록 표준화한다.
- 관광객용/교통기관용/축제 운영본부용 화면이 동일한 리소스를 재사용할 수 있도록 리소스 구조를 통일한다.
- AI 분석 결과와 데이터 출처를 함께 제공해야 하는 요구사항(신뢰성 확보)을 API 응답 규격에 반영한다.

### 1.3 범위
- 포함: REST API 설계 원칙, 리소스/엔드포인트 정의, 공통 요청/응답 포맷, 에러 코드 체계, 페이지네이션·필터링, 버저닝, 인증
- 제외: 프론트엔드 UI 컴포넌트 디자인, 인프라/배포 아키텍처, 데이터 수집 파이프라인 상세 설계

### 1.4 대상 독자
백엔드 개발자, 프론트엔드 개발자, 데이터 엔지니어, QA

---

## 2. API 설계 원칙

| 원칙 | 설명 |
|---|---|
| 일관성 (Consistency) | 모든 엔드포인트는 동일한 네이밍·응답 포맷·에러 구조를 따른다. |
| 예측 가능성 (Predictability) | 리소스 URL만 보고도 어떤 데이터가 반환될지 유추 가능해야 한다. |
| 사용자 관점 우선 | 관광객/교통기관/축제 운영본부 세 사용자 시나리오에서 실제로 필요한 데이터 단위로 리소스를 나눈다. |
| 투명성 (Traceability) | 방문객 수·축제·기상 데이터는 반드시 출처(source), 기준일(reference_date), 갱신일(updated_at)을 함께 반환한다. |
| 추정값 명시 | 혼잡 지수 등 실측이 아닌 예측값은 응답에 `is_estimated: true`로 명시한다. |

---

## 3. 네이밍 규칙

- 리소스명은 **복수형 명사**, 소문자, 하이픈(`-`) 구분을 사용한다. 예: `/regions`, `/festivals`, `/congestion-index`
- 경로 파라미터는 `{snake_case}` 형태로 표기한다. 예: `/regions/{region_id}/visitors`
- 쿼리 파라미터는 `snake_case`를 사용한다. 예: `?start_date=2026-07-01&end_date=2026-07-14`
- 응답 필드(JSON key)도 `snake_case`로 통일한다.
- 지역 식별자는 행정표준코드(법정동코드 기반)를 `region_id`로 사용하고, 지역명(`region_name`)은 함께 제공하되 식별 기준으로 사용하지 않는다.

---

## 4. 버전 관리

- URL 경로에 메이저 버전을 명시한다: `https://api.safetrip-jb.kr/v1/...`
- 하위 호환이 깨지는 변경(필드 삭제, 타입 변경 등)은 메이저 버전을 올린다.
- 필드 추가 등 하위 호환 변경은 버전을 올리지 않고 `changelog.md`에만 기록한다.

---

## 5. 인증 및 접근 제어

| 사용자 그룹 | 인증 방식 | 접근 범위 |
|---|---|---|
| 일반 방문객(웹/앱) | API Key (Public, Read-only) | 지역 현황, 혼잡 지수, AI 분석 결과 조회 |
| 교통기관/경찰 | OAuth 2.0 (기관 계정) | 위 항목 + 상세 통계, 과거 축제 비교 데이터 |
| 축제 운영본부 | OAuth 2.0 (기관 계정) | 위 항목 + 담당 축제 성과 리포트, 원시 데이터 export |
| 내부 관리자 | OAuth 2.0 + Role: admin | 전체 CRUD, 데이터 제공기관 연동 관리 |

- 모든 요청은 `Authorization: Bearer {token}` 헤더를 사용한다.
- Public Key는 초당 요청 수 제한(Rate Limit)을 적용한다.

---

## 6. 공통 요청/응답 포맷

### 6.1 공통 헤더
| 헤더 | 필수 | 설명 |
|---|---|---|
| `Authorization` | Y | Bearer 토큰 |
| `Accept-Language` | N | 기본값 `ko-KR` |
| `X-Request-Id` | N | 요청 추적용 UUID |

### 6.2 공통 응답 Envelope
모든 성공 응답은 다음 구조를 따른다.

```json
{
  "success": true,
  "data": { },
  "meta": {
    "request_id": "string",
    "generated_at": "2026-07-21T09:00:00+09:00"
  }
}
```

### 6.3 데이터 출처 공통 필드
방문객 수, 축제, 기상 등 외부 데이터를 포함하는 응답에는 아래 `source` 객체를 항상 포함한다.

```json
"source": {
  "provider": "한국관광공사",
  "reference_date": "2026-07-20",
  "updated_at": "2026-07-21T06:00:00+09:00",
  "is_estimated": false
}
```

---

## 7. 페이지네이션 · 정렬 · 필터링

- 목록 조회는 커서 기반 페이지네이션을 사용한다.
  - 쿼리: `?limit=20&cursor={cursor_token}`
  - 응답: `"pagination": { "next_cursor": "string", "has_more": true }`
- 정렬: `?sort=visitor_count&order=desc`
- 기간 필터: `?start_date=YYYY-MM-DD&end_date=YYYY-MM-DD` (기본 14일)
- 지역 필터: `?region_id={id}` (다중 선택 시 콤마 구분)

---

## 8. 주요 리소스 및 엔드포인트 정의

### 8.1 지역 (Regions)
| 메서드 | 엔드포인트 | 설명 |
|---|---|---|
| GET | `/v1/regions` | 전북특별자치도 시·군 목록 조회 |
| GET | `/v1/regions/{region_id}` | 특정 지역 상세 정보 조회 |
| GET | `/v1/regions/{region_id}/dashboard` | 현재 방문객 수준·진행 축제·포화상태 통합 조회 (지역 현황 대시보드용) |

### 8.2 방문객 추이 (Visitor Trends)
| 메서드 | 엔드포인트 | 설명 |
|---|---|---|
| GET | `/v1/regions/{region_id}/visitors` | 최근 N일(기본 14일) 일별 방문객 수 추이 |
| GET | `/v1/regions/{region_id}/visitors/compare` | 평상시 대비 축제 기간 방문객 수 비교 |

**응답 예시 (`/v1/regions/{region_id}/visitors`)**
```json
{
  "success": true,
  "data": {
    "region_id": "45210",
    "region_name": "전주시",
    "daily_visitors": [
      { "date": "2026-07-07", "visitor_count": 42000, "is_festival_day": false },
      { "date": "2026-07-08", "visitor_count": 68000, "is_festival_day": true }
    ]
  },
  "source": {
    "provider": "공공데이터포털",
    "reference_date": "2026-07-20",
    "updated_at": "2026-07-21T06:00:00+09:00",
    "is_estimated": false
  }
}
```

### 8.3 축제 (Festivals)
| 메서드 | 엔드포인트 | 설명 |
|---|---|---|
| GET | `/v1/regions/{region_id}/festivals` | 진행 중/예정 축제 목록 |
| GET | `/v1/festivals/{festival_id}` | 축제 상세 정보 |
| GET | `/v1/festivals/{festival_id}/performance` | 축제 전후 방문객 증가율, 흥행 성과 분석 (운영본부용) |
| GET | `/v1/festivals/compare` | 여러 축제 간 방문객 증가율·흥행 성과 비교 |

### 8.4 혼잡 지수 (Congestion Index)
| 메서드 | 엔드포인트 | 설명 |
|---|---|---|
| GET | `/v1/regions/{region_id}/congestion-index` | 교통 혼잡 지수, 관광지 혼잡 지수, 음식점 대기 지수 |
| GET | `/v1/regions/{region_id}/saturation` | 지역 포화상태 (안전/보통/주의/혼잡 4단계) |

**응답 예시**
```json
{
  "success": true,
  "data": {
    "region_id": "45210",
    "traffic_congestion_level": "주의",
    "tourist_spot_congestion_level": "혼잡",
    "restaurant_wait_index": 0.78,
    "saturation_status": "주의"
  },
  "source": {
    "provider": "SafeTrip JB 자체 추정 모델",
    "reference_date": "2026-07-21",
    "updated_at": "2026-07-21T08:00:00+09:00",
    "is_estimated": true
  }
}
```

### 8.5 AI 원인 분석 (AI Insights)
| 메서드 | 엔드포인트 | 설명 |
|---|---|---|
| GET | `/v1/regions/{region_id}/ai-insights` | 방문객 증감 원인에 대한 AI 분석 텍스트 및 근거 데이터 |

**응답 예시**
```json
{
  "success": true,
  "data": {
    "region_id": "45210",
    "summary": "현재 전주시의 방문객 수는 최근 14일 평균보다 증가한 상태입니다. 주요 원인으로는 주말과 지역 축제 개최가 동시에 겹친 점이 확인됩니다.",
    "contributing_factors": [
      { "factor": "weekend", "impact": "high" },
      { "factor": "festival", "impact": "high" },
      { "factor": "weather", "impact": "medium" }
    ],
    "based_on_sources": ["visitor_count", "festival_schedule", "weather"]
  }
}
```

### 8.6 데이터 출처 (Data Sources)
| 메서드 | 엔드포인트 | 설명 |
|---|---|---|
| GET | `/v1/data-sources` | 서비스에서 사용하는 전체 데이터 제공기관, 갱신 주기 목록 |

---

## 9. 에러 처리 표준

### 9.1 에러 응답 포맷
```json
{
  "success": false,
  "error": {
    "code": "REGION_NOT_FOUND",
    "message": "요청한 지역 정보를 찾을 수 없습니다.",
    "status": 404
  },
  "meta": {
    "request_id": "string",
    "generated_at": "2026-07-21T09:00:00+09:00"
  }
}
```

### 9.2 공통 에러 코드
| HTTP Status | error.code | 설명 |
|---|---|---|
| 400 | `INVALID_PARAMETER` | 요청 파라미터 형식 오류 |
| 401 | `UNAUTHORIZED` | 인증 실패 |
| 403 | `FORBIDDEN` | 권한 부족 (예: 운영본부 전용 리소스 접근) |
| 404 | `REGION_NOT_FOUND` / `FESTIVAL_NOT_FOUND` | 리소스 없음 |
| 409 | `DATA_NOT_READY` | 원본 데이터 미갱신으로 분석 불가 |
| 429 | `RATE_LIMIT_EXCEEDED` | 요청 한도 초과 |
| 500 | `INTERNAL_SERVER_ERROR` | 서버 오류 |
| 503 | `EXTERNAL_SOURCE_UNAVAILABLE` | 외부 데이터 제공기관(기상청 등) 응답 실패 |

---

## 10. 데이터 모델 요약

### Region
| 필드 | 타입 | 설명 |
|---|---|---|
| region_id | string | 행정표준코드 |
| region_name | string | 지역명 |
| saturation_status | enum(`안전`,`보통`,`주의`,`혼잡`) | 현재 포화상태 |

### Festival
| 필드 | 타입 | 설명 |
|---|---|---|
| festival_id | string | 축제 고유 ID |
| name | string | 축제명 |
| region_id | string | 개최 지역 |
| start_date / end_date | date | 개최 기간 |
| visitor_growth_rate | float | 평상시 대비 증가율 |

### VisitorTrend
| 필드 | 타입 | 설명 |
|---|---|---|
| date | date | 기준일 |
| visitor_count | integer | 방문객 수 |
| is_festival_day | boolean | 축제 개최일 여부 |

### CongestionIndex
| 필드 | 타입 | 설명 |
|---|---|---|
| traffic_congestion_level | enum | 교통 혼잡 수준 |
| tourist_spot_congestion_level | enum | 관광지 혼잡 수준 |
| restaurant_wait_index | float(0~1) | 음식점 대기 지수 |
| is_estimated | boolean | 추정값 여부 |

---

## 11. Rate Limiting

| 등급 | 제한 |
|---|---|
| Public API Key | 60 req/min |
| 기관 OAuth 계정 | 300 req/min |
| 관리자 | 무제한 (내부망 한정) |

한도 초과 시 `429 RATE_LIMIT_EXCEEDED`와 함께 `Retry-After` 헤더를 반환한다.

---

## 12. 로깅 및 모니터링 기준

- 모든 요청은 `request_id`, 호출 사용자 그룹(관광객/교통기관/운영본부/관리자), 응답 시간, 상태 코드를 로깅한다.
- 외부 데이터 제공기관(한국관광공사, 기상청, 공공데이터포털) 응답 실패율을 모니터링하며, 실패율이 임계치를 초과하면 `EXTERNAL_SOURCE_UNAVAILABLE` 알림을 발송한다.
- AI 분석 응답의 근거 데이터 누락 여부를 별도 검증 로그로 관리하여 신뢰성 요구사항을 충족한다.

---

## 13. 향후 확장 고려사항

- 다국어 지원: `Accept-Language` 헤더 기반 응답 로컬라이제이션 (영어/중국어/일본어)
- Webhook: 지역 포화상태가 '혼잡' 단계로 전환될 때 교통기관에 실시간 알림 발송
- Batch export API: 축제 운영본부용 성과 리포트 대량 다운로드(CSV/Excel)

---

## 14. 변경 이력

| 버전 | 일자 | 변경 내용 |
|---|---|---|
| v0.1 | 2026-07-21 | 최초 초안 작성 |

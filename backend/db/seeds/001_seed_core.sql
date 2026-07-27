INSERT INTO regions (region_id, region_name, parent_region_id, saturation_status)
VALUES
  ('jeonbuk', '전북특별자치도', NULL, 'normal'),
  ('jeonju', '전주시', 'jeonbuk', 'normal'),
  ('gunsan', '군산시', 'jeonbuk', 'normal'),
  ('iksan', '익산시', 'jeonbuk', 'safe'),
  ('namwon', '남원시', 'jeonbuk', 'normal'),
  ('gimje', '김제시', 'jeonbuk', 'safe'),
  ('jeongeup', '정읍시', 'jeonbuk', 'safe'),
  ('wanju', '완주군', 'jeonbuk', 'safe'),
  ('jinan', '진안군', 'jeonbuk', 'safe'),
  ('muju', '무주군', 'jeonbuk', 'safe'),
  ('jangsu', '장수군', 'jeonbuk', 'safe'),
  ('imsil', '임실군', 'jeonbuk', 'safe'),
  ('sunchang', '순창군', 'jeonbuk', 'safe'),
  ('gochang', '고창군', 'jeonbuk', 'safe'),
  ('buan', '부안군', 'jeonbuk', 'safe')
ON CONFLICT (region_id) DO UPDATE
SET region_name = EXCLUDED.region_name,
    parent_region_id = EXCLUDED.parent_region_id,
    saturation_status = EXCLUDED.saturation_status,
    updated_at = now();

INSERT INTO roles (role_id, role_name, description)
VALUES
  ('tourist', '관광객', '지역 현황과 축제 정보를 조회하는 일반 사용자'),
  ('traffic_agency', '교통기관/경찰', '혼잡 지수와 상세 모니터링 정보를 조회하는 기관 사용자'),
  ('festival_operator', '축제 운영본부', '축제 성과 리포트와 원시 데이터 export에 접근하는 운영 사용자'),
  ('admin', '내부 관리자', '마스터 데이터와 외부 연동 설정을 관리하는 관리자')
ON CONFLICT (role_id) DO UPDATE
SET role_name = EXCLUDED.role_name,
    description = EXCLUDED.description;

INSERT INTO data_sources (
  source_id,
  provider,
  dataset_name,
  endpoint,
  reference_date,
  is_estimated,
  raw_storage_path,
  processed_storage_path
)
VALUES
  (
    'kto-datalab-visitors',
    '한국관광공사',
    '빅데이터 지역별 방문자수 GW',
    'https://apis.data.go.kr/B551011/DataLabService',
    CURRENT_DATE,
    false,
    'data/raw/kto/visitors/{yyyy}/{mm}/{dd}/response.json',
    'data/processed/jeonbuk_visitors_daily.json'
  ),
  (
    'odcloud-historical-festivals',
    '공공데이터포털',
    '전라북도 지역축제 관광객현황',
    'https://api.odcloud.kr/api/15055596/v1/uddi:54ab775e-8d6b-4e86-acbb-d6841dee1013',
    CURRENT_DATE,
    false,
    'data/raw/odcloud/festivals/{yyyy}/{mm}/{dd}/response.json',
    'data/processed/historical_festivals_en.csv'
  ),
  (
    'kma-weather',
    '기상청',
    '단기예보/관측 기반 날씨',
    NULL,
    CURRENT_DATE,
    true,
    'data/raw/kma/weather/{yyyy}/{mm}/{dd}/response.json',
    'data/processed/weather_daily.json'
  )
ON CONFLICT (source_id) DO UPDATE
SET provider = EXCLUDED.provider,
    dataset_name = EXCLUDED.dataset_name,
    endpoint = EXCLUDED.endpoint,
    reference_date = EXCLUDED.reference_date,
    is_estimated = EXCLUDED.is_estimated,
    raw_storage_path = EXCLUDED.raw_storage_path,
    processed_storage_path = EXCLUDED.processed_storage_path,
    updated_at = now();

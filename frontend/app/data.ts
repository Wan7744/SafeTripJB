export const regions = [
  { name: "전주시", status: "주의", visitors: "68,240", change: "+18.4%" },
  { name: "군산시", status: "보통", visitors: "41,980", change: "+6.2%" },
  { name: "익산시", status: "안전", visitors: "32,410", change: "-2.1%" },
  { name: "남원시", status: "혼잡", visitors: "27,300", change: "+31.7%" }
];

export const visitorTrend = [
  { day: "07.14", value: 46 },
  { day: "07.15", value: 52 },
  { day: "07.16", value: 49 },
  { day: "07.17", value: 58 },
  { day: "07.18", value: 72 },
  { day: "07.19", value: 86 },
  { day: "07.20", value: 76 },
  { day: "07.21", value: 68 },
  { day: "07.22", value: 61 },
  { day: "07.23", value: 66 },
  { day: "07.24", value: 74 },
  { day: "07.25", value: 89 },
  { day: "07.26", value: 94 },
  { day: "07.27", value: 82 }
];

export const festivals = [
  {
    name: "전주 문화의 밤",
    region: "전주시",
    period: "07.25 - 07.30",
    growth: "+42%"
  },
  {
    name: "군산 선유도 축제",
    region: "군산시",
    period: "07.26 - 08.02",
    growth: "+21%"
  },
  {
    name: "익산 경관조명 축제",
    region: "익산시",
    period: "07.27 - 08.04",
    growth: "+36%"
  }
];

export const sources = [
  { label: "방문객", provider: "한국관광공사", updated: "2026-07-27 06:00" },
  { label: "기상", provider: "기상청", updated: "2026-07-27 08:00" },
  { label: "축제", provider: "공공데이터포털", updated: "2026-07-26 22:00" }
];

export const congestionRows = [
  { area: "전주시 도심권", traffic: "주의", spot: "혼잡", food: "0.78" },
  { area: "군산시 해안권", traffic: "보통", spot: "주의", food: "0.54" },
  { area: "익산시 역사권", traffic: "안전", spot: "보통", food: "0.31" },
  { area: "남원시 관광권", traffic: "혼잡", spot: "혼잡", food: "0.86" }
];

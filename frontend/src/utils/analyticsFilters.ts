import type { DashboardPayload } from '../types/dataset';
export function matchesHsSelection(row: { hs8_code?: string; hs4_code?: string }, codes: string[]) {
  return codes.length === 0 || codes.some(code => code.length === 8 ? row.hs8_code === code : row.hs4_code === code);
}
export function allowedYears(data: DashboardPayload): number[] {
  const years = new Set<number>(data.available_years || []);
  if (!years.size) for (const chart of data.level1_charts || []) {
    for (const row of chart.data || []) {
      const month = row.yyyy_mm || row.name;
      if (typeof month === 'string' && /^\d{4}-\d{2}$/.test(month)) years.add(Number(month.slice(0, 4)));
    }
  }
  const start = data.publication?.start_month || data.begin_date;
  const end = data.publication?.end_month || data.end_date;
  return [...years].filter(year => Number.isInteger(year) && (!start || year >= Number(start.slice(0, 4))) && (!end || year <= Number(end.slice(0, 4)))).sort((a, b) => a - b);
}

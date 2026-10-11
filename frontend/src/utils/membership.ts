import type { Currency, Payment } from '../types/membership';
export function money(amount: string, currency: Currency) {
  return new Intl.NumberFormat('en-US', { style: 'currency', currency, maximumFractionDigits: currency === 'KHR' ? 0 : 2 }).format(Number(amount));
}
export function localDate(value: string | null | undefined) {
  if (!value) return '—';
  return new Intl.DateTimeFormat('en-GB', { timeZone: 'Asia/Phnom_Penh', dateStyle: 'medium', timeStyle: 'short' }).format(new Date(value));
}
export function canReportDelay(payment: Payment, now = Date.now()) {
  return payment.status === 'submitted' && !!payment.confirmed_at && !payment.delayed_reported_at && now - Date.parse(payment.confirmed_at) >= 24 * 60 * 60 * 1000;
}
export function uppercasePayerName(value: string) { return value.toUpperCase(); }

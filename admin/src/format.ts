export function dateTime(value: string | null | undefined) {
  if (!value) return '—';
  const date = new Date(value);
  return Number.isNaN(date.getTime())
    ? value
    : new Intl.DateTimeFormat('en-GB', {
        timeZone: 'Asia/Phnom_Penh',
        dateStyle: 'medium',
        timeStyle: 'short',
      }).format(date);
}
// datetime-local controls are explicitly Phnom Penh (UTC+07:00), not the browser's timezone.
export function phnomPenhISO(value: string) {
  if (!value) throw new Error('A date and time in Asia/Phnom_Penh is required.');
  const date = new Date(`${value}:00+07:00`);
  if (Number.isNaN(date.getTime())) throw new Error('Invalid date/time.');
  return date.toISOString();
}
export function monthRange(start: string, end: string) {
  if (!/^\d{4}-(0[1-9]|1[0-2])$/.test(start) || !/^\d{4}-(0[1-9]|1[0-2])$/.test(end) || start > end)
    throw new Error('Enter valid YYYY-MM boundaries with start not after end.');
}

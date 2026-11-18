const dateFmt = new Intl.DateTimeFormat("tr-TR", { day: "2-digit", month: "short", year: "numeric" });
const dateTimeFmt = new Intl.DateTimeFormat("tr-TR", {
  day: "2-digit",
  month: "short",
  hour: "2-digit",
  minute: "2-digit",
});
const relFmt = new Intl.RelativeTimeFormat("tr-TR", { numeric: "auto" });

export function fmtDate(v?: string | null): string {
  if (!v) return "—";
  return dateFmt.format(new Date(v.length === 10 ? `${v}T00:00:00` : v));
}

export function fmtDateTime(v?: string | null): string {
  return v ? dateTimeFmt.format(new Date(v)) : "—";
}

export function fmtRelative(v?: string | null): string {
  if (!v) return "—";
  const diffMin = Math.round((new Date(v).getTime() - Date.now()) / 60000);
  if (Math.abs(diffMin) < 60) return relFmt.format(diffMin, "minute");
  const diffH = Math.round(diffMin / 60);
  if (Math.abs(diffH) < 24) return relFmt.format(diffH, "hour");
  return relFmt.format(Math.round(diffH / 24), "day");
}

export function isoDate(d: Date): string {
  const tz = d.getTimezoneOffset() * 60000;
  return new Date(d.getTime() - tz).toISOString().slice(0, 10);
}

export function initials(name: string): string {
  return name
    .split(" ")
    .map((p) => p[0])
    .slice(0, 2)
    .join("")
    .toLocaleUpperCase("tr-TR");
}

export function pct(part: number, total: number): number {
  return total ? Math.round((part / total) * 100) : 0;
}

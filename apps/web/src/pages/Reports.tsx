import { Download } from "lucide-react";
import { useState } from "react";
import { Bar, BarChart, CartesianGrid, Legend, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import { csvUrl, errorMessage, useTaskReport, useTeams } from "../api/hooks";
import {
  Card,
  CardHeader,
  EmptyState,
  ErrorState,
  Field,
  Input,
  PageHeader,
  ProgressBar,
  Select,
  Skeleton,
} from "../components/ui";
import { groupByLabel, priorityLabel, statusLabel, typeLabel, categoryLabel } from "../i18n/tr";
import { isoDate, pct } from "../lib/format";

type GroupBy = keyof typeof groupByLabel;
const ENUM_LABELS: Record<string, Record<string, string>> = {
  status: statusLabel,
  priority: priorityLabel,
  type: typeLabel,
  category: categoryLabel,
};

export function ReportsPage() {
  const teams = useTeams();
  const today = new Date();
  const [groupBy, setGroupBy] = useState<GroupBy>("team");
  const [from, setFrom] = useState(isoDate(new Date(today.getTime() - 30 * 864e5)));
  const [to, setTo] = useState(isoDate(today));
  const [teamId, setTeamId] = useState("");
  const invalid = !from || !to || to < from;
  const report = useTaskReport({ groupBy, from, to, teamId: teamId || undefined });
  const label = (l: string) => ENUM_LABELS[groupBy]?.[l] ?? l;
  const rows = report.data?.rows ?? [];
  const chart = rows.slice(0, 12).map((r) => ({
    name: label(r.label),
    Başlanmadı: r.counts.todo,
    "Devam ediyor": r.counts.inProgress,
    Bloklu: r.counts.blocked,
    Tamamlandı: r.counts.done,
  }));

  return (
    <>
      <PageHeader
        title="Raporlar"
        subtitle="Task'ların toplu raporu — oluşturulma tarihine göre"
        actions={
          <a
            href={invalid ? undefined : csvUrl("/reports/tasks", { groupBy, from, to, teamId: teamId || undefined })}
            aria-disabled={invalid}
            className="inline-flex h-10 items-center gap-2 rounded-lg bg-primary px-4 text-sm font-medium text-on-primary hover:bg-primary-hover aria-disabled:pointer-events-none aria-disabled:opacity-50"
          >
            <Download className="size-4" /> CSV indir
          </a>
        }
      />
      <Card className="mb-6">
        <div className="grid gap-4 p-5 sm:grid-cols-2 lg:grid-cols-4">
          <Field label="Gruplama" htmlFor="r-group">
            <Select id="r-group" value={groupBy} onChange={(e) => setGroupBy(e.target.value as GroupBy)}>
              {Object.entries(groupByLabel).map(([k, l]) => <option key={k} value={k}>{l}</option>)}
            </Select>
          </Field>
          <Field label="Ekip" htmlFor="r-team">
            <Select id="r-team" value={teamId} onChange={(e) => setTeamId(e.target.value)}>
              <option value="">Tüm görünür ekipler</option>
              {teams.data?.map((t) => <option key={t.id} value={t.id}>{t.name}</option>)}
            </Select>
          </Field>
          <Field label="Başlangıç" htmlFor="r-from"><Input id="r-from" type="date" value={from} max={to} onChange={(e) => setFrom(e.target.value)} /></Field>
          <Field label="Bitiş" htmlFor="r-to" error={invalid ? "Bitiş başlangıçtan önce olamaz." : undefined}>
            <Input id="r-to" type="date" value={to} min={from} onChange={(e) => setTo(e.target.value)} />
          </Field>
        </div>
      </Card>
      {report.error ? (
        <Card><ErrorState message={errorMessage(report.error)} onRetry={() => void report.refetch()} /></Card>
      ) : report.isPending ? (
        <Skeleton className="h-96" />
      ) : rows.length === 0 ? (
        <Card><EmptyState title="Bu aralıkta task yok" /></Card>
      ) : (
        <div className="space-y-6">
          <Card>
            <CardHeader title={`${groupByLabel[groupBy]} bazında dağılım`} subtitle={rows.length > 12 ? "İlk 12 grup gösteriliyor" : undefined} />
            <div className="h-80 p-4">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={chart}>
                  <CartesianGrid strokeDasharray="3 3" stroke="var(--border)" vertical={false} />
                  <XAxis dataKey="name" tick={{ fill: "var(--text-muted)", fontSize: 11 }} interval={0} angle={chart.length > 6 ? -25 : 0} textAnchor={chart.length > 6 ? "end" : "middle"} height={chart.length > 6 ? 70 : 30} />
                  <YAxis tick={{ fill: "var(--text-muted)", fontSize: 12 }} allowDecimals={false} />
                  <Tooltip contentStyle={{ background: "var(--surface)", border: "1px solid var(--border)", borderRadius: 8, color: "var(--text)" }} />
                  <Legend wrapperStyle={{ fontSize: 12 }} />
                  <Bar dataKey="Başlanmadı" stackId="a" fill="var(--todo)" />
                  <Bar dataKey="Devam ediyor" stackId="a" fill="var(--progress)" />
                  <Bar dataKey="Bloklu" stackId="a" fill="var(--blocked)" />
                  <Bar dataKey="Tamamlandı" stackId="a" fill="var(--done)" />
                </BarChart>
              </ResponsiveContainer>
            </div>
          </Card>
          <Card>
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead className="bg-surface-2 text-left text-xs text-muted uppercase">
                  <tr>
                    <th scope="col" className="px-5 py-3 font-medium">{groupByLabel[groupBy]}</th>
                    {["Başlanmadı", "Devam", "Bloklu", "Tamamlandı", "Gecikmiş", "Toplam", "Ort. süre (sa)"].map((h) => (
                      <th key={h} scope="col" className="px-3 py-3 text-right font-medium">{h}</th>
                    ))}
                    <th scope="col" className="w-40 px-5 py-3 font-medium">Tamamlanma</th>
                  </tr>
                </thead>
                <tbody>
                  {rows.map((r) => (
                    <tr key={r.key} className="border-t border-border">
                      <th scope="row" className="px-5 py-2.5 text-left font-medium text-text">{label(r.label)}</th>
                      <td className="tabular px-3 text-right text-todo">{r.counts.todo}</td>
                      <td className="tabular px-3 text-right text-progress">{r.counts.inProgress}</td>
                      <td className="tabular px-3 text-right text-blocked">{r.counts.blocked}</td>
                      <td className="tabular px-3 text-right text-done">{r.counts.done}</td>
                      <td className="tabular px-3 text-right text-danger">{r.counts.overdue}</td>
                      <td className="tabular px-3 text-right font-medium">{r.counts.total}</td>
                      <td className="tabular px-3 text-right text-muted">{r.avgCompletionHours ?? "—"}</td>
                      <td className="px-5"><div className="flex items-center gap-2"><ProgressBar counts={r.counts} /><span className="tabular w-9 text-right text-xs text-muted">%{pct(r.counts.done, r.counts.total)}</span></div></td>
                    </tr>
                  ))}
                </tbody>
                {report.data && (
                  <tfoot className="border-t-2 border-border font-semibold">
                    <tr>
                      <th scope="row" className="px-5 py-3 text-left">Toplam</th>
                      {(["todo", "inProgress", "blocked", "done", "overdue", "total"] as const).map((k) => (
                        <td key={k} className="tabular px-3 text-right">{report.data.totals[k]}</td>
                      ))}
                      <td colSpan={2} />
                    </tr>
                  </tfoot>
                )}
              </table>
            </div>
          </Card>
        </div>
      )}
    </>
  );
}

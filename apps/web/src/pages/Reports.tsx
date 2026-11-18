import { CalendarClock, Download, Play, Trash2 } from "lucide-react";
import { useState } from "react";
import { Bar, BarChart, CartesianGrid, Legend, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import {
  csvUrl,
  errorMessage,
  useCreateReportSchedule,
  useDeleteReportSchedule,
  useReportSchedules,
  useRunReportSchedule,
  useTaskReport,
  useTeams,
  useUnits,
  useUpdateReportSchedule,
  type Schemas,
} from "../api/hooks";
import { useAuth } from "../auth";
import {
  Badge,
  Button,
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
  legendText,
  useToast,
} from "../components/ui";
import { groupByLabel, priorityLabel, reportFrequencyLabel, statusLabel, typeLabel, categoryLabel } from "../i18n/tr";
import { fmtDateTime, isoDate, pct } from "../lib/format";
import { TeamOptions } from "../components/TeamOptions";

type GroupBy = keyof typeof groupByLabel;
const ENUM_LABELS: Record<string, Record<string, string>> = {
  status: statusLabel,
  priority: priorityLabel,
  type: typeLabel,
  category: categoryLabel,
};

export function ReportsPage() {
  const teams = useTeams();
  const units = useUnits();
  const today = new Date();
  const [groupBy, setGroupBy] = useState<GroupBy>("team");
  const [unitId, setUnitId] = useState("");
  const [from, setFrom] = useState(isoDate(new Date(today.getTime() - 30 * 864e5)));
  const [to, setTo] = useState(isoDate(today));
  const [teamId, setTeamId] = useState("");
  const invalid = !from || !to || to < from;
  const unitTeams = unitId ? teams.data?.filter((t) => t.unitId === unitId) : teams.data;
  const report = useTaskReport({ groupBy, from, to, teamId: teamId || undefined, unitId: unitId || undefined });
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
            href={invalid ? undefined : csvUrl("/reports/tasks", { groupBy, from, to, teamId: teamId || undefined, unitId: unitId || undefined })}
            aria-disabled={invalid}
            className="inline-flex h-10 items-center gap-2 rounded-lg bg-primary px-4 text-sm font-medium text-on-primary hover:bg-primary-hover aria-disabled:pointer-events-none aria-disabled:opacity-50"
          >
            <Download className="size-4" /> CSV indir
          </a>
        }
      />
      <Card className="mb-6">
        <div className="grid gap-4 p-5 sm:grid-cols-2 lg:grid-cols-5">
          <Field label="Gruplama" htmlFor="r-group">
            <Select id="r-group" value={groupBy} onChange={(e) => setGroupBy(e.target.value as GroupBy)}>
              {Object.entries(groupByLabel).map(([k, l]) => <option key={k} value={k}>{l}</option>)}
            </Select>
          </Field>
          <Field label="Unit" htmlFor="r-unit">
            <Select
              id="r-unit"
              value={unitId}
              disabled={(units.data?.length ?? 0) < 2}
              onChange={(e) => {
                setUnitId(e.target.value);
                setTeamId("");
              }}
            >
              <option value="">Tüm unit'ler</option>
              {units.data?.map((u) => <option key={u.id} value={u.id}>{u.name}{u.description ? ` — ${u.description}` : ""}</option>)}
            </Select>
          </Field>
          <Field label="Ekip" htmlFor="r-team">
            <Select id="r-team" value={teamId} onChange={(e) => setTeamId(e.target.value)}>
              <option value="">{unitId ? "Unit'in tüm ekipleri" : "Tüm görünür ekipler"}</option>
              <TeamOptions teams={unitTeams} />
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
                  <Tooltip cursor={{ fill: "var(--surface-2)" }} contentStyle={{ background: "var(--surface)", border: "1px solid var(--border)", borderRadius: 8, color: "var(--text)" }}
                          itemStyle={{ color: "var(--text)" }} />
                  <Legend wrapperStyle={{ fontSize: 12 }} formatter={legendText} />
                  <Bar dataKey="Başlanmadı" stackId="a" fill="var(--chart-todo)" />
                  <Bar dataKey="Devam ediyor" stackId="a" fill="var(--chart-progress)" />
                  <Bar dataKey="Bloklu" stackId="a" fill="var(--chart-blocked)" />
                  <Bar dataKey="Tamamlandı" stackId="a" fill="var(--chart-done)" />
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
      <SchedulesCard />
    </>
  );
}

function SchedulesCard() {
  const { can } = useAuth();
  const toast = useToast();
  const teams = useTeams();
  const list = useReportSchedules();
  const create = useCreateReportSchedule();
  const update = useUpdateReportSchedule();
  const del = useDeleteReportSchedule();
  const run = useRunReportSchedule();
  const [name, setName] = useState("");
  const [frequency, setFrequency] = useState<Schemas["ReportFrequency"]>("WEEKLY");
  const [groupBy, setGroupBy] = useState<GroupBy>("team");
  const [teamId, setTeamId] = useState("");
  if (!can.manage && !can.readOnly) return null;
  const onError = (e: unknown) => toast("error", errorMessage(e));
  return (
    <Card className="mt-6">
      <CardHeader
        title="Planlı raporlar"
        subtitle="Haftalık ve aylık raporlar önceki dönem için üretilip CSV eki ile e-postanıza gönderilir."
      />
      <form
        className="grid gap-3 border-b border-border px-5 py-4 sm:grid-cols-2 lg:grid-cols-[2fr_1.5fr_1fr_1fr_auto] lg:items-end"
        onSubmit={(e) => {
          e.preventDefault();
          create.mutate(
            { name: name.trim(), frequency, groupBy, teamId: teamId || undefined },
            { onSuccess: () => (setName(""), toast("success", "Rapor planlandı.")), onError },
          );
        }}
      >
        <Field label="Ad" htmlFor="s-name">
          <Input id="s-name" value={name} onChange={(e) => setName(e.target.value)} minLength={2} maxLength={100} placeholder="Örn. SOC haftalık durum" />
        </Field>
        <Field label="Sıklık" htmlFor="s-freq">
          <Select id="s-freq" value={frequency} onChange={(e) => setFrequency(e.target.value as Schemas["ReportFrequency"])}>
            {Object.entries(reportFrequencyLabel).map(([k, l]) => <option key={k} value={k}>{l}</option>)}
          </Select>
        </Field>
        <Field label="Gruplama" htmlFor="s-group">
          <Select id="s-group" value={groupBy} onChange={(e) => setGroupBy(e.target.value as GroupBy)}>
            {Object.entries(groupByLabel).map(([k, l]) => <option key={k} value={k}>{l}</option>)}
          </Select>
        </Field>
        <Field label="Ekip" htmlFor="s-team">
          <Select id="s-team" value={teamId} onChange={(e) => setTeamId(e.target.value)}>
            <option value="">Tümü</option>
            <TeamOptions teams={teams.data} />
          </Select>
        </Field>
        <Button type="submit" loading={create.isPending} disabled={name.trim().length < 2}>
          <CalendarClock className="size-4" /> Planla
        </Button>
      </form>
      {list.isPending ? (
        <Skeleton className="m-5 h-16" />
      ) : list.error ? (
        <ErrorState message={errorMessage(list.error)} />
      ) : list.data.length === 0 ? (
        <EmptyState title="Planlı rapor yok" description="Yukarıdan haftalık veya aylık rapor planlayın." />
      ) : (
        <ul className="divide-y divide-border">
          {list.data.map((s) => (
            <li key={s.id} className="flex flex-wrap items-center gap-3 px-5 py-3 text-sm">
              <div className="min-w-0 flex-1">
                <p className="font-medium text-text">{s.name}</p>
                <p className="text-xs text-muted">
                  {reportFrequencyLabel[s.frequency]} · {groupByLabel[s.groupBy as GroupBy]} bazında
                  {s.teamId ? ` · ${teams.data?.find((t) => t.id === s.teamId)?.name ?? ""}` : ""} · sonraki: {fmtDateTime(s.nextRunAt)}
                  {s.lastRunAt && ` · son: ${fmtDateTime(s.lastRunAt)}`}
                </p>
              </div>
              {s.lastStatus && (
                <Badge className={s.lastStatus === "SUCCESS" ? "bg-success-soft text-done" : "bg-danger-soft text-danger"}>
                  {s.lastStatus === "SUCCESS" ? "Gönderildi" : "Başarısız"}
                </Badge>
              )}
              <label className="flex items-center gap-1.5 text-xs text-muted">
                <input
                  type="checkbox"
                  checked={s.active}
                  onChange={(e) => update.mutate({ id: s.id, active: e.target.checked }, { onError })}
                />
                Aktif
              </label>
              <Button
                size="sm"
                variant="secondary"
                loading={run.isPending && run.variables === s.id}
                onClick={() => run.mutate(s.id, { onSuccess: () => toast("success", "Rapor e-postayla gönderildi."), onError })}
              >
                <Play className="size-4" /> Şimdi gönder
              </Button>
              <Button
                size="sm"
                variant="ghost"
                aria-label={`${s.name} planını sil`}
                onClick={() => confirm("Plan silinsin mi?") && del.mutate(s.id, { onError })}
              >
                <Trash2 className="size-4 text-danger" />
              </Button>
            </li>
          ))}
        </ul>
      )}
    </Card>
  );
}

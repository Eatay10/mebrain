import { AlarmClock, ArrowRight } from "lucide-react";
import { useState } from "react";
import { Link } from "react-router";
import { Bar, BarChart, CartesianGrid, Legend, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import { useAnnouncements, useDashboard, useTeams, type Schemas } from "../api/hooks";
import { useAuth } from "../auth";
import {
  Card,
  CardHeader,
  EmptyState,
  ErrorState,
  PageHeader,
  ProgressBar,
  Select,
  Skeleton,
  Stat,
  Tabs,
} from "../components/ui";
import { fmtDate, fmtRelative, pct } from "../lib/format";

type Part = "all" | "standard" | "project";
const PART_LABEL: Record<Part, string> = { all: "Tümü", standard: "Standart task'lar", project: "Proje task'ları" };
const COLS: Array<{ key: keyof Schemas["StatusCounts"]; label: string; status?: string; tone: string }> = [
  { key: "todo", label: "Başlanmadı", status: "TODO", tone: "text-todo" },
  { key: "inProgress", label: "Devam ediyor", status: "IN_PROGRESS", tone: "text-progress" },
  { key: "blocked", label: "Bloklu", status: "BLOCKED", tone: "text-blocked" },
  { key: "done", label: "Tamamlandı", status: "DONE", tone: "text-done" },
  { key: "overdue", label: "Gecikmiş", tone: "text-danger" },
];

function taskLink(teamId: string | undefined, part: Part, col: (typeof COLS)[number]): string {
  const q = new URLSearchParams();
  if (teamId) q.set("teamId", teamId);
  if (part !== "all") q.set("type", part === "standard" ? "STANDARD" : "PROJECT");
  if (col.status) q.set("status", col.status);
  else q.set("overdue", "true");
  return `/tasks?${q.toString()}`;
}

export function DashboardPage() {
  const { user, session } = useAuth();
  const [part, setPart] = useState<Part>("all");
  const [teamId, setTeamId] = useState<string>("");
  const teams = useTeams();
  const dash = useDashboard(teamId ? { teamId } : {});
  const d = dash.data;
  const totals = d?.totals[part];
  const chartData =
    d?.teams.map((t) => ({
      name: t.teamName,
      Başlanmadı: t[part].todo,
      "Devam ediyor": t[part].inProgress,
      Bloklu: t[part].blocked,
      Tamamlandı: t[part].done,
    })) ?? [];

  return (
    <>
      <PageHeader
        title={`Merhaba, ${user.fullName.split(" ")[0]}`}
        subtitle={`Ekip bazlı task durumu · ${session.visibleTeamIds.length} ekip görünür${d ? ` · güncellendi ${fmtRelative(d.generatedAt)}` : ""}`}
        actions={
          <>
            {(teams.data?.length ?? 0) > 1 && (
              <Select aria-label="Ekip filtresi" value={teamId} onChange={(e) => setTeamId(e.target.value)} className="w-48">
                <option value="">Tüm ekipler</option>
                {teams.data?.map((t) => (
                  <option key={t.id} value={t.id}>
                    {t.name}
                  </option>
                ))}
              </Select>
            )}
            <Tabs<Part>
              value={part}
              onChange={setPart}
              items={(["all", "standard", "project"] as const).map((v) => ({ value: v, label: PART_LABEL[v] }))}
            />
          </>
        }
      />

      {dash.error ? (
        <Card>
          <ErrorState message="Dashboard verisi alınamadı." onRetry={() => void dash.refetch()} />
        </Card>
      ) : (
        <div className="space-y-6">
          <div className="grid grid-cols-2 gap-4 md:grid-cols-3 xl:grid-cols-6">
            {COLS.map((c) =>
              totals ? (
                <Link key={c.key} to={taskLink(teamId || undefined, part, c)} className="rounded-xl focus-visible:outline-2">
                  <Stat label={c.label} value={totals[c.key]} tone={c.tone} hint={c.key === "overdue" ? "son tarihi geçmiş" : `%${pct(totals[c.key], totals.total)}`} />
                </Link>
              ) : (
                <Skeleton key={c.key} className="h-[92px]" />
              ),
            )}
            {totals ? <Stat label="Toplam" value={totals.total} hint={PART_LABEL[part]} /> : <Skeleton className="h-[92px]" />}
          </div>

          <div className="grid gap-6 xl:grid-cols-3">
            <Card className="xl:col-span-2">
              <CardHeader title="Ekiplere göre durum" subtitle={PART_LABEL[part]} />
              <div className="h-72 px-2 py-4">
                {!d ? (
                  <Skeleton className="m-4 h-60" />
                ) : chartData.length === 0 ? (
                  <EmptyState title="Görüntülenecek ekip yok" />
                ) : (
                  <ResponsiveContainer width="100%" height="100%">
                    <BarChart data={chartData} margin={{ left: 0, right: 16 }}>
                      <CartesianGrid strokeDasharray="3 3" stroke="var(--border)" vertical={false} />
                      <XAxis dataKey="name" tick={{ fill: "var(--text-muted)", fontSize: 12 }} axisLine={false} tickLine={false} />
                      <YAxis tick={{ fill: "var(--text-muted)", fontSize: 12 }} axisLine={false} tickLine={false} allowDecimals={false} />
                      <Tooltip
                        cursor={{ fill: "var(--surface-2)" }}
                        contentStyle={{ background: "var(--surface)", border: "1px solid var(--border)", borderRadius: 8, color: "var(--text)" }}
                      />
                      <Legend wrapperStyle={{ fontSize: 12 }} />
                      <Bar dataKey="Başlanmadı" stackId="a" fill="var(--todo)" />
                      <Bar dataKey="Devam ediyor" stackId="a" fill="var(--progress)" />
                      <Bar dataKey="Bloklu" stackId="a" fill="var(--blocked)" />
                      <Bar dataKey="Tamamlandı" stackId="a" fill="var(--done)" radius={[4, 4, 0, 0]} />
                    </BarChart>
                  </ResponsiveContainer>
                )}
              </div>
            </Card>

            <Card>
              <CardHeader title="Bana atananlar" subtitle="Tüm türler" />
              {!d ? (
                <Skeleton className="m-5 h-40" />
              ) : (
                <div className="space-y-3 px-5 py-4">
                  {COLS.map((c) => (
                    <Link
                      key={c.key}
                      to={`/tasks?assigneeId=me&${c.status ? `status=${c.status}` : "overdue=true"}`}
                      className="flex items-center justify-between rounded-lg px-3 py-2 hover:bg-surface-2"
                    >
                      <span className="text-sm text-text">{c.label}</span>
                      <span className={`tabular text-lg font-semibold ${c.tone}`}>{d.mine[c.key]}</span>
                    </Link>
                  ))}
                  {d.mine.overdue > 0 && (
                    <p className="flex items-center gap-2 rounded-lg bg-danger-soft px-3 py-2 text-xs text-danger">
                      <AlarmClock className="size-4" /> {d.mine.overdue} task'ınızın son tarihi geçti.
                    </p>
                  )}
                </div>
              )}
            </Card>
          </div>

          <Card>
            <CardHeader title="Ekip tablosu" subtitle="Sayıya tıklayarak filtrelenmiş task listesini açın" />
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead className="bg-surface-2 text-left text-xs text-muted uppercase">
                  <tr>
                    <th scope="col" className="px-5 py-3 font-medium">Ekip</th>
                    {COLS.map((c) => (
                      <th key={c.key} scope="col" className="px-3 py-3 text-right font-medium">{c.label}</th>
                    ))}
                    <th scope="col" className="px-3 py-3 text-right font-medium">Toplam</th>
                    <th scope="col" className="w-48 px-5 py-3 font-medium">İlerleme</th>
                  </tr>
                </thead>
                <tbody>
                  {!d
                    ? Array.from({ length: 3 }).map((_, i) => (
                        <tr key={i}>
                          <td colSpan={8} className="px-5 py-3"><Skeleton className="h-5" /></td>
                        </tr>
                      ))
                    : d.teams.map((t) => (
                        <tr key={t.teamId} className="border-t border-border">
                          <th scope="row" className="px-5 py-3 text-left font-medium text-text">{t.teamName}</th>
                          {COLS.map((c) => (
                            <td key={c.key} className="px-3 py-3 text-right">
                              <Link className={`tabular rounded px-1.5 py-0.5 hover:bg-surface-2 ${c.tone}`} to={taskLink(t.teamId, part, c)}>
                                {t[part][c.key]}
                              </Link>
                            </td>
                          ))}
                          <td className="tabular px-3 py-3 text-right font-medium">{t[part].total}</td>
                          <td className="px-5 py-3">
                            <div className="flex items-center gap-2">
                              <ProgressBar counts={t[part]} />
                              <span className="tabular w-10 text-right text-xs text-muted">%{pct(t[part].done, t[part].total)}</span>
                            </div>
                          </td>
                        </tr>
                      ))}
                </tbody>
              </table>
            </div>
          </Card>

          <div className="grid gap-6 xl:grid-cols-2">
            <ProjectsCard projects={d?.projects} />
            <AnnouncementsCard />
          </div>
        </div>
      )}
      <span className="sr-only" aria-live="polite">{dash.isFetching ? "Güncelleniyor" : ""}</span>
    </>
  );
}

function ProjectsCard({ projects }: { projects?: Schemas["DashboardSummary"]["projects"] }) {
  return (
    <Card>
      <CardHeader title="Aktif projeler" subtitle="Son tarihe göre" actions={<Link to="/projects" className="text-sm text-primary hover:underline">Tümü</Link>} />
      {!projects ? (
        <Skeleton className="m-5 h-40" />
      ) : projects.length === 0 ? (
        <EmptyState title="Aktif proje yok" />
      ) : (
        <ul className="divide-y divide-border">
          {projects.map((p) => (
            <li key={p.id}>
              <Link to={`/projects/${p.id}`} className="flex items-center gap-4 px-5 py-3 hover:bg-surface-2">
                <div className="min-w-0 flex-1">
                  <p className="truncate text-sm font-medium text-text">{p.name}</p>
                  <p className="text-xs text-muted">Son tarih: {fmtDate(p.dueDate)} · {p.progress.total} task</p>
                </div>
                <div className="w-32"><ProgressBar counts={p.progress} /></div>
                <span className="tabular w-10 text-right text-xs text-muted">%{pct(p.progress.done, p.progress.total)}</span>
                <ArrowRight className="size-4 text-muted" aria-hidden />
              </Link>
            </li>
          ))}
        </ul>
      )}
    </Card>
  );
}

function AnnouncementsCard() {
  const a = useAnnouncements();
  return (
    <Card>
      <CardHeader title="Duyurular" actions={<Link to="/announcements" className="text-sm text-primary hover:underline">Tümü</Link>} />
      {a.isPending ? (
        <Skeleton className="m-5 h-40" />
      ) : a.error ? (
        <ErrorState message="Duyurular yüklenemedi." />
      ) : !a.data.items.length ? (
        <EmptyState title="Duyuru yok" />
      ) : (
        <ul className="divide-y divide-border">
          {a.data.items.slice(0, 4).map((x) => (
            <li key={x.id} className="px-5 py-3">
              <p className="text-sm font-medium text-text">{x.pinned && "📌 "}{x.title}</p>
              <p className="line-clamp-2 text-sm text-muted">{x.body}</p>
              <p className="mt-1 text-xs text-muted">
                {x.author.fullName} · {x.scope === "ORGANIZATION" ? "Kurum geneli" : "Ekip"} · {fmtRelative(x.createdAt)}
              </p>
            </li>
          ))}
        </ul>
      )}
    </Card>
  );
}

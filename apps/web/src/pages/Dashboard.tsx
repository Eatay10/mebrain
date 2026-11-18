import { AlarmClock, ArrowRight, Star, TrendingUp } from "lucide-react";
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
  StatusBadge,
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

type Kind = Schemas["DashboardBreakdownKind"];
// Rol → kırılım başlıkları (API kırılımı role göre seçer; ekran sadece etiketler).
const KIND_TEXT: Record<Exclude<Kind, "NONE">, { chart: string; table: string; col: string; empty: string }> = {
  MEMBER: { chart: "Çalışanlara göre durum", table: "Çalışan tablosu", col: "Çalışan", empty: "Yönettiğiniz ekiplerde çalışan yok" },
  TEAM_MANAGER: { chart: "Ekip yöneticilerinin puanları", table: "Ekip yöneticileri", col: "Ekip yöneticisi", empty: "Unit'inizde ekip yok" },
  UNIT: { chart: "Unit'lere göre durum", table: "Unit tablosu", col: "Unit", empty: "Görüntülenecek unit yok" },
};
const SCORE_HINT = "Puan = 0,5 × tamamlanma oranı + 0,5 × ortalama ilerleme − gecikmiş oranı (0–100)";

function taskLink(teamId: string | undefined, part: Part, col: (typeof COLS)[number], assigneeId?: string | null): string {
  const q = new URLSearchParams();
  if (teamId) q.set("teamId", teamId);
  if (assigneeId) q.set("assigneeId", assigneeId);
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
  const kind: Kind | undefined = d?.breakdown.kind;
  const rows = d?.breakdown.rows ?? [];
  const text = kind && kind !== "NONE" ? KIND_TEXT[kind] : undefined;
  const chartData = rows.map((r) => ({
    name: r.label,
    Başlanmadı: r[part].todo,
    "Devam ediyor": r[part].inProgress,
    Bloklu: r[part].blocked,
    Tamamlandı: r[part].done,
    Puan: r.score,
  }));

  return (
    <>
      <PageHeader
        title={`Merhaba, ${user.fullName.split(" ")[0]}`}
        subtitle={`${session.visibleTeamIds.length} ekip görünür${d ? ` · güncellendi ${fmtRelative(d.generatedAt)}` : ""}`}
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
            <Card>
              <CardHeader title="İlerleme" subtitle="Task'ların ortalama tamamlanma yüzdesi" />
              {!d ? (
                <Skeleton className="m-5 h-24" />
              ) : (
                <div className="space-y-4 px-5 py-4">
                  {[
                    ["Kapsamdaki tüm task'lar", d.avgProgress ?? 0],
                    ["Dahil olduğum task'lar", d.mineAvgProgress ?? 0],
                  ].map(([label, value]) => (
                    <div key={String(label)}>
                      <div className="mb-1 flex items-center justify-between text-sm">
                        <span className="flex items-center gap-1.5 text-text"><TrendingUp className="size-4 text-muted" aria-hidden />{label}</span>
                        <span className="tabular text-xl font-semibold text-primary">%{value}</span>
                      </div>
                      <div className="h-2 overflow-hidden rounded-full bg-surface-2" role="progressbar" aria-valuenow={Number(value)} aria-valuemin={0} aria-valuemax={100} aria-label={String(label)}>
                        <div className="h-full rounded-full bg-primary" style={{ width: `${value}%` }} />
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </Card>
            <WatchingCard items={d?.watching} />
          </div>

          <div className="grid gap-6 xl:grid-cols-3">
            {kind !== "NONE" && (
              <Card className="xl:col-span-2">
                <CardHeader
                  title={text?.chart ?? "Durum"}
                  subtitle={kind === "TEAM_MANAGER" ? SCORE_HINT : PART_LABEL[part]}
                />
                <div className="h-72 px-2 py-4">
                  {!d ? (
                    <Skeleton className="m-4 h-60" />
                  ) : chartData.length === 0 ? (
                    <EmptyState title={text?.empty ?? "Veri yok"} />
                  ) : (
                    <ResponsiveContainer width="100%" height="100%">
                      <BarChart data={chartData} margin={{ left: 0, right: 16 }}>
                        <CartesianGrid strokeDasharray="3 3" stroke="var(--border)" vertical={false} />
                        <XAxis dataKey="name" tick={{ fill: "var(--text-muted)", fontSize: 12 }} axisLine={false} tickLine={false} interval={0} />
                        <YAxis
                          tick={{ fill: "var(--text-muted)", fontSize: 12 }}
                          axisLine={false}
                          tickLine={false}
                          allowDecimals={false}
                          domain={kind === "TEAM_MANAGER" ? [0, 100] : undefined}
                        />
                        <Tooltip
                          cursor={{ fill: "var(--surface-2)" }}
                          contentStyle={{ background: "var(--surface)", border: "1px solid var(--border)", borderRadius: 8, color: "var(--text)" }}
                        />
                        {kind === "TEAM_MANAGER" ? (
                          <Bar dataKey="Puan" fill="var(--primary)" radius={[4, 4, 0, 0]} />
                        ) : (
                          <>
                            <Legend wrapperStyle={{ fontSize: 12 }} />
                            <Bar dataKey="Başlanmadı" stackId="a" fill="var(--todo)" />
                            <Bar dataKey="Devam ediyor" stackId="a" fill="var(--progress)" />
                            <Bar dataKey="Bloklu" stackId="a" fill="var(--blocked)" />
                            <Bar dataKey="Tamamlandı" stackId="a" fill="var(--done)" radius={[4, 4, 0, 0]} />
                          </>
                        )}
                      </BarChart>
                    </ResponsiveContainer>
                  )}
                </div>
              </Card>
            )}

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

          {kind !== "NONE" && (
            <Card>
              <CardHeader
                title={text?.table ?? "Tablo"}
                subtitle={kind === "UNIT" ? "Unit bazında toplamlar" : "Sayıya tıklayarak filtrelenmiş task listesini açın"}
              />
              <div className="overflow-x-auto">
                <table className="w-full text-sm">
                  <thead className="bg-surface-2 text-left text-xs text-muted uppercase">
                    <tr>
                      <th scope="col" className="px-5 py-3 font-medium">{text?.col ?? ""}</th>
                      {COLS.map((c) => (
                        <th key={c.key} scope="col" className="px-3 py-3 text-right font-medium">{c.label}</th>
                      ))}
                      <th scope="col" className="px-3 py-3 text-right font-medium">Toplam</th>
                      <th scope="col" className="w-48 px-5 py-3 font-medium">Tamamlanan</th>
                      <th scope="col" className="px-3 py-3 text-right font-medium">Ort. ilerleme</th>
                      <th scope="col" className="px-3 py-3 text-right font-medium" title={SCORE_HINT}>Puan</th>
                    </tr>
                  </thead>
                  <tbody>
                    {!d ? (
                      Array.from({ length: 3 }).map((_, i) => (
                        <tr key={i}>
                          <td colSpan={10} className="px-5 py-3"><Skeleton className="h-5" /></td>
                        </tr>
                      ))
                    ) : rows.length === 0 ? (
                      <tr>
                        <td colSpan={10}><EmptyState title={text?.empty ?? "Veri yok"} /></td>
                      </tr>
                    ) : (
                      rows.map((r) => {
                        const linkable = kind !== "UNIT" && !!r.teamId;
                        return (
                          <tr key={r.id} className="border-t border-border">
                            <th scope="row" className="px-5 py-3 text-left font-medium text-text">
                              {r.label}
                              {r.sublabel && <span className="block text-xs font-normal text-muted">{r.sublabel}</span>}
                            </th>
                            {COLS.map((c) => (
                              <td key={c.key} className="px-3 py-3 text-right">
                                {linkable ? (
                                  <Link
                                    className={`tabular rounded px-1.5 py-0.5 hover:bg-surface-2 ${c.tone}`}
                                    to={taskLink(r.teamId ?? undefined, part, c, r.assigneeId)}
                                  >
                                    {r[part][c.key]}
                                  </Link>
                                ) : (
                                  <span className={`tabular px-1.5 ${c.tone}`}>{r[part][c.key]}</span>
                                )}
                              </td>
                            ))}
                            <td className="tabular px-3 py-3 text-right font-medium">{r[part].total}</td>
                            <td className="px-5 py-3">
                              <div className="flex items-center gap-2">
                                <ProgressBar counts={r[part]} />
                                <span className="tabular w-10 text-right text-xs text-muted">%{pct(r[part].done, r[part].total)}</span>
                              </div>
                            </td>
                            <td className="tabular px-3 py-3 text-right text-muted">%{r.avgProgress}</td>
                            <td className="tabular px-3 py-3 text-right text-base font-semibold text-primary">{r.score}</td>
                          </tr>
                        );
                      })
                    )}
                  </tbody>
                </table>
              </div>
            </Card>
          )}

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

function WatchingCard({ items }: { items?: Schemas["DashboardSummary"]["watching"] }) {
  return (
    <Card className="xl:col-span-2">
      <CardHeader
        title="Yıldızlı task'larım"
        subtitle="Takip ettiğiniz task'lardaki her güncelleme size bildirilir"
        actions={<Link to="/tasks?watching=true" className="text-sm text-primary hover:underline">Tümü</Link>}
      />
      {!items ? (
        <Skeleton className="m-5 h-24" />
      ) : items.length === 0 ? (
        <EmptyState title="Yıldızlı task yok" description="Task detayındaki yıldız ile takip etmeye başlayın." />
      ) : (
        <ul className="divide-y divide-border">
          {items.map((t) => (
            <li key={t.id}>
              <Link to={`/tasks?watching=true&open=${t.id}`} className="flex items-center gap-3 px-5 py-2.5 hover:bg-surface-2">
                <Star className="size-4 shrink-0 fill-blocked text-blocked" aria-hidden />
                <span className="min-w-0 flex-1 truncate text-sm text-text">{t.title}</span>
                <StatusBadge status={t.status} />
                <span className="tabular w-12 text-right text-sm font-medium">%{t.progress}</span>
                <span className="hidden w-24 text-right text-xs text-muted sm:inline">{fmtRelative(t.updatedAt)}</span>
              </Link>
            </li>
          ))}
        </ul>
      )}
    </Card>
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

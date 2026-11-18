import { ArrowRight, CalendarDays, CheckCircle2, Clock, ListChecks, Plus, ShieldCheck, Star, Users } from "lucide-react";
import { useMemo, useState } from "react";
import { Link, useNavigate } from "react-router";
import { Bar, BarChart, CartesianGrid, Legend, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import {
  errorMessage,
  useAnnouncements,
  useDashboard,
  useEvents,
  useParticipations,
  useTasks,
  useTeams,
  useTransitionTask,
  type Schemas,
} from "../api/hooks";
import { useAuth } from "../auth";
import {
  Avatar,
  Button,
  Card,
  CardHeader,
  cx,
  EmptyState,
  ErrorState,
  ProgressBar,
  Select,
  Skeleton,
  StatusBadge,
  Tabs,
  legendText,
  useToast,
} from "../components/ui";
import { TeamOptions } from "../components/TeamOptions";
import { priorityLabel } from "../i18n/tr";
import { fmtDate, fmtRelative, isoDate, pct } from "../lib/format";
import { TaskFormModal } from "./TaskForm";

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
const AXIS_TICK = { fill: "var(--text-muted)", fontSize: 12 };
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

const STATUS_TITLE: Record<Exclude<Kind, "NONE">, string> = {
  MEMBER: "Çalışan durumu",
  TEAM_MANAGER: "Ekip durumu",
  UNIT: "Unit durumu",
};
const PRIORITY_TONE: Record<Schemas["TaskPriority"], string> = {
  CRITICAL: "bg-danger-soft text-danger",
  HIGH: "bg-danger-soft text-danger",
  MEDIUM: "bg-accent-soft text-blocked",
  LOW: "bg-success-soft text-done",
};
const OPEN: Schemas["TaskStatus"][] = ["TODO", "IN_PROGRESS", "BLOCKED"];

function endOfWeek(d: Date): Date {
  const e = new Date(d);
  e.setDate(d.getDate() + ((7 - d.getDay()) % 7)); // Pazar
  return e;
}

function dueText(due?: string | null): { text: string; late: boolean } {
  if (!due) return { text: "Tarih yok", late: false };
  const today = isoDate(new Date());
  const tomorrow = isoDate(new Date(Date.now() + 864e5));
  if (due < today) return { text: "Gecikti", late: true };
  if (due === today) return { text: "Bugün", late: false };
  if (due === tomorrow) return { text: "Yarın", late: false };
  return { text: new Date(due).toLocaleDateString("tr-TR", { day: "numeric", month: "short", weekday: "short" }), late: false };
}

export function DashboardPage() {
  const { user, session, can } = useAuth();
  const [creating, setCreating] = useState(false);
  const dash = useDashboard({});
  const d = dash.data;
  const kind = d?.breakdown.kind;
  const canCreate = !can.readOnly && (can.manage || !!session.user.teamId);
  const managing = !!d && d.missingBackup > 0;
  const today = new Date();

  return (
    <>
      <div className="mb-6 flex flex-wrap items-end justify-between gap-4">
        <div>
          <h1 className="text-3xl font-semibold tracking-tight text-text sm:text-4xl">Merhaba {user.fullName.split(" ")[0]},</h1>
          <p className="mt-1 text-muted">Bugünün öncelikleri, tek ekranda.</p>
        </div>
        <div className="flex items-center gap-3">
          <span className="inline-flex h-11 items-center gap-2 rounded-xl border border-border bg-surface px-4 text-sm text-text shadow-card">
            <CalendarDays className="size-4 text-muted" aria-hidden />
            {today.toLocaleDateString("tr-TR", { day: "numeric", month: "long", year: "numeric" })}
          </span>
          {canCreate && (
            <Button variant="accent" className="h-11 px-5" onClick={() => setCreating(true)}>
              <Plus className="size-4" /> Yeni görev
            </Button>
          )}
        </div>
      </div>

      <section className="relative mb-6 overflow-hidden rounded-2xl bg-sidebar px-6 py-7 text-white sm:px-8" aria-label="Karşılama">
        <div className="relative z-10 max-w-xl">
          <p className="text-2xl font-semibold tracking-tight sm:text-3xl">Birlikte daha planlı, her zaman hazır.</p>
          <p className="mt-1 text-white/80">Görevlerini takip et, ekibinle ilerle.</p>
        </div>
        <span className="absolute -right-6 -bottom-40 size-72 rounded-full bg-accent/45" aria-hidden />
        <span className="absolute -top-24 -right-20 size-72 rounded-full bg-accent" aria-hidden />
      </section>

      {dash.error ? (
        <Card>
          <ErrorState message="Genel bakış verisi alınamadı." onRetry={() => void dash.refetch()} />
        </Card>
      ) : (
        <div className="space-y-6">
          <div className="grid gap-4 md:grid-cols-3">
            <StatCard
              icon={<ListChecks className="size-7" />}
              iconClass="bg-info-soft text-primary"
              label="Bugünkü görevler"
              value={d?.today.total}
              hint={can.manage || can.observe ? "Kapsamınızda bugün son tarihli" : "Size atanan, bugün son tarihli"}
              to={`/tasks?${can.manage || can.observe ? "" : "assigneeId=me&"}dueFrom=${isoDate(today)}&dueTo=${isoDate(today)}`}
            />
            <StatCard
              icon={<CheckCircle2 className="size-7" />}
              iconClass="bg-success-soft text-done"
              label="Tamamlanan"
              value={d?.today.done}
              bar={d ? { value: d.today.done, max: d.today.total, className: "bg-done" } : undefined}
              hint="Bugün son tarihli görevlerden"
            />
            <StatCard
              icon={<Clock className="size-7" />}
              iconClass="bg-accent-soft text-blocked"
              label="Onay bekleyen"
              value={d?.approvals.pending}
              bar={d ? { value: d.approvals.pending, max: d.approvals.pending + d.approvals.decided, className: "bg-accent" } : undefined}
              hint={can.manage ? "Karar bekleyen katılım talepleri" : "Bekleyen katılım talepleriniz"}
              to="/events"
            />
          </div>

          <div className="grid gap-6 xl:grid-cols-5">
            <PriorityTasks className="xl:col-span-3" assigneeOnly={!can.manage && !can.observe} />
            <div className="flex flex-col gap-6 xl:col-span-2">
              {managing && <BackupCallout count={d.missingBackup} />}
              <UpcomingEvent />
            </div>
          </div>

          {d && kind && kind !== "NONE" && (
            <>
              <TeamStatus kind={kind} rows={d.breakdown.rows} avgProgress={d.avgProgress ?? 0} />
              <DetailedBreakdown />
            </>
          )}

          <div className="grid gap-6 xl:grid-cols-3">
            <WatchingCard items={d?.watching} />
            <AnnouncementsCard />
          </div>
          <ProjectsCard projects={d?.projects} />
        </div>
      )}
      <TaskFormModal open={creating} onClose={() => setCreating(false)} />
      <span className="sr-only" aria-live="polite">{dash.isFetching ? "Güncelleniyor" : ""}</span>
    </>
  );
}

function StatCard({
  icon,
  iconClass,
  label,
  value,
  bar,
  hint,
  to,
}: {
  icon: React.ReactNode;
  iconClass: string;
  label: string;
  value?: number;
  bar?: { value: number; max: number; className: string };
  hint?: string;
  to?: string;
}) {
  const body = (
    <div className="flex h-full items-center gap-5 rounded-2xl border border-border bg-surface p-5 shadow-card transition-colors hover:border-primary/30">
      <span className={cx("grid size-20 shrink-0 place-items-center rounded-2xl", iconClass)} aria-hidden>
        {icon}
      </span>
      <div className="min-w-0 flex-1">
        <p className="text-[15px] font-medium text-text">{label}</p>
        {value === undefined ? (
          <Skeleton className="mt-2 h-10 w-24" />
        ) : (
          <div className="mt-1 flex items-center gap-4">
            <span className="tabular text-4xl font-semibold text-text">{value}</span>
            {bar && (
              <span
                className="h-2.5 flex-1 overflow-hidden rounded-full bg-surface-2"
                role="progressbar"
                aria-label={label}
                aria-valuenow={bar.value}
                aria-valuemin={0}
                aria-valuemax={bar.max}
              >
                <span className={cx("block h-full rounded-full", bar.className)} style={{ width: `${pct(bar.value, bar.max)}%` }} />
              </span>
            )}
          </div>
        )}
        {hint && <p className="mt-1 truncate text-xs text-muted">{hint}</p>}
      </div>
    </div>
  );
  return to ? (
    <Link to={to} className="block rounded-2xl">
      {body}
    </Link>
  ) : (
    body
  );
}

function PriorityTasks({ className, assigneeOnly }: { className?: string; assigneeOnly: boolean }) {
  const [range, setRange] = useState<"today" | "week">("today");
  const navigate = useNavigate();
  const toast = useToast();
  const transition = useTransitionTask();
  const now = new Date();
  const dueTo = isoDate(range === "today" ? now : endOfWeek(now));
  const tasks = useTasks({
    status: OPEN,
    dueTo,
    sort: "-priority",
    pageSize: 5,
    ...(assigneeOnly ? { assigneeId: "me" } : {}),
  });
  const items = tasks.data?.items ?? [];
  return (
    <Card className={cx("rounded-2xl", className)}>
      <div className="flex flex-wrap items-center justify-between gap-3 px-5 pt-5 pb-3">
        <h2 className="text-xl font-semibold text-text">Öncelikli görevler</h2>
        <div className="flex rounded-full bg-surface-2 p-1 text-sm" role="tablist" aria-label="Zaman aralığı">
          {(
            [
              ["today", "Bugün"],
              ["week", "Bu hafta"],
            ] as const
          ).map(([k, l]) => (
            <button
              key={k}
              role="tab"
              aria-selected={range === k}
              onClick={() => setRange(k)}
              className={cx("rounded-full px-4 py-1.5", range === k ? "bg-accent font-semibold text-on-accent" : "text-muted hover:text-text")}
            >
              {l}
            </button>
          ))}
        </div>
      </div>
      {tasks.isPending ? (
        <Skeleton className="mx-5 mb-5 h-48" />
      ) : tasks.error ? (
        <ErrorState message={errorMessage(tasks.error)} onRetry={() => void tasks.refetch()} />
      ) : items.length === 0 ? (
        <EmptyState title={range === "today" ? "Bugün için açık görev yok" : "Bu hafta için açık görev yok"} />
      ) : (
        <ul className="mx-5 divide-y divide-border border-y border-border">
          {items.map((t) => {
            const due = dueText(t.dueDate);
            const canFinish = t.status === "IN_PROGRESS";
            return (
              <li key={t.id} className="flex items-center gap-4 py-3">
                <button
                  role="checkbox"
                  aria-checked={false}
                  aria-label={canFinish ? `${t.title} görevini tamamla` : `${t.title} görevini aç`}
                  title={canFinish ? "Tamamlandı olarak işaretle" : "Tamamlamak için önce başlatın"}
                  disabled={transition.isPending}
                  onClick={() =>
                    canFinish
                      ? transition.mutate(
                          { id: t.id, to: "DONE", version: t.version },
                          { onSuccess: () => toast("success", "Görev tamamlandı."), onError: (e) => toast("error", errorMessage(e)) },
                        )
                      : navigate(`/tasks?open=${t.id}`)
                  }
                  className="size-6 shrink-0 rounded-md border-2 border-border hover:border-primary"
                />
                <Link to={`/tasks?open=${t.id}`} className="min-w-0 flex-1">
                  <p className="truncate font-semibold text-text">{t.title}</p>
                  <p className="truncate text-sm text-muted">
                    {t.teamName} · {t.backupAssignee ? `Yedek: ${t.backupAssignee.fullName}` : "Yedek yok"}
                  </p>
                </Link>
                <span className={cx("hidden rounded-full px-3 py-1 text-sm font-medium sm:inline", PRIORITY_TONE[t.priority])}>
                  {priorityLabel[t.priority]}
                </span>
                <span className={cx("hidden w-24 items-center gap-1.5 border-l border-border pl-4 text-sm md:flex", due.late ? "text-danger" : "text-text")}>
                  <Clock className="size-4" aria-hidden />
                  {due.text}
                </span>
                {t.assignee && <span title={t.assignee.fullName}><Avatar name={t.assignee.fullName} size="lg" /></span>}
              </li>
            );
          })}
        </ul>
      )}
      <Link to={assigneeOnly ? "/tasks?assigneeId=me" : "/tasks"} className="inline-flex items-center gap-1.5 px-5 py-4 text-sm font-medium text-primary hover:underline">
        Tüm görevleri gör <ArrowRight className="size-4" />
      </Link>
    </Card>
  );
}

function BackupCallout({ count }: { count: number }) {
  return (
    <section className="flex gap-4 rounded-2xl border border-accent/40 bg-accent-soft p-6" aria-label="Yedek sorumlu eksikleri">
      <ShieldCheck className="size-11 shrink-0 fill-accent stroke-primary" strokeWidth={1.8} aria-hidden />
      <div>
        <h2 className="text-xl font-semibold text-text">Yedekleri tamamla</h2>
        <p className="mt-1 text-sm text-muted">{count} görev için yedek sorumlu bekleniyor.</p>
        <Link
          to="/tasks?hasBackup=false&status=TODO,IN_PROGRESS,BLOCKED"
          className="mt-4 inline-flex items-center gap-2 rounded-xl bg-primary px-5 py-2.5 text-sm font-medium text-on-primary hover:bg-primary-hover"
        >
          Sorumlu ata <ArrowRight className="size-4" />
        </Link>
      </div>
    </section>
  );
}

function UpcomingEvent() {
  const events = useEvents({ from: isoDate(new Date()) });
  const next = useMemo(() => {
    const now = Date.now();
    return (events.data?.items ?? [])
      .filter((e) => new Date(e.startsAt).getTime() >= now)
      .sort((a, b) => a.startsAt.localeCompare(b.startsAt))[0];
  }, [events.data]);
  const people = useParticipations(next?.id);
  const active = (people.data ?? []).filter((p) => ["REQUESTED", "APPROVED", "ATTENDED"].includes(p.status));
  const start = next ? new Date(next.startsAt) : null;
  const end = next ? new Date(next.endsAt) : null;
  const time = (x: Date) => x.toLocaleTimeString("tr-TR", { hour: "2-digit", minute: "2-digit" });
  return (
    <Card className="flex-1 rounded-2xl">
      <div className="flex items-center justify-between px-5 pt-5 pb-3">
        <h2 className="text-xl font-semibold text-text">Yaklaşan etkinlik</h2>
        <Link to="/events" className="text-sm text-primary hover:underline">Tümü</Link>
      </div>
      {events.isPending ? (
        <Skeleton className="mx-5 mb-5 h-20" />
      ) : !next || !start || !end ? (
        <EmptyState title="Yaklaşan etkinlik yok" />
      ) : (
        <Link to="/events" className="mx-5 mb-5 flex items-center gap-4 rounded-xl hover:bg-surface-2">
          <span className="grid size-20 shrink-0 place-content-center rounded-xl bg-info-soft text-center text-primary">
            <span className="text-3xl leading-none font-semibold">{start.getDate()}</span>
            <span className="text-sm font-medium uppercase">{start.toLocaleDateString("tr-TR", { month: "short" })}</span>
          </span>
          <span className="min-w-0 flex-1 border-l border-border pl-4">
            <span className="block truncate font-semibold text-text">{next.title}</span>
            <span className="mt-1 flex items-center gap-1.5 text-sm text-muted">
              <Clock className="size-4" aria-hidden />
              {start.toDateString() === end.toDateString() ? `${time(start)} – ${time(end)}` : `${fmtDate(next.startsAt)} – ${fmtDate(next.endsAt)}`}
            </span>
          </span>
          <span className="hidden shrink-0 flex-col items-end gap-1 sm:flex">
            <span className="flex -space-x-2">
              {active.slice(0, 3).map((p) => (
                <span key={p.id} className="rounded-full ring-2 ring-surface" title={p.user.fullName}>
                  <Avatar name={p.user.fullName} />
                </span>
              ))}
              {active.length > 3 && (
                <span className="grid size-8 place-items-center rounded-full bg-surface-2 text-xs font-semibold text-text ring-2 ring-surface">
                  +{active.length - 3}
                </span>
              )}
            </span>
            <span className="text-xs text-muted">{next.participantCount ?? active.length} katılımcı</span>
          </span>
        </Link>
      )}
    </Card>
  );
}

function TeamStatus({ kind, rows, avgProgress }: { kind: Exclude<Kind, "NONE">; rows: Schemas["DashboardBreakdownRow"][]; avgProgress: number }) {
  const shown = kind === "MEMBER" ? [...rows].sort((a, b) => b.all.total - a.all.total).slice(0, 8) : rows;
  return (
    <Card className="rounded-2xl">
      <div className="flex flex-wrap items-center justify-between gap-2 px-5 pt-5 pb-2">
        <h2 className="text-xl font-semibold text-text">{STATUS_TITLE[kind]}</h2>
        <span className="text-sm text-muted">
          Ort. ilerleme <span className="font-semibold text-primary">%{avgProgress}</span>
          {kind === "MEMBER" && rows.length > shown.length && (
            <a href="#ayrintili-durum" className="ml-3 text-primary hover:underline">Tümü ({rows.length})</a>
          )}
        </span>
      </div>
      {shown.length === 0 ? (
        <EmptyState title={KIND_TEXT[kind].empty} />
      ) : (
        <ul className="grid gap-x-6 gap-y-5 px-5 pt-2 pb-5 sm:grid-cols-2 xl:grid-cols-4">
          {shown.map((r) => {
            const done = pct(r.all.done, r.all.total);
            return (
              <li key={r.id} className="flex items-center gap-4">
                <span className="grid size-12 shrink-0 place-items-center rounded-xl bg-info-soft text-primary" aria-hidden>
                  <Users className="size-5" />
                </span>
                <div className="min-w-0 flex-1">
                  <p className="truncate font-semibold text-text" title={r.sublabel ?? undefined}>{r.label}</p>
                  {r.sublabel && <p className="truncate text-xs text-muted">{r.sublabel}</p>}
                  <div className="mt-1.5 flex items-center gap-3">
                    <span
                      className="h-2 flex-1 overflow-hidden rounded-full bg-surface-2"
                      role="progressbar"
                      aria-label={`${r.label} tamamlanma`}
                      aria-valuenow={done}
                      aria-valuemin={0}
                      aria-valuemax={100}
                    >
                      <span className="block h-full rounded-full bg-primary" style={{ width: `${done}%` }} />
                    </span>
                    <span className="tabular w-10 text-right text-sm text-text">%{done}</span>
                  </div>
                </div>
              </li>
            );
          })}
        </ul>
      )}
    </Card>
  );
}

/** Rol bazlı ayrıntılı kırılım: grafik + tablo (yönetici, unit yöneticisi, direktör/denetmen). */
function DetailedBreakdown() {
  const [part, setPart] = useState<Part>("all");
  const [teamId, setTeamId] = useState<string>("");
  const teams = useTeams();
  const dash = useDashboard(teamId ? { teamId } : {});
  const d = dash.data;
  const kind: Kind | undefined = d?.breakdown.kind;
  const rows = d?.breakdown.rows ?? [];
  const text = kind && kind !== "NONE" ? KIND_TEXT[kind] : undefined;
  const horizontal = kind === "MEMBER";
  const chartData = rows.map((r) => ({
    name: r.label,
    Başlanmadı: r[part].todo,
    "Devam ediyor": r[part].inProgress,
    Bloklu: r[part].blocked,
    Tamamlandı: r[part].done,
    Puan: r.score,
  }));
  return (
    <section id="ayrintili-durum" className="space-y-6 scroll-mt-6" aria-label="Ayrıntılı durum">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <h2 className="text-xl font-semibold text-text">Ayrıntılı durum</h2>
        <div className="flex flex-wrap items-center gap-2">
          {(teams.data?.length ?? 0) > 1 && (
            <Select aria-label="Ekip filtresi" value={teamId} onChange={(e) => setTeamId(e.target.value)} className="w-56">
              <option value="">Tüm ekipler</option>
              <TeamOptions teams={teams.data} />
            </Select>
          )}
          <Tabs<Part>
            value={part}
            onChange={setPart}
            items={(["all", "standard", "project"] as const).map((v) => ({ value: v, label: PART_LABEL[v] }))}
          />
        </div>
      </div>
<Card>
                <CardHeader
                  title={text?.chart ?? "Durum"}
                  subtitle={kind === "TEAM_MANAGER" ? SCORE_HINT : PART_LABEL[part]}
                />
                {/* Çalışan kırılımında satır çok olabilir: isimler okunaklı kalsın diye yatay çubuk, yükseklik satır sayısına göre. */}
                <div className="px-2 py-4" style={{ height: horizontal ? Math.max(288, chartData.length * 28 + 64) : 288 }}>
                  {!d ? (
                    <Skeleton className="m-4 h-60" />
                  ) : chartData.length === 0 ? (
                    <EmptyState title={text?.empty ?? "Veri yok"} />
                  ) : (
                    <ResponsiveContainer width="100%" height="100%">
                      <BarChart data={chartData} layout={horizontal ? "vertical" : "horizontal"} margin={{ left: 0, right: 16 }}>
                        <CartesianGrid strokeDasharray="3 3" stroke="var(--border)" vertical={horizontal} horizontal={!horizontal} />
                        {horizontal
                          ? [
                              <XAxis key="x" type="number" tick={AXIS_TICK} axisLine={false} tickLine={false} allowDecimals={false} />,
                              <YAxis key="y" type="category" dataKey="name" width={150} tick={AXIS_TICK} axisLine={false} tickLine={false} interval={0} />,
                            ]
                          : [
                              <XAxis key="x" dataKey="name" tick={AXIS_TICK} axisLine={false} tickLine={false} interval={0} />,
                              <YAxis
                                key="y"
                                tick={AXIS_TICK}
                                axisLine={false}
                                tickLine={false}
                                allowDecimals={false}
                                domain={kind === "TEAM_MANAGER" ? [0, 100] : undefined}
                              />,
                            ]}
                        <Tooltip
                          cursor={{ fill: "var(--surface-2)" }}
                          contentStyle={{ background: "var(--surface)", border: "1px solid var(--border)", borderRadius: 8, color: "var(--text)" }}
                          itemStyle={{ color: "var(--text)" }}
                        />
                        {/* Recharts alt bileşenleri Fragment içinde görmez; dizi olarak verilmeli. */}
                        {kind === "TEAM_MANAGER"
                          ? [<Bar key="score" dataKey="Puan" fill="var(--primary)" radius={[4, 4, 0, 0]} />]
                          : [
                              <Legend key="legend" wrapperStyle={{ fontSize: 12 }} formatter={legendText} />,
                              <Bar key="todo" dataKey="Başlanmadı" stackId="a" fill="var(--chart-todo)" />,
                              <Bar key="prog" dataKey="Devam ediyor" stackId="a" fill="var(--chart-progress)" />,
                              <Bar key="blk" dataKey="Bloklu" stackId="a" fill="var(--chart-blocked)" />,
                              <Bar
                                key="done"
                                dataKey="Tamamlandı"
                                stackId="a"
                                fill="var(--chart-done)"
                                radius={horizontal ? [0, 4, 4, 0] : [4, 4, 0, 0]}
                              />,
                            ]}
                      </BarChart>
                    </ResponsiveContainer>
                  )}
                </div>
              </Card>
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
    </section>
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

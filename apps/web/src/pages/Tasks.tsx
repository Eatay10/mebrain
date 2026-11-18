import { Paperclip, Plus, Repeat, Search, Star, Users } from "lucide-react";
import { useEffect, useMemo, useState } from "react";
import { useSearchParams } from "react-router";
import { useTasks, useTeams, type Schemas, type TaskFilters } from "../api/hooks";
import { useAuth } from "../auth";
import {
  Badge,
  Button,
  Card,
  cx,
  EmptyState,
  ErrorState,
  Input,
  PageHeader,
  Pagination,
  PriorityBadge,
  Select,
  Skeleton,
  StatusBadge,
} from "../components/ui";
import { priorityLabel, statusLabel, typeLabel } from "../i18n/tr";
import { fmtDate } from "../lib/format";
import { TaskDetailModal } from "./TaskDetail";
import { TaskFormModal } from "./TaskForm";
import { TeamOptions } from "../components/TeamOptions";

const STATUSES: Schemas["TaskStatus"][] = ["TODO", "IN_PROGRESS", "BLOCKED", "DONE"];
type Sort = NonNullable<TaskFilters["sort"]>;

export function TasksPage({ projectId, embedded }: { projectId?: string; embedded?: boolean } = {}) {
  const { can, session } = useAuth();
  const [params, setParams] = useSearchParams();
  const teams = useTeams();
  const [q, setQ] = useState(params.get("q") ?? "");
  const [creating, setCreating] = useState(false);

  const set = (key: string, value?: string | null) => {
    const next = new URLSearchParams(params);
    if (value) next.set(key, value);
    else next.delete(key);
    if (key !== "page" && key !== "open") next.delete("page");
    setParams(next, { replace: key === "q" });
  };
  useEffect(() => {
    const t = setTimeout(() => q !== (params.get("q") ?? "") && set("q", q.trim() || null), 300);
    return () => clearTimeout(t);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [q]);

  const statuses = params.get("status")?.split(",").filter(Boolean) ?? [];
  const page = Number(params.get("page") ?? 1);
  const filters: TaskFilters = useMemo(
    () => ({
      q: params.get("q") || undefined,
      status: statuses.length ? (statuses as Schemas["TaskStatus"][]) : undefined,
      priority: params.get("priority") ? [params.get("priority") as Schemas["TaskPriority"]] : undefined,
      type: (params.get("type") as Schemas["TaskType"]) || undefined,
      teamId: params.get("teamId") || undefined,
      projectId,
      assigneeId: params.get("assigneeId") || undefined,
      overdue: params.get("overdue") === "true" ? true : undefined,
      recurring: params.get("recurring") === "true" ? true : undefined,
      watching: params.get("watching") === "true" ? true : undefined,
      sort: (params.get("sort") as Sort) || "-updatedAt",
      page,
      pageSize: 20,
    }),
    // eslint-disable-next-line react-hooks/exhaustive-deps
    [params, projectId],
  );
  const tasks = useTasks(filters);
  const toggleStatus = (s: string) => {
    const next = statuses.includes(s) ? statuses.filter((x) => x !== s) : [...statuses, s];
    set("status", next.join(",") || null);
  };
  const canCreate = !can.readOnly && (can.manage || !!session.user.teamId);

  return (
    <>
      {!embedded && (
        <PageHeader
          title="Task'lar"
          subtitle="Günlük, rutin ve proje task'ları"
          actions={canCreate && <Button onClick={() => setCreating(true)}><Plus className="size-4" />Yeni task</Button>}
        />
      )}
      <Card>
        <div className="flex flex-wrap items-center gap-3 border-b border-border px-5 py-4">
          <div className="relative min-w-56 flex-1">
            <Search className="pointer-events-none absolute top-1/2 left-3 size-4 -translate-y-1/2 text-muted" aria-hidden />
            <Input aria-label="Task ara" placeholder="Başlık veya açıklamada ara…" value={q} onChange={(e) => setQ(e.target.value)} className="pl-9" maxLength={100} />
          </div>
          <Select aria-label="Ekip" value={params.get("teamId") ?? ""} onChange={(e) => set("teamId", e.target.value)} className="w-44">
            <option value="">Tüm ekipler</option>
            <TeamOptions teams={teams.data} />
          </Select>
          <Select aria-label="Tür" value={params.get("type") ?? ""} onChange={(e) => set("type", e.target.value)} className="w-36">
            <option value="">Tüm türler</option>
            <option value="STANDARD">Standart</option>
            <option value="PROJECT">Proje</option>
          </Select>
          <Select aria-label="Öncelik" value={params.get("priority") ?? ""} onChange={(e) => set("priority", e.target.value)} className="w-36">
            <option value="">Tüm öncelikler</option>
            {Object.entries(priorityLabel).map(([k, l]) => <option key={k} value={k}>{l}</option>)}
          </Select>
          <Select aria-label="Sıralama" value={filters.sort} onChange={(e) => set("sort", e.target.value)} className="w-44">
            <option value="-updatedAt">Son güncellenen</option>
            <option value="dueDate">Son tarih (yakın)</option>
            <option value="-priority">Öncelik (yüksek)</option>
            <option value="-createdAt">En yeni</option>
          </Select>
        </div>
        <div className="flex flex-wrap items-center gap-2 border-b border-border px-5 py-3" role="group" aria-label="Hızlı filtreler">
          {STATUSES.map((s) => (
            <Chip key={s} active={statuses.includes(s)} onClick={() => toggleStatus(s)}>{statusLabel[s]}</Chip>
          ))}
          <span className="mx-1 h-5 w-px bg-border" />
          <Chip active={params.get("assigneeId") === "me"} onClick={() => set("assigneeId", params.get("assigneeId") === "me" ? null : "me")}>Bana atanan</Chip>
          <Chip active={params.get("watching") === "true"} onClick={() => set("watching", params.get("watching") ? null : "true")}>
            <Star className="size-3" aria-hidden />Yıldızlılar
          </Chip>
          <Chip active={params.get("overdue") === "true"} onClick={() => set("overdue", params.get("overdue") ? null : "true")}>Gecikmiş</Chip>
          <Chip active={params.get("recurring") === "true"} onClick={() => set("recurring", params.get("recurring") ? null : "true")}>
            <Repeat className="size-3" />Rutin şablonlar
          </Chip>
          {params.toString() && params.toString() !== "open=" && (
            <Button variant="ghost" size="sm" onClick={() => (setQ(""), setParams(new URLSearchParams()))}>Filtreleri temizle</Button>
          )}
        </div>

        {tasks.error ? (
          <ErrorState message="Task'lar yüklenemedi." onRetry={() => void tasks.refetch()} />
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead className="bg-surface-2 text-left text-xs text-muted uppercase">
                <tr>
                  <th scope="col" className="px-5 py-3 font-medium">Task</th>
                  <th scope="col" className="px-3 py-3 font-medium">Durum</th>
                  <th scope="col" className="hidden px-3 py-3 font-medium sm:table-cell">İlerleme</th>
                  <th scope="col" className="hidden px-3 py-3 font-medium md:table-cell">Öncelik</th>
                  <th scope="col" className="hidden px-3 py-3 font-medium lg:table-cell">Sorumlu</th>
                  <th scope="col" className="px-3 py-3 font-medium">Son tarih</th>
                </tr>
              </thead>
              <tbody className={cx(tasks.isPlaceholderData && "opacity-60")}>
                {tasks.isPending
                  ? Array.from({ length: 8 }).map((_, i) => (
                      <tr key={i} className="border-t border-border"><td colSpan={6} className="px-5 py-3"><Skeleton className="h-6" /></td></tr>
                    ))
                  : tasks.data.items.map((t) => (
                      <tr key={t.id} className="cursor-pointer border-t border-border hover:bg-surface-2" onClick={() => set("open", t.id)}>
                        <td className="max-w-md px-5 py-3">
                          <button className="text-left font-medium text-text hover:text-primary" onClick={(e) => (e.stopPropagation(), set("open", t.id))}>
                            {t.title}
                          </button>
                          <p className="mt-0.5 flex flex-wrap items-center gap-1.5 text-xs text-muted">
                            <span>{t.teamName}</span>·<span>{typeLabel[t.type]}</span>
                            {t.project && <>·<span className="truncate">{t.project.name}</span></>}
                            {t.recurrence !== "NONE" && <Badge className="bg-primary-soft text-primary"><Repeat className="size-3" />Rutin</Badge>}
                            {t.isWatching && <Star className="size-3 fill-blocked text-blocked" aria-label="Yıldızlı" />}
                            {(t.collaborators?.length ?? 0) > 0 && (
                              <span className="inline-flex items-center gap-0.5" title={t.collaborators!.map((c) => c.fullName).join(", ")}>
                                <Users className="size-3" aria-hidden />+{t.collaborators!.length}
                              </span>
                            )}
                            {(t.attachmentCount ?? 0) > 0 && (
                              <span className="inline-flex items-center gap-0.5"><Paperclip className="size-3" aria-hidden />{t.attachmentCount}</span>
                            )}
                          </p>
                        </td>
                        <td className="px-3 py-3"><StatusBadge status={t.status} /></td>
                        <td className="hidden px-3 py-3 sm:table-cell">
                          <div className="flex items-center gap-2">
                            <div className="h-1.5 w-16 overflow-hidden rounded-full bg-surface-2" aria-hidden>
                              <div className={cx("h-full rounded-full", t.progress >= 100 ? "bg-done" : "bg-primary")} style={{ width: `${t.progress}%` }} />
                            </div>
                            <span className="tabular text-xs text-muted">%{t.progress}</span>
                          </div>
                        </td>
                        <td className="hidden px-3 py-3 md:table-cell"><PriorityBadge priority={t.priority} /></td>
                        <td className="hidden px-3 py-3 text-text lg:table-cell">{t.assignee?.fullName ?? <span className="text-muted">Atanmamış</span>}</td>
                        <td className={cx("px-3 py-3 whitespace-nowrap", t.isOverdue ? "font-medium text-danger" : "text-text")}>{fmtDate(t.dueDate)}</td>
                      </tr>
                    ))}
              </tbody>
            </table>
            {tasks.data && tasks.data.total === 0 && (
              <EmptyState title="Eşleşen task yok" description="Filtreleri değiştirin veya yeni bir task oluşturun." />
            )}
          </div>
        )}
        {tasks.data && tasks.data.total > 0 && (
          <Pagination page={page} pageSize={20} total={tasks.data.total} onPage={(p) => set("page", String(p))} />
        )}
      </Card>
      <TaskDetailModal taskId={params.get("open")} onClose={() => set("open", null)} />
      <TaskFormModal open={creating} onClose={() => setCreating(false)} />
    </>
  );
}

function Chip({ active, onClick, children }: { active: boolean; onClick: () => void; children: React.ReactNode }) {
  return (
    <button
      onClick={onClick}
      aria-pressed={active}
      className={cx(
        "inline-flex items-center gap-1 rounded-full border px-3 py-1 text-xs font-medium transition-colors",
        active ? "border-primary bg-primary-soft text-primary" : "border-border text-muted hover:text-text",
      )}
    >
      {children}
    </button>
  );
}

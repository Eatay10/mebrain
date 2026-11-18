import { CalendarClock, Download, MessageSquare, Paperclip, Pencil, Repeat, Star, Trash2, TrendingUp } from "lucide-react";
import { useState } from "react";
import {
  errorMessage,
  useAddComment,
  useAttachments,
  useComments,
  useDeleteAttachment,
  useDeleteTask,
  useTask,
  useTaskHistory,
  useTaskProgress,
  useTransitionTask,
  useUpdateProgress,
  useUploadAttachment,
  useWatchers,
  useWatchToggle,
  type Schemas,
} from "../api/hooks";
import { useAuth } from "../auth";
import {
  Avatar,
  Badge,
  Button,
  EmptyState,
  ErrorState,
  Field,
  Input,
  Modal,
  PriorityBadge,
  Spinner,
  StatusBadge,
  Tabs,
  Textarea,
  useToast,
} from "../components/ui";
import { categoryLabel, recurrenceLabel, statusLabel, typeLabel } from "../i18n/tr";
import { fmtDate, fmtDateTime, fmtRelative } from "../lib/format";
import { TaskFormModal } from "./TaskForm";

type Status = Schemas["TaskStatus"];
// knowledge/domain/task-lifecycle.md — "M" sadece yönetici+.
const NEXT: Record<Status, Array<{ to: Status; label: string; managerOnly?: boolean }>> = {
  TODO: [{ to: "IN_PROGRESS", label: "Başla" }, { to: "BLOCKED", label: "Blokla" }],
  IN_PROGRESS: [{ to: "DONE", label: "Tamamla" }, { to: "BLOCKED", label: "Blokla" }],
  BLOCKED: [{ to: "IN_PROGRESS", label: "Devam et" }, { to: "TODO", label: "Başlanmadıya al" }],
  DONE: [{ to: "IN_PROGRESS", label: "Yeniden aç", managerOnly: true }],
};

export function TaskDetailModal({ taskId, onClose }: { taskId: string | null; onClose: () => void }) {
  const task = useTask(taskId ?? undefined);
  return (
    <Modal open={!!taskId} onClose={onClose} title={task.data?.title ?? "Task"} wide>
      {task.isPending ? (
        <Spinner />
      ) : task.error ? (
        <ErrorState message={errorMessage(task.error)} />
      ) : (
        <TaskDetailBody task={task.data} onDeleted={onClose} />
      )}
    </Modal>
  );
}

function TaskDetailBody({ task, onDeleted }: { task: Schemas["Task"]; onDeleted: () => void }) {
  const { user, can, managesTeam } = useAuth();
  const toast = useToast();
  const transition = useTransitionTask();
  const del = useDeleteTask();
  const [tab, setTab] = useState<"comments" | "timeline" | "history">("timeline");
  const watch = useWatchToggle(task.id);
  const [editing, setEditing] = useState(false);
  const [blockOpen, setBlockOpen] = useState(false);
  const [reason, setReason] = useState("");
  const manager = managesTeam(task.teamId);
  const involved =
    user.id === task.assignee?.id ||
    user.id === task.backupAssignee?.id ||
    (task.collaborators ?? []).some((c) => c.id === user.id);
  const actions = can.readOnly ? [] : NEXT[task.status].filter((a) => (a.managerOnly ? manager : manager || involved));

  const go = (to: Status, r?: string) =>
    transition.mutate(
      { id: task.id, to, version: task.version, reason: r },
      {
        onSuccess: () => toast("success", `Durum: ${statusLabel[to]}`),
        onError: (e) => toast("error", errorMessage(e)),
      },
    );

  return (
    <div className="space-y-5">
      <div className="flex flex-wrap items-center gap-2">
        <StatusBadge status={task.status} />
        <Badge className="bg-surface-2 text-muted">{typeLabel[task.type]}</Badge>
        {task.recurrence !== "NONE" && (
          <Badge className="bg-primary-soft text-primary"><Repeat className="size-3" />{recurrenceLabel[task.recurrence]}</Badge>
        )}
        {task.isOverdue && <Badge className="bg-danger-soft text-danger"><CalendarClock className="size-3" />Gecikmiş</Badge>}
        <span className="ml-auto flex flex-wrap gap-2">
          <Button
            size="sm"
            variant="ghost"
            aria-pressed={task.isWatching}
            aria-label={task.isWatching ? "Yıldızı kaldır" : "Yıldız koy (takip et)"}
            title={task.isWatching ? "Takip ediliyor — her güncellemede bildirim alırsınız" : "Takip et"}
            loading={watch.isPending}
            onClick={() =>
              watch.mutate(!task.isWatching, {
                onSuccess: () => toast("success", task.isWatching ? "Takip bırakıldı." : "Task takip ediliyor; güncellemelerde bildirim alacaksınız."),
                onError: (e) => toast("error", errorMessage(e)),
              })
            }
          >
            <Star className={task.isWatching ? "size-4 fill-blocked text-blocked" : "size-4"} />
            <span className="tabular text-xs">{task.watcherCount}</span>
          </Button>
          {actions.map((a) => (
            <Button
              key={a.to}
              size="sm"
              variant={a.to === "DONE" ? "primary" : "secondary"}
              loading={transition.isPending && transition.variables?.to === a.to}
              onClick={() => (a.to === "BLOCKED" ? setBlockOpen(true) : go(a.to))}
            >
              {a.label}
            </Button>
          ))}
          {manager && !can.readOnly && (
            <>
              <Button size="sm" variant="ghost" onClick={() => setEditing(true)} aria-label="Düzenle"><Pencil className="size-4" /></Button>
              <Button
                size="sm"
                variant="ghost"
                aria-label="Sil"
                onClick={() =>
                  confirm("Bu task silinsin mi?") &&
                  del.mutate(task.id, {
                    onSuccess: () => (toast("success", "Task silindi."), onDeleted()),
                    onError: (e) => toast("error", errorMessage(e)),
                  })
                }
              >
                <Trash2 className="size-4 text-danger" />
              </Button>
            </>
          )}
        </span>
      </div>

      {task.status === "BLOCKED" && task.blockedReason && (
        <p className="rounded-lg bg-warning-soft px-3 py-2 text-sm text-blocked">Blok nedeni: {task.blockedReason}</p>
      )}

      <ProgressPanel task={task} canUpdate={!can.readOnly && (manager || involved)} />

      <dl className="grid grid-cols-2 gap-x-6 gap-y-3 text-sm sm:grid-cols-3">
        {[
          ["Ekip", task.teamName],
          ["Proje", task.project?.name ?? "—"],
          ["Kategori", categoryLabel[task.category]],
          ["Öncelik", <PriorityBadge key="p" priority={task.priority} />],
          ["Talep sahibi", task.requester?.fullName ?? "—"],
          ["Sorumlu", task.assignee?.fullName ?? "Atanmamış"],
          ["Yedek", task.backupAssignee?.fullName ?? "—"],
          [
            "Çalışma arkadaşları",
            task.collaborators?.length ? task.collaborators.map((c) => c.fullName).join(", ") : "—",
          ],
          ["Takip edenler", <Watchers key="w" taskId={task.id} />],
          ["Son tarih", fmtDate(task.dueDate)],
          ["Başlangıç", fmtDateTime(task.startedAt)],
          ["Tamamlanma", fmtDateTime(task.completedAt)],
        ].map(([k, v]) => (
          <div key={String(k)}>
            <dt className="text-xs text-muted">{k}</dt>
            <dd className="mt-0.5 text-text">{v}</dd>
          </div>
        ))}
      </dl>

      {task.description && (
        <div>
          <h3 className="mb-1 text-xs text-muted">Açıklama</h3>
          {/* Kullanıcı içeriği düz metin olarak render edilir (XSS koruması, T06). */}
          <p className="text-sm whitespace-pre-wrap text-text">{task.description}</p>
        </div>
      )}

      <Attachments task={task} canAdd={!can.readOnly && (manager || involved || task.requester?.id === user.id)} manager={manager} />

      <div className="space-y-3 border-t border-border pt-4">
        <Tabs
          value={tab}
          onChange={setTab}
          items={[
            { value: "timeline", label: "İlerleme tarihçesi" },
            { value: "comments", label: `Yorumlar (${task.commentCount ?? 0})` },
            { value: "history", label: "Geçmiş" },
          ]}
        />
        {tab === "comments" ? <Comments task={task} /> : tab === "timeline" ? <Timeline taskId={task.id} /> : <History taskId={task.id} />}
      </div>

      <TaskFormModal open={editing} onClose={() => setEditing(false)} task={task} />
      <Modal
        open={blockOpen}
        onClose={() => setBlockOpen(false)}
        title="Task'ı blokla"
        footer={
          <>
            <Button variant="secondary" onClick={() => setBlockOpen(false)}>Vazgeç</Button>
            <Button
              disabled={!reason.trim()}
              onClick={() => {
                go("BLOCKED", reason.trim());
                setBlockOpen(false);
                setReason("");
              }}
            >
              Blokla
            </Button>
          </>
        }
      >
        <Field label="Blok nedeni" htmlFor="block-reason" hint="Zorunlu; ekip ve yönetici bilgilendirilir.">
          <Input id="block-reason" value={reason} onChange={(e) => setReason(e.target.value)} maxLength={500} autoFocus />
        </Field>
      </Modal>
    </div>
  );
}

function Comments({ task }: { task: Schemas["Task"] }) {
  const { can } = useAuth();
  const toast = useToast();
  const comments = useComments(task.id);
  const add = useAddComment(task.id);
  const [body, setBody] = useState("");
  return (
    <div className="space-y-3">
      {comments.isPending ? (
        <Spinner />
      ) : comments.error ? (
        <ErrorState message={errorMessage(comments.error)} />
      ) : comments.data.items.length === 0 ? (
        <EmptyState title="Henüz yorum yok" />
      ) : (
        <ul className="space-y-3">
          {comments.data.items.map((c) => (
            <li key={c.id} className="flex gap-3">
              <Avatar name={c.author.fullName} size="sm" />
              <div className="min-w-0 flex-1 rounded-lg bg-surface-2 px-3 py-2">
                <p className="text-xs text-muted"><span className="font-medium text-text">{c.author.fullName}</span> · {fmtRelative(c.createdAt)}</p>
                <p className="mt-0.5 text-sm whitespace-pre-wrap text-text">{c.body}</p>
              </div>
            </li>
          ))}
        </ul>
      )}
      {!can.readOnly && (
        <form
          className="flex flex-col gap-2"
          onSubmit={(e) => {
            e.preventDefault();
            if (!body.trim()) return;
            add.mutate(body.trim(), { onSuccess: () => setBody(""), onError: (err) => toast("error", errorMessage(err)) });
          }}
        >
          <label htmlFor="comment" className="sr-only">Yorum</label>
          <Textarea id="comment" value={body} onChange={(e) => setBody(e.target.value)} placeholder="Yorum yazın…" maxLength={5000} className="min-h-16" />
          <div className="flex justify-end">
            <Button size="sm" type="submit" loading={add.isPending} disabled={!body.trim()}>
              <MessageSquare className="size-4" /> Gönder
            </Button>
          </div>
        </form>
      )}
    </div>
  );
}

function ProgressBar({ value, className }: { value: number; className?: string }) {
  return (
    <div className={`h-2 overflow-hidden rounded-full bg-surface-2 ${className ?? ""}`} role="progressbar" aria-valuenow={value} aria-valuemin={0} aria-valuemax={100} aria-label="İlerleme">
      <div className={`h-full rounded-full ${value >= 100 ? "bg-done" : "bg-primary"}`} style={{ width: `${value}%` }} />
    </div>
  );
}

function ProgressPanel({ task, canUpdate }: { task: Schemas["Task"]; canUpdate: boolean }) {
  const toast = useToast();
  const update = useUpdateProgress(task.id);
  const [value, setValue] = useState(task.progress);
  const [note, setNote] = useState("");
  const [open, setOpen] = useState(false);
  return (
    <div className="rounded-lg border border-border p-3">
      <div className="flex items-center gap-3">
        <TrendingUp className="size-4 text-muted" aria-hidden />
        <span className="text-sm font-medium">İlerleme</span>
        <ProgressBar value={task.progress} className="flex-1" />
        <span className="tabular w-12 text-right text-sm font-semibold">%{task.progress}</span>
        {canUpdate && !open && (
          <Button size="sm" variant="secondary" onClick={() => (setValue(task.progress), setOpen(true))}>
            Güncelle
          </Button>
        )}
      </div>
      {open && (
        <form
          className="mt-3 grid gap-3 sm:grid-cols-[1fr_auto]"
          onSubmit={(e) => {
            e.preventDefault();
            update.mutate(
              { progress: value, note: note.trim(), version: task.version },
              {
                onSuccess: () => (toast("success", `İlerleme %${value} olarak kaydedildi; takipçiler bilgilendirildi.`), setOpen(false), setNote("")),
                onError: (err) => toast("error", errorMessage(err)),
              },
            );
          }}
        >
          <div className="space-y-2">
            <label htmlFor="progress-range" className="flex items-center justify-between text-xs text-muted">
              <span>Yeni ilerleme</span>
              <span className="tabular text-sm font-semibold text-text">%{task.progress} → %{value}</span>
            </label>
            <input id="progress-range" type="range" min={0} max={100} step={5} value={value} onChange={(e) => setValue(Number(e.target.value))} className="w-full accent-[var(--color-primary)]" />
            <Field label="Kısa not" htmlFor="progress-note" hint="Takipçilere giden bildirime eklenir. Örn: Test ortamı doğrulandı">
              <Input id="progress-note" value={note} onChange={(e) => setNote(e.target.value)} maxLength={500} required />
            </Field>
          </div>
          <div className="flex items-end gap-2">
            <Button variant="secondary" type="button" onClick={() => setOpen(false)}>Vazgeç</Button>
            <Button type="submit" loading={update.isPending} disabled={!note.trim() || value === task.progress}>Kaydet</Button>
          </div>
        </form>
      )}
    </div>
  );
}

function Timeline({ taskId }: { taskId: string }) {
  const t = useTaskProgress(taskId);
  if (t.isPending) return <Spinner />;
  if (t.error) return <ErrorState message={errorMessage(t.error)} />;
  if (!t.data.length) return <EmptyState title="Henüz ilerleme kaydı yok" description="İlerleme güncellendikçe burada kronolojik olarak listelenir." />;
  return (
    <ol className="relative space-y-4 border-l border-border pl-5">
      {t.data.map((e) => (
        <li key={e.id} className="relative">
          <span className={`absolute top-1 -left-[1.6rem] size-3 rounded-full border-2 border-surface ${e.toProgress >= 100 ? "bg-done" : "bg-primary"}`} aria-hidden />
          <p className="text-xs text-muted">{fmtDateTime(e.createdAt)}</p>
          <p className="text-sm text-text">
            <span className="font-medium">{e.author.fullName}</span> ilerlemeyi{" "}
            <span className="tabular font-semibold">%{e.fromProgress} → %{e.toProgress}</span> yaptı
          </p>
          <p className="mt-0.5 text-sm whitespace-pre-wrap text-muted">{e.note}</p>
        </li>
      ))}
    </ol>
  );
}

function Watchers({ taskId }: { taskId: string }) {
  const w = useWatchers(taskId);
  if (w.isPending) return <span className="text-muted">…</span>;
  if (w.error || !w.data.length) return <span>—</span>;
  return <span>{w.data.map((u) => u.fullName).join(", ")}</span>;
}

function fmtSize(n: number): string {
  return n < 1024 ? `${n} B` : n < 1024 * 1024 ? `${(n / 1024).toFixed(0)} KB` : `${(n / 1024 / 1024).toFixed(1)} MB`;
}

function Attachments({ task, canAdd, manager }: { task: Schemas["Task"]; canAdd: boolean; manager: boolean }) {
  const { user } = useAuth();
  const toast = useToast();
  const list = useAttachments(task.id);
  const up = useUploadAttachment(task.id);
  const del = useDeleteAttachment(task.id);
  return (
    <div>
      <div className="mb-2 flex items-center gap-2">
        <Paperclip className="size-4 text-muted" aria-hidden />
        <h3 className="text-sm font-medium">Ekler ({list.data?.length ?? task.attachmentCount ?? 0})</h3>
        {canAdd && (
          <label className="ml-auto inline-flex cursor-pointer items-center gap-1.5 rounded-lg bg-surface-2 px-3 py-1.5 text-xs font-medium hover:bg-primary-soft">
            {up.isPending ? "Yükleniyor…" : "Dosya ekle"}
            <input
              type="file"
              className="sr-only"
              aria-label="Dosya ekle"
              onChange={(e) => {
                const f = e.target.files?.[0];
                e.target.value = "";
                if (!f) return;
                if (f.size > 10 * 1024 * 1024) return toast("error", "Dosya en fazla 10 MB olabilir.");
                up.mutate(f, { onSuccess: () => toast("success", "Ek yüklendi."), onError: (err) => toast("error", errorMessage(err)) });
              }}
            />
          </label>
        )}
      </div>
      {list.data && list.data.length > 0 && (
        <ul className="divide-y divide-border rounded-lg border border-border text-sm">
          {list.data.map((a) => (
            <li key={a.id} className="flex items-center gap-2 px-3 py-2">
              <a href={`/api/v1/attachments/${a.id}`} className="min-w-0 flex-1 truncate text-primary hover:underline" download>
                {a.fileName}
              </a>
              <span className="text-xs text-muted">{fmtSize(a.sizeBytes)} · {a.uploadedBy.fullName} · {fmtRelative(a.createdAt)}</span>
              <a href={`/api/v1/attachments/${a.id}`} download aria-label={`${a.fileName} indir`} className="p-1 text-muted hover:text-text">
                <Download className="size-4" />
              </a>
              {(a.uploadedBy.id === user.id || manager) && (
                <button
                  className="p-1 text-muted hover:text-danger"
                  aria-label={`${a.fileName} sil`}
                  onClick={() => confirm("Ek silinsin mi?") && del.mutate(a.id, { onError: (err) => toast("error", errorMessage(err)) })}
                >
                  <Trash2 className="size-4" />
                </button>
              )}
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}

const ACTION_LABEL: Record<string, string> = {
  "task.progress": "ilerlemeyi güncelledi",
  "attachment.create": "ek ekledi",
  "attachment.delete": "eki sildi",
  "task.create": "oluşturdu",
  "task.update": "güncelledi",
  "task.transition": "durumu değiştirdi",
  "task.delete": "sildi",
  "comment.create": "yorum ekledi",
};

function History({ taskId }: { taskId: string }) {
  const h = useTaskHistory(taskId);
  if (h.isPending) return <Spinner />;
  if (h.error) return <ErrorState message={errorMessage(h.error)} />;
  if (!h.data.length) return <EmptyState title="Kayıt yok" description="Seed verisiyle gelen task'ların geçmişi boştur." />;
  return (
    <ol className="space-y-2 text-sm">
      {h.data.map((e) => (
        <li key={e.id} className="flex gap-2">
          <span className="w-28 shrink-0 text-xs text-muted">{fmtDateTime(e.occurredAt)}</span>
          <span className="text-text">
            <span className="font-medium">{e.actor?.fullName ?? "Sistem"}</span> {ACTION_LABEL[e.action] ?? e.action}
            {e.changes && "status" in e.changes && Array.isArray(e.changes.status) && (
              <span className="text-muted"> ({statusLabel[e.changes.status[0] as Status] ?? ""} → {statusLabel[e.changes.status[1] as Status] ?? ""})</span>
            )}
          </span>
        </li>
      ))}
    </ol>
  );
}

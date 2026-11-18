import { CalendarClock, MessageSquare, Pencil, Repeat, Trash2 } from "lucide-react";
import { useState } from "react";
import {
  errorMessage,
  useAddComment,
  useComments,
  useDeleteTask,
  useTask,
  useTaskHistory,
  useTransitionTask,
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
  const [tab, setTab] = useState<"comments" | "history">("comments");
  const [editing, setEditing] = useState(false);
  const [blockOpen, setBlockOpen] = useState(false);
  const [reason, setReason] = useState("");
  const manager = managesTeam(task.teamId);
  const involved = user.id === task.assignee?.id || user.id === task.backupAssignee?.id;
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

      <dl className="grid grid-cols-2 gap-x-6 gap-y-3 text-sm sm:grid-cols-3">
        {[
          ["Ekip", task.teamName],
          ["Proje", task.project?.name ?? "—"],
          ["Kategori", categoryLabel[task.category]],
          ["Öncelik", <PriorityBadge key="p" priority={task.priority} />],
          ["Sorumlu", task.assignee?.fullName ?? "Atanmamış"],
          ["Yedek", task.backupAssignee?.fullName ?? "—"],
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

      <div className="space-y-3 border-t border-border pt-4">
        <Tabs value={tab} onChange={setTab} items={[{ value: "comments", label: `Yorumlar (${task.commentCount ?? 0})` }, { value: "history", label: "Geçmiş" }]} />
        {tab === "comments" ? <Comments task={task} /> : <History taskId={task.id} />}
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

const ACTION_LABEL: Record<string, string> = {
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

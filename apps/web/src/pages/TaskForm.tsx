import { zodResolver } from "@hookform/resolvers/zod";
import { useEffect } from "react";
import { useForm, useWatch } from "react-hook-form";
import { z } from "zod";
import {
  errorMessage,
  useCreateTask,
  useProjects,
  useTeams,
  useUpdateTask,
  useUsers,
  type Schemas,
} from "../api/hooks";
import { useAuth } from "../auth";
import { Button, Field, Input, Modal, Select, Textarea, useToast } from "../components/ui";
import { categoryLabel, priorityLabel, recurrenceLabel } from "../i18n/tr";

// Sözleşmedeki kısıtların aynası (R-TS-04): title 3–200, description ≤ 10000.
const schema = z
  .object({
    type: z.enum(["STANDARD", "PROJECT"]),
    teamId: z.string().optional(),
    projectId: z.string().optional(),
    title: z.string().trim().min(3, "En az 3 karakter.").max(200, "En fazla 200 karakter."),
    description: z.string().max(10000, "En fazla 10.000 karakter.").optional(),
    priority: z.enum(["LOW", "MEDIUM", "HIGH", "CRITICAL"]),
    category: z.enum([
      "INCIDENT_RESPONSE", "VULNERABILITY_MANAGEMENT", "MONITORING", "PENETRATION_TEST",
      "COMPLIANCE", "THREAT_INTEL", "AWARENESS", "OPERATIONS", "OTHER",
    ]),
    assigneeId: z.string().optional(),
    backupAssigneeId: z.string().optional(),
    dueDate: z.string().optional(),
    recurrence: z.enum(["NONE", "DAILY", "WEEKLY", "MONTHLY"]),
  })
  .refine((v) => v.type !== "PROJECT" || !!v.projectId, { path: ["projectId"], message: "Proje seçin." })
  .refine((v) => v.type !== "STANDARD" || !!v.teamId, { path: ["teamId"], message: "Ekip seçin." })
  .refine((v) => !v.backupAssigneeId || v.backupAssigneeId !== v.assigneeId, {
    path: ["backupAssigneeId"],
    message: "Yedek, sorumluyla aynı olamaz.",
  });
type FormValues = z.infer<typeof schema>;

const opt = (v?: string) => (v ? v : undefined);

export function TaskFormModal({ open, onClose, task }: { open: boolean; onClose: () => void; task?: Schemas["Task"] }) {
  const { user, can, managesTeam } = useAuth();
  const toast = useToast();
  const teams = useTeams();
  const create = useCreateTask();
  const update = useUpdateTask(task?.id ?? "");
  const isEdit = !!task;
  const manageableTeams = (teams.data ?? []).filter((t) => managesTeam(t.id));
  const { register, handleSubmit, control, reset, setValue, formState } = useForm<FormValues>({
    resolver: zodResolver(schema),
  });

  useEffect(() => {
    if (!open) return;
    reset({
      type: task?.type ?? "STANDARD",
      teamId: task?.teamId ?? (can.manage ? (manageableTeams[0]?.id ?? user.teamId ?? undefined) : (user.teamId ?? undefined)),
      projectId: task?.project?.id,
      title: task?.title ?? "",
      description: task?.description ?? "",
      priority: task?.priority ?? "MEDIUM",
      category: task?.category ?? "OTHER",
      assigneeId: task?.assignee?.id ?? (can.manage ? undefined : user.id),
      backupAssigneeId: task?.backupAssignee?.id,
      dueDate: task?.dueDate ?? undefined,
      recurrence: task?.recurrence ?? "NONE",
    });
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [open, task?.id]);

  const type = useWatch({ control, name: "type" });
  const teamId = useWatch({ control, name: "teamId" });
  const projectId = useWatch({ control, name: "projectId" });
  const projects = useProjects({ status: "ACTIVE" });
  const projectTeam = projects.data?.items.find((p) => p.id === projectId)?.teamId;
  const effectiveTeam = type === "PROJECT" ? projectTeam : teamId;
  const members = useUsers({ teamId: effectiveTeam, pageSize: 100, isActive: true });

  useEffect(() => {
    if (!isEdit && !can.manage) setValue("assigneeId", user.id);
  }, [isEdit, can.manage, setValue, user.id]);

  const submit = handleSubmit((v) => {
    const onError = (e: unknown) => toast("error", errorMessage(e));
    if (isEdit && task) {
      update.mutate(
        {
          version: task.version,
          title: v.title,
          description: v.description || null,
          priority: v.priority,
          category: v.category,
          assigneeId: opt(v.assigneeId) ?? null,
          backupAssigneeId: opt(v.backupAssigneeId) ?? null,
          dueDate: opt(v.dueDate) ?? null,
          recurrence: v.recurrence,
        },
        { onSuccess: () => (toast("success", "Task güncellendi."), onClose()), onError },
      );
    } else {
      create.mutate(
        {
          type: v.type,
          teamId: v.type === "STANDARD" ? opt(v.teamId) : undefined,
          projectId: v.type === "PROJECT" ? opt(v.projectId) : undefined,
          title: v.title,
          description: opt(v.description),
          priority: v.priority,
          category: v.category,
          assigneeId: opt(v.assigneeId),
          backupAssigneeId: opt(v.backupAssigneeId),
          dueDate: opt(v.dueDate),
          recurrence: v.recurrence,
        },
        { onSuccess: () => (toast("success", "Task oluşturuldu."), onClose()), onError },
      );
    }
  });

  const e = formState.errors;
  const memberOptions = (members.data?.items ?? []).filter((m) => m.teamId === effectiveTeam);
  return (
    <Modal
      open={open}
      onClose={onClose}
      wide
      title={isEdit ? "Task'ı düzenle" : "Yeni task"}
      footer={
        <>
          <Button variant="secondary" onClick={onClose}>Vazgeç</Button>
          <Button onClick={() => void submit()} loading={create.isPending || update.isPending}>
            {isEdit ? "Kaydet" : "Oluştur"}
          </Button>
        </>
      }
    >
      <form noValidate onSubmit={(ev) => (ev.preventDefault(), void submit())} className="grid gap-4 sm:grid-cols-2">
        {!isEdit && (
          <Field label="Tür" htmlFor="t-type" error={e.type?.message}>
            <Select id="t-type" {...register("type")} disabled={!can.manage}>
              <option value="STANDARD">Standart task</option>
              <option value="PROJECT">Proje task'ı</option>
            </Select>
          </Field>
        )}
        {!isEdit && type === "STANDARD" && (
          <Field label="Ekip" htmlFor="t-team" error={e.teamId?.message}>
            <Select id="t-team" {...register("teamId")} disabled={!can.manage}>
              {(can.manage ? manageableTeams : (teams.data ?? []).filter((t) => t.id === user.teamId)).map((t) => (
                <option key={t.id} value={t.id}>{t.name}</option>
              ))}
            </Select>
          </Field>
        )}
        {!isEdit && type === "PROJECT" && (
          <Field label="Proje" htmlFor="t-project" error={e.projectId?.message}>
            <Select id="t-project" {...register("projectId")}>
              <option value="">Seçin…</option>
              {(projects.data?.items ?? []).filter((p) => managesTeam(p.teamId)).map((p) => (
                <option key={p.id} value={p.id}>{p.name} ({p.teamName})</option>
              ))}
            </Select>
          </Field>
        )}
        <div className="sm:col-span-2">
          <Field label="Başlık" htmlFor="t-title" error={e.title?.message}>
            <Input id="t-title" {...register("title")} maxLength={200} />
          </Field>
        </div>
        <div className="sm:col-span-2">
          <Field label="Açıklama" htmlFor="t-desc" error={e.description?.message}>
            <Textarea id="t-desc" {...register("description")} maxLength={10000} />
          </Field>
        </div>
        <Field label="Öncelik" htmlFor="t-prio">
          <Select id="t-prio" {...register("priority")}>
            {Object.entries(priorityLabel).map(([k, l]) => <option key={k} value={k}>{l}</option>)}
          </Select>
        </Field>
        <Field label="Kategori" htmlFor="t-cat">
          <Select id="t-cat" {...register("category")}>
            {Object.entries(categoryLabel).map(([k, l]) => <option key={k} value={k}>{l}</option>)}
          </Select>
        </Field>
        <Field label="Sorumlu" htmlFor="t-assignee" error={e.assigneeId?.message}>
          <Select id="t-assignee" {...register("assigneeId")} disabled={!can.manage}>
            <option value="">Atanmamış</option>
            {(can.manage ? memberOptions : [user]).map((m) => <option key={m.id} value={m.id}>{m.fullName}</option>)}
          </Select>
        </Field>
        <Field label="Yedek sorumlu" htmlFor="t-backup" error={e.backupAssigneeId?.message} hint="Asıl kişi yokken işi devralır.">
          <Select id="t-backup" {...register("backupAssigneeId")}>
            <option value="">Yok</option>
            {memberOptions.map((m) => <option key={m.id} value={m.id}>{m.fullName}</option>)}
          </Select>
        </Field>
        <Field label="Son tarih" htmlFor="t-due">
          <Input id="t-due" type="date" {...register("dueDate")} />
        </Field>
        <Field label="Tekrar" htmlFor="t-rec" hint="Rutin işler için worker her periyotta yeni task üretir.">
          <Select id="t-rec" {...register("recurrence")}>
            {Object.entries(recurrenceLabel).map(([k, l]) => <option key={k} value={k}>{l}</option>)}
          </Select>
        </Field>
      </form>
    </Modal>
  );
}

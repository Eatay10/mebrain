import { zodResolver } from "@hookform/resolvers/zod";
import { ArrowLeft, Plus } from "lucide-react";
import { useState } from "react";
import { useForm } from "react-hook-form";
import { Link, useParams } from "react-router";
import { z } from "zod";
import {
  errorMessage,
  useCreateProject,
  useProject,
  useProjects,
  useTeams,
  useUpdateProject,
  type Schemas,
} from "../api/hooks";
import { useAuth } from "../auth";
import {
  Badge,
  Button,
  Card,
  EmptyState,
  ErrorState,
  Field,
  Input,
  Modal,
  PageHeader,
  ProgressBar,
  Select,
  Skeleton,
  Stat,
  Textarea,
  useToast,
} from "../components/ui";
import { projectStatusLabel } from "../i18n/tr";
import { fmtDate, pct } from "../lib/format";
import { TasksPage } from "./Tasks";

const statusTone: Record<Schemas["ProjectStatus"], string> = {
  ACTIVE: "bg-info-soft text-progress",
  ON_HOLD: "bg-warning-soft text-blocked",
  COMPLETED: "bg-success-soft text-done",
  ARCHIVED: "bg-surface-2 text-muted",
};

export function ProjectsPage() {
  const { can, managesTeam } = useAuth();
  const teams = useTeams();
  const [teamId, setTeamId] = useState("");
  const [status, setStatus] = useState<Schemas["ProjectStatus"] | "">("ACTIVE");
  const [open, setOpen] = useState(false);
  const projects = useProjects({ teamId: teamId || undefined, status: status || undefined });
  const canCreate = can.manage && (teams.data ?? []).some((t) => managesTeam(t.id));
  return (
    <>
      <PageHeader
        title="Projeler"
        subtitle="Proje bazlı task'lar ve ilerleme"
        actions={canCreate && <Button onClick={() => setOpen(true)}><Plus className="size-4" />Yeni proje</Button>}
      />
      <div className="mb-4 flex flex-wrap gap-3">
        <Select aria-label="Ekip" value={teamId} onChange={(e) => setTeamId(e.target.value)} className="w-48">
          <option value="">Tüm ekipler</option>
          {teams.data?.map((t) => <option key={t.id} value={t.id}>{t.name}</option>)}
        </Select>
        <Select aria-label="Durum" value={status} onChange={(e) => setStatus(e.target.value as Schemas["ProjectStatus"] | "")} className="w-44">
          <option value="">Tüm durumlar</option>
          {Object.entries(projectStatusLabel).map(([k, l]) => <option key={k} value={k}>{l}</option>)}
        </Select>
      </div>
      {projects.error ? (
        <Card><ErrorState message={errorMessage(projects.error)} onRetry={() => void projects.refetch()} /></Card>
      ) : projects.isPending ? (
        <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">{Array.from({ length: 6 }).map((_, i) => <Skeleton key={i} className="h-40" />)}</div>
      ) : projects.data.items.length === 0 ? (
        <Card><EmptyState title="Proje bulunamadı" description="Filtreleri değiştirin." /></Card>
      ) : (
        <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
          {projects.data.items.map((p) => (
            <Link key={p.id} to={`/projects/${p.id}`} className="rounded-xl">
              <Card className="h-full p-5 transition-colors hover:border-primary">
                <div className="flex items-start justify-between gap-2">
                  <h2 className="font-semibold text-text">{p.name}</h2>
                  <Badge className={statusTone[p.status]}>{projectStatusLabel[p.status]}</Badge>
                </div>
                <p className="mt-1 text-xs text-muted">{p.teamName} · Sahip: {p.owner?.fullName ?? "—"}</p>
                <div className="mt-4 flex items-center gap-2">
                  <ProgressBar counts={p.progress} />
                  <span className="tabular text-xs text-muted">%{pct(p.progress.done, p.progress.total)}</span>
                </div>
                <p className="mt-3 text-xs text-muted">
                  {p.progress.total} task · {p.progress.inProgress} devam · {p.progress.blocked} bloklu
                  {p.progress.overdue > 0 && <span className="text-danger"> · {p.progress.overdue} gecikmiş</span>}
                </p>
                <p className="mt-1 text-xs text-muted">Son tarih: {fmtDate(p.dueDate)}</p>
              </Card>
            </Link>
          ))}
        </div>
      )}
      <ProjectFormModal open={open} onClose={() => setOpen(false)} />
    </>
  );
}

const schema = z.object({
  teamId: z.string().min(1, "Ekip seçin."),
  name: z.string().trim().min(2, "En az 2 karakter.").max(150),
  description: z.string().max(10000).optional(),
  startDate: z.string().optional(),
  dueDate: z.string().optional(),
  status: z.enum(["ACTIVE", "ON_HOLD", "COMPLETED", "ARCHIVED"]).optional(),
});
type Form = z.infer<typeof schema>;

function ProjectFormModal({ open, onClose, project }: { open: boolean; onClose: () => void; project?: Schemas["Project"] }) {
  const { managesTeam } = useAuth();
  const teams = useTeams();
  const toast = useToast();
  const create = useCreateProject();
  const update = useUpdateProject(project?.id ?? "");
  const { register, handleSubmit, formState } = useForm<Form>({
    resolver: zodResolver(schema),
    values: {
      teamId: project?.teamId ?? (teams.data ?? []).find((t) => managesTeam(t.id))?.id ?? "",
      name: project?.name ?? "",
      description: project?.description ?? "",
      startDate: project?.startDate ?? "",
      dueDate: project?.dueDate ?? "",
      status: project?.status ?? "ACTIVE",
    },
  });
  const submit = handleSubmit((v) => {
    const onError = (e: unknown) => toast("error", errorMessage(e));
    const done = () => (toast("success", "Proje kaydedildi."), onClose());
    if (project) {
      update.mutate(
        { name: v.name, description: v.description ?? "", startDate: v.startDate || null, dueDate: v.dueDate || null, status: v.status },
        { onSuccess: done, onError },
      );
    } else {
      create.mutate(
        { teamId: v.teamId, name: v.name, description: v.description || undefined, startDate: v.startDate || undefined, dueDate: v.dueDate || undefined },
        { onSuccess: done, onError },
      );
    }
  });
  return (
    <Modal
      open={open}
      onClose={onClose}
      title={project ? "Projeyi düzenle" : "Yeni proje"}
      footer={<><Button variant="secondary" onClick={onClose}>Vazgeç</Button><Button onClick={() => void submit()} loading={create.isPending || update.isPending}>Kaydet</Button></>}
    >
      <form noValidate className="space-y-4" onSubmit={(e) => (e.preventDefault(), void submit())}>
        {!project && (
          <Field label="Ekip" htmlFor="p-team" error={formState.errors.teamId?.message}>
            <Select id="p-team" {...register("teamId")}>
              {(teams.data ?? []).filter((t) => managesTeam(t.id)).map((t) => <option key={t.id} value={t.id}>{t.name}</option>)}
            </Select>
          </Field>
        )}
        <Field label="Ad" htmlFor="p-name" error={formState.errors.name?.message}><Input id="p-name" {...register("name")} maxLength={150} /></Field>
        <Field label="Açıklama" htmlFor="p-desc"><Textarea id="p-desc" {...register("description")} /></Field>
        <div className="grid grid-cols-2 gap-4">
          <Field label="Başlangıç" htmlFor="p-start"><Input id="p-start" type="date" {...register("startDate")} /></Field>
          <Field label="Son tarih" htmlFor="p-due"><Input id="p-due" type="date" {...register("dueDate")} /></Field>
        </div>
        {project && (
          <Field label="Durum" htmlFor="p-status">
            <Select id="p-status" {...register("status")}>
              {Object.entries(projectStatusLabel).map(([k, l]) => <option key={k} value={k}>{l}</option>)}
            </Select>
          </Field>
        )}
      </form>
    </Modal>
  );
}

export function ProjectDetailPage() {
  const { projectId } = useParams();
  const { managesTeam, can } = useAuth();
  const project = useProject(projectId);
  const [editing, setEditing] = useState(false);
  if (project.isPending) return <Skeleton className="h-64" />;
  if (project.error) return <Card><ErrorState message={errorMessage(project.error)} /></Card>;
  const p = project.data;
  return (
    <>
      <Link to="/projects" className="mb-3 inline-flex items-center gap-1 text-sm text-muted hover:text-text"><ArrowLeft className="size-4" />Projeler</Link>
      <PageHeader
        title={p.name}
        subtitle={`${p.teamName} · Sahip: ${p.owner?.fullName ?? "—"} · ${fmtDate(p.startDate)} – ${fmtDate(p.dueDate)}`}
        actions={managesTeam(p.teamId) && !can.readOnly && <Button variant="secondary" onClick={() => setEditing(true)}>Düzenle</Button>}
      />
      {p.description && <p className="mb-6 max-w-3xl text-sm whitespace-pre-wrap text-muted">{p.description}</p>}
      <div className="mb-6 grid grid-cols-2 gap-4 md:grid-cols-5">
        <Stat label="Başlanmadı" value={p.progress.todo} tone="text-todo" />
        <Stat label="Devam ediyor" value={p.progress.inProgress} tone="text-progress" />
        <Stat label="Bloklu" value={p.progress.blocked} tone="text-blocked" />
        <Stat label="Tamamlandı" value={p.progress.done} tone="text-done" />
        <Stat label="İlerleme" value={`%${pct(p.progress.done, p.progress.total)}`} hint={`${p.progress.overdue} gecikmiş`} />
      </div>
      <h2 className="mb-3 text-base font-semibold text-text">Proje task'ları</h2>
      <TasksPage projectId={p.id} embedded />
      <ProjectFormModal open={editing} onClose={() => setEditing(false)} project={p} />
    </>
  );
}

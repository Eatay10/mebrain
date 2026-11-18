import { zodResolver } from "@hookform/resolvers/zod";
import { ArrowLeft, Building2, Crown, Network, Plus, Star, Trash2, User as UserIcon, Users } from "lucide-react";
import { useState } from "react";
import { useForm } from "react-hook-form";
import { Link, useParams } from "react-router";
import { z } from "zod";
import {
  errorMessage,
  useAddStakeholder,
  useCreateProject,
  useProject,
  useProjectOrganization,
  useProjects,
  useRemoveStakeholder,
  useTeams,
  useUpdateProject,
  useUsers,
  type Schemas,
  useProjectWatchToggle,
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
  Tabs,
  Textarea,
  useToast,
} from "../components/ui";
import { projectStatusLabel, stakeholderRoleLabel } from "../i18n/tr";
import { fmtDate, pct } from "../lib/format";
import { TasksPage } from "./Tasks";
import { TeamOptions } from "../components/TeamOptions";

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
  const [starred, setStarred] = useState(false);
  const projects = useProjects({ teamId: teamId || undefined, status: status || undefined, watching: starred || undefined });
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
          <TeamOptions teams={teams.data} />
        </Select>
        <Select aria-label="Durum" value={status} onChange={(e) => setStatus(e.target.value as Schemas["ProjectStatus"] | "")} className="w-44">
          <option value="">Tüm durumlar</option>
          {Object.entries(projectStatusLabel).map(([k, l]) => <option key={k} value={k}>{l}</option>)}
        </Select>
        <Button variant={starred ? "primary" : "secondary"} aria-pressed={starred} onClick={() => setStarred((v) => !v)}>
          <Star className={`size-4 ${starred ? "fill-current" : ""}`} aria-hidden />
          Yıldızlı
        </Button>
      </div>
      {projects.error ? (
        <Card><ErrorState message={errorMessage(projects.error)} onRetry={() => void projects.refetch()} /></Card>
      ) : projects.isPending ? (
        <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">{Array.from({ length: 6 }).map((_, i) => <Skeleton key={i} className="h-40" />)}</div>
      ) : projects.data.items.length === 0 ? (
        <Card>
          <EmptyState
            title={starred ? "Yıldızlı proje yok" : "Proje bulunamadı"}
            description={starred ? "Proje kartındaki yıldız ile takip etmeye başlayın." : "Filtreleri değiştirin."}
          />
        </Card>
      ) : (
        <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
          {projects.data.items.map((p) => (
            <div key={p.id} className="relative">
            <Link to={`/projects/${p.id}`} className="block h-full rounded-xl">
              <Card className="h-full p-5 transition-colors hover:border-primary">
                <div className="flex items-start justify-between gap-2 pr-9">
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
            <StarButton projectId={p.id} name={p.name} watching={!!p.isWatching} className="absolute top-3 right-3" />
            </div>
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
              <TeamOptions teams={(teams.data ?? []).filter((t) => managesTeam(t.id))} />
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
  const [tab, setTab] = useState<"tasks" | "org">("tasks");
  if (project.isPending) return <Skeleton className="h-64" />;
  if (project.error) return <Card><ErrorState message={errorMessage(project.error)} /></Card>;
  const p = project.data;
  return (
    <>
      <Link to="/projects" className="mb-3 inline-flex items-center gap-1 text-sm text-muted hover:text-text"><ArrowLeft className="size-4" />Projeler</Link>
      <PageHeader
        title={p.name}
        subtitle={`${p.teamName} · Sahip: ${p.owner?.fullName ?? "—"} · ${fmtDate(p.startDate)} – ${fmtDate(p.dueDate)}`}
        actions={
          <>
            <StarButton projectId={p.id} name={p.name} watching={!!p.isWatching} withLabel />
            {managesTeam(p.teamId) && !can.readOnly && <Button variant="secondary" onClick={() => setEditing(true)}>Düzenle</Button>}
          </>
        }
      />
      {p.description && <p className="mb-6 max-w-3xl text-sm whitespace-pre-wrap text-muted">{p.description}</p>}
      <div className="mb-6 grid grid-cols-2 gap-4 md:grid-cols-5">
        <Stat label="Başlanmadı" value={p.progress.todo} tone="text-todo" />
        <Stat label="Devam ediyor" value={p.progress.inProgress} tone="text-progress" />
        <Stat label="Bloklu" value={p.progress.blocked} tone="text-blocked" />
        <Stat label="Tamamlandı" value={p.progress.done} tone="text-done" />
        <Stat label="İlerleme" value={`%${pct(p.progress.done, p.progress.total)}`} hint={`${p.progress.overdue} gecikmiş`} />
      </div>
      <div className="mb-4">
        <Tabs
          value={tab}
          onChange={setTab}
          items={[
            { value: "tasks", label: "Proje task'ları" },
            { value: "org", label: "Organizasyon ve paydaşlar" },
          ]}
        />
      </div>
      {tab === "tasks" ? (
        <TasksPage projectId={p.id} embedded />
      ) : (
        <ProjectOrganization projectId={p.id} canManage={managesTeam(p.teamId) && !can.readOnly} />
      )}
      <ProjectFormModal open={editing} onClose={() => setEditing(false)} project={p} />
    </>
  );
}

const KIND_ICON = {
  DIRECTOR: <Crown className="size-4 text-blocked" aria-hidden />,
  UNIT: <Building2 className="size-4 text-primary" aria-hidden />,
  TEAM: <Users className="size-4 text-progress" aria-hidden />,
  USER: <UserIcon className="size-4 text-muted" aria-hidden />,
} as const;

function OrgTree({ nodes }: { nodes: Schemas["OrgNode"][] }) {
  return (
    <ul className="space-y-1 border-l border-border pl-4">
      {nodes.map((n) => (
        <li key={`${n.kind}-${n.id}`}>
          <div className="flex flex-wrap items-center gap-2 rounded-lg px-2 py-1.5 hover:bg-surface-2">
            {KIND_ICON[n.kind]}
            <span className={n.kind === "USER" ? "text-sm text-text" : "text-sm font-semibold text-text"}>{n.name}</span>
            {n.title && <span className="text-xs text-muted">{n.title}</span>}
            {(n.projectRoles ?? []).map((r) => (
              <Badge key={r} className="bg-primary-soft text-primary">{r}</Badge>
            ))}
          </div>
          {n.children.length > 0 && <OrgTree nodes={n.children} />}
        </li>
      ))}
    </ul>
  );
}

function ProjectOrganization({ projectId, canManage }: { projectId: string; canManage: boolean }) {
  const toast = useToast();
  const org = useProjectOrganization(projectId);
  const add = useAddStakeholder(projectId);
  const remove = useRemoveStakeholder(projectId);
  const users = useUsers({ pageSize: 100, isActive: true });
  const [kind, setKind] = useState<"internal" | "external">("internal");
  const [userId, setUserId] = useState("");
  const [name, setName] = useState("");
  const [organization, setOrganization] = useState("");
  const [role, setRole] = useState<Schemas["StakeholderRole"]>("STAKEHOLDER");
  if (org.isPending) return <Skeleton className="h-48" />;
  if (org.error) return <Card><ErrorState message={errorMessage(org.error)} /></Card>;
  const onError = (e: unknown) => toast("error", errorMessage(e));
  return (
    <div className="grid gap-6 xl:grid-cols-5">
      <Card className="xl:col-span-3">
        <div className="flex items-center gap-2 border-b border-border px-5 py-4">
          <Network className="size-4 text-muted" aria-hidden />
          <h3 className="font-semibold">Organizasyon ağacı</h3>
          <span className="text-xs text-muted">Direktör → Unit → Ekip → Kişi; projede yer alan kişiler</span>
        </div>
        <div className="px-3 py-4">
          {org.data.tree.length === 0 ? <EmptyState title="Projede henüz kimse yok" /> : <OrgTree nodes={org.data.tree} />}
        </div>
      </Card>
      <Card className="xl:col-span-2">
        <div className="border-b border-border px-5 py-4">
          <h3 className="font-semibold">Paydaşlar</h3>
        </div>
        {org.data.stakeholders.length === 0 ? (
          <EmptyState title="Paydaş eklenmemiş" />
        ) : (
          <ul className="divide-y divide-border">
            {org.data.stakeholders.map((sh) => (
              <li key={sh.id} className="flex items-center gap-3 px-5 py-2.5 text-sm">
                <div className="min-w-0 flex-1">
                  <p className="font-medium text-text">{sh.name}</p>
                  <p className="text-xs text-muted">
                    {stakeholderRoleLabel[sh.role]}
                    {sh.organization && ` · ${sh.organization}`}
                    {!sh.user && " · dış paydaş"}
                    {sh.note && ` · ${sh.note}`}
                  </p>
                </div>
                {canManage && (
                  <button
                    className="p-1 text-muted hover:text-danger"
                    aria-label={`${sh.name} paydaşını kaldır`}
                    onClick={() => remove.mutate(sh.id, { onError })}
                  >
                    <Trash2 className="size-4" />
                  </button>
                )}
              </li>
            ))}
          </ul>
        )}
        {canManage && (
          <form
            className="space-y-3 border-t border-border px-5 py-4"
            onSubmit={(e) => {
              e.preventDefault();
              const body =
                kind === "internal"
                  ? { userId, role }
                  : { name: name.trim(), organization: organization.trim() || undefined, role };
              add.mutate(body, {
                onSuccess: () => (setUserId(""), setName(""), setOrganization(""), toast("success", "Paydaş eklendi.")),
                onError,
              });
            }}
          >
            <div className="flex gap-2 text-xs">
              {(["internal", "external"] as const).map((k) => (
                <button
                  key={k}
                  type="button"
                  aria-pressed={kind === k}
                  onClick={() => setKind(k)}
                  className={kind === k ? "rounded-full bg-primary px-3 py-1 text-on-primary" : "rounded-full bg-surface-2 px-3 py-1"}
                >
                  {k === "internal" ? "Kurum içi" : "Dış paydaş"}
                </button>
              ))}
            </div>
            {kind === "internal" ? (
              <Field label="Kişi" htmlFor="sh-user">
                <Select id="sh-user" value={userId} onChange={(e) => setUserId(e.target.value)}>
                  <option value="">Seçin…</option>
                  {(users.data?.items ?? []).map((u) => <option key={u.id} value={u.id}>{u.fullName}{u.teamName ? ` — ${u.teamName}` : ""}</option>)}
                </Select>
              </Field>
            ) : (
              <div className="grid gap-3 sm:grid-cols-2">
                <Field label="Ad" htmlFor="sh-name"><Input id="sh-name" value={name} onChange={(e) => setName(e.target.value)} maxLength={120} /></Field>
                <Field label="Kurum / birim" htmlFor="sh-org"><Input id="sh-org" value={organization} onChange={(e) => setOrganization(e.target.value)} maxLength={150} /></Field>
              </div>
            )}
            <Field label="Rol" htmlFor="sh-role">
              <Select id="sh-role" value={role} onChange={(e) => setRole(e.target.value as Schemas["StakeholderRole"])}>
                {Object.entries(stakeholderRoleLabel).map(([k, l]) => <option key={k} value={k}>{l}</option>)}
              </Select>
            </Field>
            <Button type="submit" size="sm" loading={add.isPending} disabled={kind === "internal" ? !userId : name.trim().length < 2}>
              <Plus className="size-4" /> Paydaş ekle
            </Button>
          </form>
        )}
      </Card>
    </div>
  );
}

/** Projeye yıldız koy / kaldır. Yıldız kişiseldir; projeyi gören herkes kullanabilir. */
function StarButton({
  projectId,
  name,
  watching,
  withLabel,
  className,
}: {
  projectId: string;
  name: string;
  watching: boolean;
  withLabel?: boolean;
  className?: string;
}) {
  const toggle = useProjectWatchToggle(projectId);
  const toast = useToast();
  const label = watching ? `${name} projesinden yıldızı kaldır` : `${name} projesine yıldız koy`;
  return (
    <button
      type="button"
      aria-pressed={watching}
      aria-label={label}
      title={watching ? "Yıldızı kaldır" : "Yıldız koy"}
      disabled={toggle.isPending}
      onClick={() => toggle.mutate(!watching, { onError: (e) => toast("error", errorMessage(e)) })}
      className={`inline-flex items-center gap-1.5 rounded-lg p-1.5 text-sm hover:bg-surface-2 disabled:opacity-60 ${
        watching ? "text-blocked" : "text-muted hover:text-text"
      } ${withLabel ? "h-10 border border-border px-3" : ""} ${className ?? ""}`}
    >
      <Star className={`size-5 ${watching ? "fill-current" : ""}`} aria-hidden />
      {withLabel && (watching ? "Yıldızlı" : "Yıldız koy")}
    </button>
  );
}

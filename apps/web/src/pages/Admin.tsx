import { Plus, Search } from "lucide-react";
import { useState } from "react";
import {
  errorMessage,
  useCreateTeam,
  useCreateUser,
  useTeams,
  useUpdateTeam,
  useUpdateUser,
  useUsers,
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
  Modal,
  PageHeader,
  Pagination,
  Select,
  Skeleton,
  Tabs,
  useToast,
} from "../components/ui";
import { roleLabel } from "../i18n/tr";
import { fmtRelative } from "../lib/format";

export function AdminPage() {
  const { can } = useAuth();
  const [tab, setTab] = useState<"users" | "teams">("users");
  if (!can.direct) return <Card><ErrorState message="Bu sayfa sadece direktörler içindir." /></Card>;
  return (
    <>
      <PageHeader title="Kullanıcı & Ekip" subtitle="Roller, ekip üyelikleri ve yöneticiler" actions={<Tabs value={tab} onChange={setTab} items={[{ value: "users", label: "Kullanıcılar" }, { value: "teams", label: "Ekipler" }]} />} />
      {tab === "users" ? <Users /> : <Teams />}
    </>
  );
}

function Users() {
  const { user: me } = useAuth();
  const toast = useToast();
  const teams = useTeams();
  const [q, setQ] = useState("");
  const [teamId, setTeamId] = useState("");
  const [page, setPage] = useState(1);
  const users = useUsers({ q: q || undefined, teamId: teamId || undefined, page, pageSize: 20 });
  const update = useUpdateUser();
  const [creating, setCreating] = useState(false);
  const onError = (e: unknown) => toast("error", errorMessage(e));
  const change = (u: Schemas["User"], body: Schemas["UserUpdate"], msg: string) => {
    if (body.role && body.role !== u.role && !confirm(`${u.fullName} kullanıcısının rolü "${roleLabel[body.role]}" olarak değiştirilsin mi? Bu işlem güvenlik olayı olarak kaydedilir.`)) return;
    update.mutate({ id: u.id, ...body }, { onSuccess: () => toast("success", msg), onError });
  };
  return (
    <Card>
      <CardHeader
        title="Kullanıcılar"
        actions={
          <>
            <div className="relative">
              <Search className="pointer-events-none absolute top-1/2 left-3 size-4 -translate-y-1/2 text-muted" aria-hidden />
              <Input aria-label="Kullanıcı ara" placeholder="Ad veya e-posta" value={q} onChange={(e) => (setQ(e.target.value), setPage(1))} className="w-56 pl-9" />
            </div>
            <Select aria-label="Ekip" value={teamId} onChange={(e) => (setTeamId(e.target.value), setPage(1))} className="w-44">
              <option value="">Tüm ekipler</option>
              {teams.data?.map((t) => <option key={t.id} value={t.id}>{t.name}</option>)}
            </Select>
            <Button size="sm" onClick={() => setCreating(true)}><Plus className="size-4" />Kullanıcı</Button>
          </>
        }
      />
      {users.error ? <ErrorState message={errorMessage(users.error)} /> : !users.data ? <Skeleton className="m-5 h-64" /> : !users.data.items.length ? <EmptyState title="Kullanıcı bulunamadı" /> : (
        <>
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead className="bg-surface-2 text-left text-xs text-muted uppercase">
                <tr><th scope="col" className="px-5 py-2 font-medium">Kullanıcı</th><th scope="col" className="px-3 py-2 font-medium">Rol</th><th scope="col" className="px-3 py-2 font-medium">Ekip</th><th scope="col" className="px-3 py-2 font-medium">Son giriş</th><th scope="col" className="px-3 py-2 font-medium">Durum</th></tr>
              </thead>
              <tbody>
                {users.data.items.map((u) => (
                  <tr key={u.id} className="border-t border-border">
                    <td className="px-5 py-2"><p className="font-medium text-text">{u.fullName}</p><p className="text-xs text-muted">{u.email}</p></td>
                    <td className="px-3 py-2">
                      <label className="sr-only" htmlFor={`role-${u.id}`}>Rol</label>
                      <Select id={`role-${u.id}`} value={u.role} disabled={u.id === me.id} onChange={(e) => change(u, { role: e.target.value as Schemas["Role"], ...(["EMPLOYEE", "MANAGER"].includes(e.target.value) && !u.teamId ? { teamId: teams.data?.[0]?.id } : {}) }, "Rol güncellendi.")} className="h-8 w-36">
                        {Object.entries(roleLabel).map(([k, l]) => <option key={k} value={k}>{l}</option>)}
                      </Select>
                    </td>
                    <td className="px-3 py-2">
                      <label className="sr-only" htmlFor={`team-${u.id}`}>Ekip</label>
                      <Select id={`team-${u.id}`} value={u.teamId ?? ""} disabled={u.role === "DIRECTOR" || u.role === "AUDITOR"} onChange={(e) => change(u, { teamId: e.target.value }, "Ekip güncellendi.")} className="h-8 w-40">
                        {!u.teamId && <option value="">—</option>}
                        {teams.data?.map((t) => <option key={t.id} value={t.id}>{t.name}</option>)}
                      </Select>
                    </td>
                    <td className="px-3 py-2 text-xs text-muted">{fmtRelative(u.lastLoginAt)}</td>
                    <td className="px-3 py-2">
                      <button disabled={u.id === me.id} onClick={() => change(u, { isActive: !u.isActive }, u.isActive ? "Kullanıcı pasifleştirildi." : "Kullanıcı aktifleştirildi.")} className="disabled:opacity-50">
                        <Badge className={u.isActive ? "bg-success-soft text-done" : "bg-surface-2 text-muted"}>{u.isActive ? "Aktif" : "Pasif"}</Badge>
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          <Pagination page={page} pageSize={20} total={users.data.total} onPage={setPage} />
        </>
      )}
      <CreateUserModal open={creating} onClose={() => setCreating(false)} />
    </Card>
  );
}

function CreateUserModal({ open, onClose }: { open: boolean; onClose: () => void }) {
  const teams = useTeams();
  const toast = useToast();
  const create = useCreateUser();
  const [f, setF] = useState({ email: "", fullName: "", title: "", role: "EMPLOYEE" as Schemas["Role"], teamId: "", password: "" });
  const teamless = f.role === "DIRECTOR" || f.role === "AUDITOR";
  const valid = /^\S+@\S+\.\S+$/.test(f.email) && f.fullName.trim().length >= 2 && f.password.length >= 12 && (teamless || f.teamId || teams.data?.[0]);
  return (
    <Modal
      open={open}
      onClose={onClose}
      title="Yeni kullanıcı"
      footer={<><Button variant="secondary" onClick={onClose}>Vazgeç</Button><Button disabled={!valid} loading={create.isPending} onClick={() => create.mutate({ email: f.email.trim(), fullName: f.fullName.trim(), title: f.title || undefined, role: f.role, teamId: teamless ? undefined : f.teamId || teams.data?.[0]?.id, password: f.password }, { onSuccess: () => (toast("success", "Kullanıcı oluşturuldu."), onClose()), onError: (e) => toast("error", errorMessage(e)) })}>Oluştur</Button></>}
    >
      <div className="grid gap-4 sm:grid-cols-2">
        <Field label="Ad soyad" htmlFor="u-name"><Input id="u-name" value={f.fullName} onChange={(e) => setF({ ...f, fullName: e.target.value })} /></Field>
        <Field label="E-posta" htmlFor="u-email"><Input id="u-email" type="email" value={f.email} onChange={(e) => setF({ ...f, email: e.target.value })} /></Field>
        <Field label="Unvan" htmlFor="u-title"><Input id="u-title" value={f.title} onChange={(e) => setF({ ...f, title: e.target.value })} /></Field>
        <Field label="Rol" htmlFor="u-role"><Select id="u-role" value={f.role} onChange={(e) => setF({ ...f, role: e.target.value as Schemas["Role"] })}>{Object.entries(roleLabel).map(([k, l]) => <option key={k} value={k}>{l}</option>)}</Select></Field>
        {!teamless && <Field label="Ekip" htmlFor="u-team"><Select id="u-team" value={f.teamId} onChange={(e) => setF({ ...f, teamId: e.target.value })}>{teams.data?.map((t) => <option key={t.id} value={t.id}>{t.name}</option>)}</Select></Field>}
        <Field label="Geçici parola" htmlFor="u-pw" hint="En az 12 karakter."><Input id="u-pw" type="password" autoComplete="new-password" value={f.password} onChange={(e) => setF({ ...f, password: e.target.value })} /></Field>
      </div>
    </Modal>
  );
}

function Teams() {
  const toast = useToast();
  const teams = useTeams();
  const managers = useUsers({ pageSize: 100, isActive: true });
  const update = useUpdateTeam();
  const create = useCreateTeam();
  const [name, setName] = useState("");
  const mgrs = managers.data?.items.filter((u) => u.role === "MANAGER") ?? [];
  const onError = (e: unknown) => toast("error", errorMessage(e));
  return (
    <Card>
      <CardHeader
        title="Ekipler"
        actions={
          <form className="flex gap-2" onSubmit={(e) => (e.preventDefault(), name.trim().length >= 2 && create.mutate({ name: name.trim() }, { onSuccess: () => setName(""), onError }))}>
            <Input aria-label="Yeni ekip adı" placeholder="Yeni ekip adı" value={name} onChange={(e) => setName(e.target.value)} className="w-48" maxLength={100} />
            <Button size="sm" type="submit" disabled={name.trim().length < 2} loading={create.isPending}><Plus className="size-4" />Ekle</Button>
          </form>
        }
      />
      {teams.error ? <ErrorState message={errorMessage(teams.error)} /> : !teams.data ? <Skeleton className="m-5 h-40" /> : (
        <ul className="divide-y divide-border">
          {teams.data.map((t) => (
            <li key={t.id} className="flex flex-wrap items-center gap-4 px-5 py-3">
              <div className="min-w-40 flex-1"><p className="font-medium text-text">{t.name}</p><p className="text-xs text-muted">{t.memberCount} aktif üye</p></div>
              <label className="text-sm text-muted" htmlFor={`mgr-${t.id}`}>Yönetici</label>
              <Select id={`mgr-${t.id}`} value={t.manager?.id ?? ""} onChange={(e) => update.mutate({ id: t.id, managerId: e.target.value || null }, { onSuccess: () => toast("success", "Yönetici güncellendi."), onError })} className="w-56">
                <option value="">Atanmamış</option>
                {mgrs.map((m) => <option key={m.id} value={m.id}>{m.fullName}</option>)}
              </Select>
            </li>
          ))}
        </ul>
      )}
    </Card>
  );
}

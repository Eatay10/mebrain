import { Pin, Plus, Trash2 } from "lucide-react";
import { useState } from "react";
import {
  errorMessage,
  useAnnouncements,
  useCreateAnnouncement,
  useDeleteAnnouncement,
  useTeams,
} from "../api/hooks";
import { useAuth } from "../auth";
import {
  Avatar,
  Badge,
  Button,
  Card,
  EmptyState,
  ErrorState,
  Field,
  Input,
  Modal,
  PageHeader,
  Select,
  Skeleton,
  Textarea,
  useToast,
} from "../components/ui";
import { fmtDateTime } from "../lib/format";

export function AnnouncementsPage() {
  const { user, can, managesTeam } = useAuth();
  const toast = useToast();
  const list = useAnnouncements();
  const teams = useTeams();
  const del = useDeleteAnnouncement();
  const create = useCreateAnnouncement();
  const [open, setOpen] = useState(false);
  const managed = (teams.data ?? []).filter((t) => managesTeam(t.id));
  const [scope, setScope] = useState<"TEAM" | "ORGANIZATION">("TEAM");
  const [teamId, setTeamId] = useState("");
  const [title, setTitle] = useState("");
  const [body, setBody] = useState("");
  const [pinned, setPinned] = useState(false);
  const teamName = (id?: string | null) => teams.data?.find((t) => t.id === id)?.name ?? "Ekip";
  const valid = title.trim().length >= 3 && body.trim().length > 0 && (scope === "ORGANIZATION" || teamId || managed[0]);

  return (
    <>
      <PageHeader
        title="Duyurular"
        subtitle="Ekip ve kurum geneli iletişim"
        actions={can.manage && <Button onClick={() => setOpen(true)}><Plus className="size-4" />Yeni duyuru</Button>}
      />
      {list.isPending ? (
        <Skeleton className="h-64" />
      ) : list.error ? (
        <Card><ErrorState message={errorMessage(list.error)} onRetry={() => void list.refetch()} /></Card>
      ) : !list.data.items.length ? (
        <Card><EmptyState title="Duyuru yok" /></Card>
      ) : (
        <div className="space-y-4">
          {list.data.items.map((a) => (
            <Card key={a.id} className="p-5">
              <div className="flex items-start gap-3">
                <Avatar name={a.author.fullName} />
                <div className="min-w-0 flex-1">
                  <div className="flex flex-wrap items-center gap-2">
                    <h2 className="font-semibold text-text">{a.title}</h2>
                    {a.pinned && <Badge className="bg-warning-soft text-blocked"><Pin className="size-3" />Sabit</Badge>}
                    <Badge className={a.scope === "ORGANIZATION" ? "bg-primary-soft text-primary" : "bg-surface-2 text-muted"}>
                      {a.scope === "ORGANIZATION" ? "Kurum geneli" : teamName(a.teamId)}
                    </Badge>
                  </div>
                  <p className="mt-1 text-xs text-muted">{a.author.fullName} · {fmtDateTime(a.createdAt)}</p>
                  <p className="mt-3 text-sm whitespace-pre-wrap text-text">{a.body}</p>
                </div>
                {!can.readOnly && (a.author.id === user.id || can.direct) && (
                  <Button variant="ghost" size="sm" aria-label="Duyuruyu sil" onClick={() => confirm("Duyuru silinsin mi?") && del.mutate(a.id, { onError: (e) => toast("error", errorMessage(e)) })}>
                    <Trash2 className="size-4" />
                  </Button>
                )}
              </div>
            </Card>
          ))}
        </div>
      )}
      <Modal
        open={open}
        onClose={() => setOpen(false)}
        title="Yeni duyuru"
        footer={
          <>
            <Button variant="secondary" onClick={() => setOpen(false)}>Vazgeç</Button>
            <Button
              disabled={!valid}
              loading={create.isPending}
              onClick={() =>
                create.mutate(
                  { scope, teamId: scope === "TEAM" ? teamId || managed[0]?.id : undefined, title: title.trim(), body: body.trim(), pinned },
                  { onSuccess: () => (toast("success", "Duyuru yayınlandı."), setOpen(false), setTitle(""), setBody("")), onError: (e) => toast("error", errorMessage(e)) },
                )
              }
            >
              Yayınla
            </Button>
          </>
        }
      >
        <div className="space-y-4">
          <Field label="Kapsam" htmlFor="a-scope">
            <Select id="a-scope" value={scope} onChange={(e) => setScope(e.target.value as "TEAM" | "ORGANIZATION")}>
              <option value="TEAM">Ekip</option>
              {can.direct && <option value="ORGANIZATION">Kurum geneli</option>}
            </Select>
          </Field>
          {scope === "TEAM" && (
            <Field label="Ekip" htmlFor="a-team">
              <Select id="a-team" value={teamId || managed[0]?.id || ""} onChange={(e) => setTeamId(e.target.value)}>
                {managed.map((t) => <option key={t.id} value={t.id}>{t.name}</option>)}
              </Select>
            </Field>
          )}
          <Field label="Başlık" htmlFor="a-title"><Input id="a-title" value={title} onChange={(e) => setTitle(e.target.value)} maxLength={200} /></Field>
          <Field label="Metin" htmlFor="a-body"><Textarea id="a-body" value={body} onChange={(e) => setBody(e.target.value)} maxLength={5000} /></Field>
          <label className="flex items-center gap-2 text-sm"><input type="checkbox" checked={pinned} onChange={(e) => setPinned(e.target.checked)} className="size-4 accent-[var(--primary)]" />Sabitle</label>
        </div>
      </Modal>
    </>
  );
}

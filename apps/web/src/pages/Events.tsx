import { zodResolver } from "@hookform/resolvers/zod";
import { CalendarDays, Check, ExternalLink, MapPin, Plus, Users, X } from "lucide-react";
import { useState } from "react";
import { useForm } from "react-hook-form";
import { z } from "zod";
import {
  errorMessage,
  useCreateEvent,
  useDecideParticipation,
  useEvents,
  useParticipations,
  useRequestParticipation,
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
  Select,
  Skeleton,
  Spinner,
  Tabs,
  Textarea,
  useToast,
} from "../components/ui";
import {
  eventScopeLabel,
  eventTypeLabel,
  participationRoleLabel,
  participationStatusLabel,
} from "../i18n/tr";
import { fmtDateTime } from "../lib/format";

const pTone: Record<Schemas["ParticipationStatus"], string> = {
  REQUESTED: "bg-warning-soft text-blocked",
  APPROVED: "bg-info-soft text-progress",
  ATTENDED: "bg-success-soft text-done",
  REJECTED: "bg-danger-soft text-danger",
  CANCELLED: "bg-surface-2 text-muted",
};

export function EventsPage() {
  const { can } = useAuth();
  const [scope, setScope] = useState<"" | Schemas["EventScope"]>("");
  const [mine, setMine] = useState(false);
  const [creating, setCreating] = useState(false);
  const [selected, setSelected] = useState<Schemas["Event"] | null>(null);
  const events = useEvents({ scope: scope || undefined, participantId: mine ? "me" : undefined });
  const now = Date.now();
  const upcoming = events.data?.items.filter((e) => new Date(e.endsAt).getTime() >= now).reverse() ?? [];
  const past = events.data?.items.filter((e) => new Date(e.endsAt).getTime() < now) ?? [];
  return (
    <>
      <PageHeader
        title="Etkinlikler"
        subtitle="Bireysel ve kurumsal katılımlar, eğitimler, konferanslar, CTF'ler"
        actions={!can.readOnly && <Button onClick={() => setCreating(true)}><Plus className="size-4" />Yeni etkinlik</Button>}
      />
      <div className="mb-4 flex flex-wrap items-center gap-3">
        <Tabs<"" | Schemas["EventScope"]>
          value={scope}
          onChange={setScope}
          items={[{ value: "", label: "Tümü" }, { value: "CORPORATE", label: "Kurumsal" }, { value: "INDIVIDUAL", label: "Bireysel" }]}
        />
        <label className="flex items-center gap-2 text-sm text-text">
          <input type="checkbox" checked={mine} onChange={(e) => setMine(e.target.checked)} className="size-4 accent-[var(--primary)]" />
          Sadece katıldıklarım
        </label>
      </div>
      {events.error ? (
        <Card><ErrorState message={errorMessage(events.error)} onRetry={() => void events.refetch()} /></Card>
      ) : events.isPending ? (
        <Skeleton className="h-64" />
      ) : events.data.items.length === 0 ? (
        <Card><EmptyState title="Etkinlik yok" /></Card>
      ) : (
        <div className="space-y-8">
          <EventGrid title="Yaklaşan" items={upcoming} onOpen={setSelected} />
          <EventGrid title="Geçmiş" items={past} onOpen={setSelected} />
        </div>
      )}
      <EventFormModal open={creating} onClose={() => setCreating(false)} />
      <EventDetailModal event={selected} onClose={() => setSelected(null)} />
    </>
  );
}

function EventGrid({ title, items, onOpen }: { title: string; items: Schemas["Event"][]; onOpen: (e: Schemas["Event"]) => void }) {
  if (!items.length) return null;
  return (
    <section>
      <h2 className="mb-3 text-sm font-semibold tracking-wide text-muted uppercase">{title}</h2>
      <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
        {items.map((e) => (
          <button key={e.id} onClick={() => onOpen(e)} className="rounded-xl text-left">
            <Card className="h-full p-5 transition-colors hover:border-primary">
              <div className="flex flex-wrap gap-1.5">
                <Badge className={e.scope === "CORPORATE" ? "bg-primary-soft text-primary" : "bg-surface-2 text-muted"}>{eventScopeLabel[e.scope]}</Badge>
                <Badge className="bg-surface-2 text-muted">{eventTypeLabel[e.type]}</Badge>
                {e.myParticipation && <Badge className={pTone[e.myParticipation.status]}>{participationStatusLabel[e.myParticipation.status]}</Badge>}
              </div>
              <h3 className="mt-3 font-semibold text-text">{e.title}</h3>
              <p className="mt-2 flex items-center gap-1.5 text-xs text-muted"><CalendarDays className="size-3.5" />{fmtDateTime(e.startsAt)}</p>
              {e.location && <p className="mt-1 flex items-center gap-1.5 text-xs text-muted"><MapPin className="size-3.5" />{e.location}</p>}
              <p className="mt-1 flex items-center gap-1.5 text-xs text-muted"><Users className="size-3.5" />{e.participantCount ?? 0} katılımcı</p>
            </Card>
          </button>
        ))}
      </div>
    </section>
  );
}

function EventDetailModal({ event, onClose }: { event: Schemas["Event"] | null; onClose: () => void }) {
  const { user, can } = useAuth();
  const toast = useToast();
  const parts = useParticipations(event?.id);
  const request = useRequestParticipation();
  const decide = useDecideParticipation();
  const [role, setRole] = useState<Schemas["ParticipationRole"]>("ATTENDEE");
  if (!event) return null;
  const mine = parts.data?.find((p) => p.user.id === user.id) ?? event.myParticipation;
  const onError = (e: unknown) => toast("error", errorMessage(e));
  const act = (id: string, status: Schemas["ParticipationDecision"]["status"]) =>
    decide.mutate({ id, status }, { onSuccess: () => toast("success", participationStatusLabel[status]), onError });
  return (
    <Modal open={!!event} onClose={onClose} title={event.title} wide>
      <div className="space-y-4">
        <div className="flex flex-wrap gap-1.5">
          <Badge className="bg-primary-soft text-primary">{eventScopeLabel[event.scope]}</Badge>
          <Badge className="bg-surface-2 text-muted">{eventTypeLabel[event.type]}</Badge>
        </div>
        <dl className="grid grid-cols-2 gap-3 text-sm">
          <div><dt className="text-xs text-muted">Başlangıç</dt><dd>{fmtDateTime(event.startsAt)}</dd></div>
          <div><dt className="text-xs text-muted">Bitiş</dt><dd>{fmtDateTime(event.endsAt)}</dd></div>
          <div><dt className="text-xs text-muted">Yer</dt><dd>{event.location ?? "—"}</dd></div>
          <div><dt className="text-xs text-muted">Düzenleyen</dt><dd>{event.organizer ?? "—"}</dd></div>
        </dl>
        {event.description && <p className="text-sm whitespace-pre-wrap text-muted">{event.description}</p>}
        {event.url && (
          <a href={event.url} target="_blank" rel="noopener noreferrer nofollow" className="inline-flex items-center gap-1 text-sm text-primary hover:underline">
            Etkinlik sayfası <ExternalLink className="size-3.5" />
          </a>
        )}
        {!can.readOnly && (
          <div className="flex flex-wrap items-end gap-3 rounded-lg bg-surface-2 p-3">
            {mine && mine.status !== "CANCELLED" ? (
              <>
                <p className="text-sm">Katılım durumunuz: <Badge className={pTone[mine.status]}>{participationStatusLabel[mine.status]}</Badge></p>
                {["REQUESTED", "APPROVED"].includes(mine.status) && (
                  <Button size="sm" variant="secondary" onClick={() => act(mine.id, "CANCELLED")}>Talebi iptal et</Button>
                )}
              </>
            ) : (
              <>
                <Field label="Rolüm" htmlFor="p-role">
                  <Select id="p-role" value={role} onChange={(e) => setRole(e.target.value as Schemas["ParticipationRole"])} className="w-40">
                    {Object.entries(participationRoleLabel).map(([k, l]) => <option key={k} value={k}>{l}</option>)}
                  </Select>
                </Field>
                <Button loading={request.isPending} onClick={() => request.mutate({ eventId: event.id, role }, { onSuccess: () => toast("success", "Katılım talebiniz yöneticinize iletildi."), onError })}>
                  Katılım talep et
                </Button>
              </>
            )}
          </div>
        )}
        <div>
          <h3 className="mb-2 text-sm font-semibold">Katılımcılar</h3>
          {parts.isPending ? <Spinner /> : parts.error ? <ErrorState message={errorMessage(parts.error)} /> : !parts.data.length ? (
            <EmptyState title="Henüz katılımcı yok" />
          ) : (
            <ul className="divide-y divide-border rounded-lg border border-border">
              {parts.data.map((p) => (
                <li key={p.id} className="flex flex-wrap items-center gap-3 px-3 py-2 text-sm">
                  <span className="flex-1 text-text">{p.user.fullName} <span className="text-xs text-muted">· {participationRoleLabel[p.role]}</span></span>
                  <Badge className={pTone[p.status]}>{participationStatusLabel[p.status]}</Badge>
                  {can.manage && p.user.id !== user.id && (
                    <span className="flex gap-1">
                      {p.status === "REQUESTED" && (
                        <>
                          <Button size="sm" variant="secondary" aria-label="Onayla" onClick={() => act(p.id, "APPROVED")}><Check className="size-4 text-done" /></Button>
                          <Button size="sm" variant="secondary" aria-label="Reddet" onClick={() => act(p.id, "REJECTED")}><X className="size-4 text-danger" /></Button>
                        </>
                      )}
                      {p.status === "APPROVED" && new Date(event.endsAt) < new Date() && (
                        <Button size="sm" variant="secondary" onClick={() => act(p.id, "ATTENDED")}>Katıldı</Button>
                      )}
                    </span>
                  )}
                </li>
              ))}
            </ul>
          )}
        </div>
      </div>
    </Modal>
  );
}

const eventSchema = z
  .object({
    title: z.string().trim().min(3, "En az 3 karakter.").max(200),
    type: z.enum(["CONFERENCE", "TRAINING", "CTF", "WEBINAR", "WORKSHOP", "MEETUP", "OTHER"]),
    scope: z.enum(["INDIVIDUAL", "CORPORATE"]),
    startsAt: z.string().min(1, "Zorunlu."),
    endsAt: z.string().min(1, "Zorunlu."),
    location: z.string().max(200).optional(),
    organizer: z.string().max(150).optional(),
    url: z.string().max(500).regex(/^(https:\/\/.+)?$/, "Sadece https:// bağlantıları.").optional(),
    description: z.string().max(10000).optional(),
  })
  .refine((v) => !v.startsAt || !v.endsAt || v.endsAt >= v.startsAt, { path: ["endsAt"], message: "Bitiş başlangıçtan önce olamaz." });
type EventForm = z.infer<typeof eventSchema>;

function EventFormModal({ open, onClose }: { open: boolean; onClose: () => void }) {
  const { can } = useAuth();
  const toast = useToast();
  const create = useCreateEvent();
  const { register, handleSubmit, reset, formState } = useForm<EventForm>({
    resolver: zodResolver(eventSchema),
    defaultValues: { type: "CONFERENCE", scope: "INDIVIDUAL" },
  });
  const e = formState.errors;
  const submit = handleSubmit((v) =>
    create.mutate(
      {
        ...v,
        startsAt: new Date(v.startsAt).toISOString(),
        endsAt: new Date(v.endsAt).toISOString(),
        url: v.url || undefined,
        location: v.location || undefined,
        organizer: v.organizer || undefined,
        description: v.description || undefined,
      },
      { onSuccess: () => (toast("success", "Etkinlik oluşturuldu."), reset(), onClose()), onError: (err) => toast("error", errorMessage(err)) },
    ),
  );
  return (
    <Modal open={open} onClose={onClose} title="Yeni etkinlik" wide footer={<><Button variant="secondary" onClick={onClose}>Vazgeç</Button><Button loading={create.isPending} onClick={() => void submit()}>Oluştur</Button></>}>
      <form noValidate className="grid gap-4 sm:grid-cols-2" onSubmit={(ev) => (ev.preventDefault(), void submit())}>
        <div className="sm:col-span-2"><Field label="Başlık" htmlFor="e-title" error={e.title?.message}><Input id="e-title" {...register("title")} /></Field></div>
        <Field label="Tür" htmlFor="e-type"><Select id="e-type" {...register("type")}>{Object.entries(eventTypeLabel).map(([k, l]) => <option key={k} value={k}>{l}</option>)}</Select></Field>
        <Field label="Katılım tipi" htmlFor="e-scope" hint={can.direct ? undefined : "Kurumsal etkinlikleri direktör oluşturur."}>
          <Select id="e-scope" {...register("scope")}>
            <option value="INDIVIDUAL">Bireysel</option>
            {can.direct && <option value="CORPORATE">Kurumsal</option>}
          </Select>
        </Field>
        <Field label="Başlangıç" htmlFor="e-start" error={e.startsAt?.message}><Input id="e-start" type="datetime-local" {...register("startsAt")} /></Field>
        <Field label="Bitiş" htmlFor="e-end" error={e.endsAt?.message}><Input id="e-end" type="datetime-local" {...register("endsAt")} /></Field>
        <Field label="Yer" htmlFor="e-loc"><Input id="e-loc" {...register("location")} /></Field>
        <Field label="Düzenleyen" htmlFor="e-org"><Input id="e-org" {...register("organizer")} /></Field>
        <div className="sm:col-span-2"><Field label="Bağlantı" htmlFor="e-url" error={e.url?.message}><Input id="e-url" type="url" placeholder="https://" {...register("url")} /></Field></div>
        <div className="sm:col-span-2"><Field label="Açıklama" htmlFor="e-desc"><Textarea id="e-desc" {...register("description")} /></Field></div>
      </form>
    </Modal>
  );
}

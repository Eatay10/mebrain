import { zodResolver } from "@hookform/resolvers/zod";
import { Award, CalendarDays, Check, ExternalLink, ImagePlus, MapPin, Pencil, Plus, Trash2, Users, X } from "lucide-react";
import { useState } from "react";
import { useForm } from "react-hook-form";
import { z } from "zod";
import {
  errorMessage,
  useCompetencyCatalog,
  useCreateEvent,
  useDecideParticipation,
  useDeleteEventPhoto,
  useEventPhotos,
  useEvents,
  useParticipations,
  useRequestParticipation,
  useUpdateEvent,
  useUploadEventPhoto,
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
        {(event.competencies?.length ?? 0) > 0 && (
          <div className="flex flex-wrap items-center gap-1.5 text-xs">
            <Award className="size-4 text-primary" aria-hidden />
            <span className="text-muted">Katılım tamamlanınca artan yetkinlikler:</span>
            {event.competencies!.map((c) => (
              <Badge key={c.competencyId} className="bg-success-soft text-done">{c.name} +{c.points}</Badge>
            ))}
          </div>
        )}
        <EventNotes event={event} />
        <EventPhotos event={event} canUpload={!can.readOnly && (event.createdBy.id === user.id || can.direct || ["APPROVED", "ATTENDED"].includes(mine?.status ?? ""))} />
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
    notes: z.string().max(10000).optional(),
    competencyIds: z.array(z.string()).max(10),
    competencyPoints: z.coerce.number().int().min(1).max(50),
  })
  .refine((v) => !v.startsAt || !v.endsAt || v.endsAt >= v.startsAt, { path: ["endsAt"], message: "Bitiş başlangıçtan önce olamaz." });
type EventForm = z.infer<typeof eventSchema>;

function EventFormModal({ open, onClose }: { open: boolean; onClose: () => void }) {
  const { can } = useAuth();
  const toast = useToast();
  const create = useCreateEvent();
  const catalog = useCompetencyCatalog();
  const { register, handleSubmit, reset, formState, watch, setValue } = useForm<EventForm>({
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    resolver: zodResolver(eventSchema) as any,
    defaultValues: { type: "CONFERENCE", scope: "INDIVIDUAL", competencyIds: [], competencyPoints: 10 },
  });
  const selected = watch("competencyIds") ?? [];
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
        notes: v.notes || undefined,
        competencyIds: v.competencyIds.length ? v.competencyIds : undefined,
        competencyPoints: v.competencyIds.length ? v.competencyPoints : undefined,
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
        <div className="sm:col-span-2">
          <Field label="Konferans notları / bilgiler" htmlFor="e-notes" hint="Konuşmalar, öğrenilenler, paylaşılacak kaynaklar. Sonradan da eklenebilir.">
            <Textarea id="e-notes" {...register("notes")} />
          </Field>
        </div>
        <fieldset className="sm:col-span-2">
          <legend className="mb-1.5 text-sm font-medium text-text">Tamamlanınca artacak yetkinlikler</legend>
          <div className="flex max-h-32 flex-wrap gap-1.5 overflow-y-auto">
            {(catalog.data ?? []).map((c) => {
              const on = selected.includes(c.id);
              return (
                <button
                  key={c.id}
                  type="button"
                  aria-pressed={on}
                  onClick={() => setValue("competencyIds", on ? selected.filter((x) => x !== c.id) : [...selected, c.id])}
                  className={on ? "rounded-full bg-primary px-2.5 py-1 text-xs text-on-primary" : "rounded-full bg-surface-2 px-2.5 py-1 text-xs text-text hover:bg-primary-soft"}
                >
                  {c.name}
                </button>
              );
            })}
          </div>
        </fieldset>
        {selected.length > 0 && (
          <Field label="Yetkinlik başına puan" htmlFor="e-points" hint="Katılımcı 'Katıldı' olarak işaretlenince eklenir (en fazla %100).">
            <Input id="e-points" type="number" min={1} max={50} {...register("competencyPoints")} />
          </Field>
        )}
      </form>
    </Modal>
  );
}

function EventNotes({ event }: { event: Schemas["Event"] }) {
  const { user, can } = useAuth();
  const toast = useToast();
  const update = useUpdateEvent(event.id);
  const [editing, setEditing] = useState(false);
  const [notes, setNotes] = useState(event.notes ?? "");
  const canEdit = !can.readOnly && (event.createdBy.id === user.id || can.direct);
  if (!event.notes && !canEdit) return null;
  return (
    <div className="rounded-lg border border-border p-3">
      <div className="mb-1 flex items-center gap-2">
        <h3 className="text-sm font-semibold">Konferans notları</h3>
        {canEdit && !editing && (
          <Button size="sm" variant="ghost" className="ml-auto" aria-label="Notları düzenle" onClick={() => (setNotes(event.notes ?? ""), setEditing(true))}>
            <Pencil className="size-4" />
          </Button>
        )}
      </div>
      {editing ? (
        <div className="space-y-2">
          <label htmlFor="ev-notes" className="sr-only">Konferans notları</label>
          <Textarea id="ev-notes" value={notes} onChange={(e) => setNotes(e.target.value)} maxLength={10000} />
          <div className="flex justify-end gap-2">
            <Button size="sm" variant="secondary" onClick={() => setEditing(false)}>Vazgeç</Button>
            <Button
              size="sm"
              loading={update.isPending}
              onClick={() =>
                update.mutate(
                  { notes: notes.trim() || null },
                  { onSuccess: () => (setEditing(false), toast("success", "Notlar kaydedildi.")), onError: (e) => toast("error", errorMessage(e)) },
                )
              }
            >
              Kaydet
            </Button>
          </div>
        </div>
      ) : event.notes ? (
        <p className="text-sm whitespace-pre-wrap text-text">{event.notes}</p>
      ) : (
        <p className="text-xs text-muted">Henüz not eklenmedi.</p>
      )}
    </div>
  );
}

function EventPhotos({ event, canUpload }: { event: Schemas["Event"]; canUpload: boolean }) {
  const { user, can } = useAuth();
  const toast = useToast();
  const photos = useEventPhotos(event.id);
  const upload = useUploadEventPhoto(event.id);
  const del = useDeleteEventPhoto(event.id);
  const [caption, setCaption] = useState("");
  const [zoom, setZoom] = useState<Schemas["EventPhoto"] | null>(null);
  const items = photos.data ?? [];
  if (!canUpload && items.length === 0) return null;
  return (
    <div>
      <div className="mb-2 flex flex-wrap items-center gap-2">
        <h3 className="text-sm font-semibold">Fotoğraflar ({items.length})</h3>
        {canUpload && (
          <div className="ml-auto flex items-center gap-2">
            <label htmlFor="ph-caption" className="sr-only">Fotoğraf açıklaması</label>
            <Input id="ph-caption" value={caption} onChange={(e) => setCaption(e.target.value)} placeholder="Açıklama (isteğe bağlı)" maxLength={300} className="h-8 w-48 text-xs" />
            <label className="inline-flex cursor-pointer items-center gap-1.5 rounded-lg bg-surface-2 px-3 py-1.5 text-xs font-medium hover:bg-primary-soft">
              <ImagePlus className="size-4" /> {upload.isPending ? "Yükleniyor…" : "Fotoğraf ekle"}
              <input
                type="file"
                accept="image/jpeg,image/png,image/webp"
                className="sr-only"
                aria-label="Fotoğraf ekle"
                onChange={(e) => {
                  const f = e.target.files?.[0];
                  e.target.value = "";
                  if (!f) return;
                  if (f.size > 10 * 1024 * 1024) return toast("error", "Fotoğraf en fazla 10 MB olabilir.");
                  upload.mutate(
                    { file: f, caption: caption.trim() || undefined },
                    { onSuccess: () => (setCaption(""), toast("success", "Fotoğraf yüklendi.")), onError: (err) => toast("error", errorMessage(err)) },
                  );
                }}
              />
            </label>
          </div>
        )}
      </div>
      {items.length > 0 && (
        <ul className="grid grid-cols-2 gap-2 sm:grid-cols-4">
          {items.map((ph) => (
            <li key={ph.id} className="group relative overflow-hidden rounded-lg border border-border bg-surface-2">
              <button className="block w-full" onClick={() => setZoom(ph)} aria-label={ph.caption ?? "Fotoğrafı büyüt"}>
                <img src={`/api/v1/event-photos/${ph.id}`} alt={ph.caption ?? `${event.title} fotoğrafı`} className="aspect-square w-full object-cover" loading="lazy" />
              </button>
              {ph.caption && <p className="truncate px-2 py-1 text-xs text-muted">{ph.caption}</p>}
              {!can.readOnly && (ph.uploadedBy.id === user.id || event.createdBy.id === user.id || can.direct) && (
                <button
                  className="absolute top-1 right-1 rounded-md bg-surface/90 p-1 text-muted opacity-0 group-hover:opacity-100 hover:text-danger focus:opacity-100"
                  aria-label="Fotoğrafı sil"
                  onClick={() => confirm("Fotoğraf silinsin mi?") && del.mutate(ph.id, { onError: (err) => toast("error", errorMessage(err)) })}
                >
                  <Trash2 className="size-4" />
                </button>
              )}
            </li>
          ))}
        </ul>
      )}
      {zoom && (
        <Modal open onClose={() => setZoom(null)} title={zoom.caption ?? event.title} wide>
          <img src={`/api/v1/event-photos/${zoom.id}`} alt={zoom.caption ?? event.title} className="max-h-[70vh] w-full rounded-lg object-contain" />
          <p className="mt-2 text-xs text-muted">{zoom.uploadedBy.fullName} · {fmtDateTime(zoom.createdAt)}</p>
        </Modal>
      )}
    </div>
  );
}

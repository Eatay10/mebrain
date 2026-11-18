import { BadgeCheck, Plus, Trash2 } from "lucide-react";
import { useState } from "react";
import {
  errorMessage,
  useCompetencyCatalog,
  useCompetencyMatrix,
  useCreateCatalogItem,
  useDeleteCompetency,
  useTeams,
  useUpsertCompetency,
  useUserCompetencies,
  type Schemas,
} from "../api/hooks";
import { useAuth } from "../auth";
import {
  Button,
  Card,
  CardHeader,
  cx,
  EmptyState,
  ErrorState,
  Field,
  Input,
  Modal,
  PageHeader,
  Select,
  Skeleton,
  Tabs,
  useToast,
} from "../components/ui";
import { competencyCategoryLabel } from "../i18n/tr";

const LEVELS = ["", "Başlangıç", "Temel", "Orta", "İleri", "Uzman"];
const levelTone = ["", "bg-surface-2", "bg-primary-soft", "bg-primary/30", "bg-primary/60", "bg-primary"];

export function CompetenciesPage() {
  const { can } = useAuth();
  const [tab, setTab] = useState<"mine" | "matrix">("mine");
  return (
    <>
      <PageHeader
        title="Yetkinlikler"
        subtitle="Bireysel yetkinlik seviyeleri ve ekip yetkinlik matrisi"
        actions={(can.manage || can.observe) && <Tabs value={tab} onChange={setTab} items={[{ value: "mine", label: "Yetkinliklerim" }, { value: "matrix", label: "Ekip matrisi" }]} />}
      />
      {tab === "mine" ? <MyCompetencies /> : <TeamMatrix />}
    </>
  );
}

function MyCompetencies() {
  const { user, can } = useAuth();
  const toast = useToast();
  const mine = useUserCompetencies(user.id);
  const catalog = useCompetencyCatalog();
  const upsert = useUpsertCompetency();
  const remove = useDeleteCompetency();
  const [adding, setAdding] = useState(false);
  const [newComp, setNewComp] = useState("");
  const [level, setLevel] = useState(3);
  const [evidence, setEvidence] = useState("");
  const [catalogOpen, setCatalogOpen] = useState(false);
  const owned = new Set(mine.data?.map((m) => m.competency.id));
  const onError = (e: unknown) => toast("error", errorMessage(e));
  return (
    <Card>
      <CardHeader
        title="Yetkinliklerim"
        subtitle="Seviyenizi güncellediğinizde yönetici doğrulaması sıfırlanır."
        actions={
          !can.readOnly && (
            <>
              {can.manage && <Button variant="secondary" size="sm" onClick={() => setCatalogOpen(true)}>Kataloğa ekle</Button>}
              <Button size="sm" onClick={() => setAdding(true)}><Plus className="size-4" />Yetkinlik ekle</Button>
            </>
          )
        }
      />
      {mine.isPending ? (
        <Skeleton className="m-5 h-40" />
      ) : mine.error ? (
        <ErrorState message={errorMessage(mine.error)} />
      ) : !mine.data.length ? (
        <EmptyState title="Henüz yetkinlik eklemediniz" />
      ) : (
        <ul className="divide-y divide-border">
          {mine.data.map((m) => (
            <li key={m.competency.id} className="flex flex-wrap items-center gap-4 px-5 py-3">
              <div className="min-w-48 flex-1">
                <p className="flex items-center gap-1.5 font-medium text-text">
                  {m.competency.name}
                  {m.verifiedBy && <BadgeCheck className="size-4 text-done" aria-label={`${m.verifiedBy.fullName} tarafından doğrulandı`} />}
                </p>
                <p className="text-xs text-muted">{competencyCategoryLabel[m.competency.category]}{m.evidence ? ` · ${m.evidence}` : ""}</p>
              </div>
              <label className="sr-only" htmlFor={`lvl-${m.competency.id}`}>Seviye</label>
              <Select
                id={`lvl-${m.competency.id}`}
                className="w-36"
                value={m.level}
                disabled={can.readOnly || upsert.isPending}
                onChange={(e) => upsert.mutate({ userId: user.id, competencyId: m.competency.id, level: Number(e.target.value), evidence: m.evidence ?? undefined }, { onError })}
              >
                {[1, 2, 3, 4, 5].map((l) => <option key={l} value={l}>{l} · {LEVELS[l]}</option>)}
              </Select>
              {!can.readOnly && (
                <Button variant="ghost" size="sm" aria-label={`${m.competency.name} kaldır`} onClick={() => remove.mutate({ userId: user.id, competencyId: m.competency.id }, { onError })}>
                  <Trash2 className="size-4" />
                </Button>
              )}
            </li>
          ))}
        </ul>
      )}
      <Modal
        open={adding}
        onClose={() => setAdding(false)}
        title="Yetkinlik ekle"
        footer={<><Button variant="secondary" onClick={() => setAdding(false)}>Vazgeç</Button><Button disabled={!newComp} loading={upsert.isPending} onClick={() => upsert.mutate({ userId: user.id, competencyId: newComp, level, evidence: evidence || undefined }, { onSuccess: () => (setAdding(false), setNewComp(""), setEvidence("")), onError })}>Ekle</Button></>}
      >
        <div className="space-y-4">
          <Field label="Yetkinlik" htmlFor="c-comp">
            <Select id="c-comp" value={newComp} onChange={(e) => setNewComp(e.target.value)}>
              <option value="">Seçin…</option>
              {catalog.data?.filter((c) => !owned.has(c.id)).map((c) => <option key={c.id} value={c.id}>{c.name} ({competencyCategoryLabel[c.category]})</option>)}
            </Select>
          </Field>
          <Field label="Seviye" htmlFor="c-level">
            <Select id="c-level" value={level} onChange={(e) => setLevel(Number(e.target.value))}>
              {[1, 2, 3, 4, 5].map((l) => <option key={l} value={l}>{l} · {LEVELS[l]}</option>)}
            </Select>
          </Field>
          <Field label="Kanıt (sertifika, proje…)" htmlFor="c-ev"><Input id="c-ev" value={evidence} onChange={(e) => setEvidence(e.target.value)} maxLength={500} /></Field>
        </div>
      </Modal>
      <CatalogModal open={catalogOpen} onClose={() => setCatalogOpen(false)} />
    </Card>
  );
}

function CatalogModal({ open, onClose }: { open: boolean; onClose: () => void }) {
  const toast = useToast();
  const create = useCreateCatalogItem();
  const [name, setName] = useState("");
  const [category, setCategory] = useState<Schemas["CompetencyCategory"]>("DEFENSIVE");
  return (
    <Modal
      open={open}
      onClose={onClose}
      title="Kataloğa yetkinlik ekle"
      footer={<><Button variant="secondary" onClick={onClose}>Vazgeç</Button><Button disabled={name.trim().length < 2} loading={create.isPending} onClick={() => create.mutate({ name: name.trim(), category }, { onSuccess: () => (toast("success", "Eklendi."), setName(""), onClose()), onError: (e) => toast("error", errorMessage(e)) })}>Ekle</Button></>}
    >
      <div className="space-y-4">
        <Field label="Ad" htmlFor="cat-name"><Input id="cat-name" value={name} onChange={(e) => setName(e.target.value)} maxLength={100} /></Field>
        <Field label="Kategori" htmlFor="cat-cat">
          <Select id="cat-cat" value={category} onChange={(e) => setCategory(e.target.value as Schemas["CompetencyCategory"])}>
            {Object.entries(competencyCategoryLabel).map(([k, l]) => <option key={k} value={k}>{l}</option>)}
          </Select>
        </Field>
      </div>
    </Modal>
  );
}

function TeamMatrix() {
  const { managesTeam, can } = useAuth();
  const toast = useToast();
  const teams = useTeams();
  const allowed = (teams.data ?? []).filter((t) => can.observe || managesTeam(t.id));
  const [teamId, setTeamId] = useState<string>("");
  const active = teamId || allowed[0]?.id;
  const matrix = useCompetencyMatrix(active);
  const upsert = useUpsertCompetency();
  return (
    <Card>
      <CardHeader
        title="Ekip yetkinlik matrisi"
        subtitle="Hücreye tıklayarak doğrulayın (yönetici)"
        actions={
          <Select aria-label="Ekip" value={active ?? ""} onChange={(e) => setTeamId(e.target.value)} className="w-48">
            {allowed.map((t) => <option key={t.id} value={t.id}>{t.name}</option>)}
          </Select>
        }
      />
      {matrix.isPending ? (
        <Skeleton className="m-5 h-64" />
      ) : matrix.error ? (
        <ErrorState message={errorMessage(matrix.error)} />
      ) : !matrix.data.competencies.length ? (
        <EmptyState title="Bu ekipte kayıtlı yetkinlik yok" />
      ) : (
        <div className="overflow-x-auto p-4">
          <table className="text-xs">
            <thead>
              <tr>
                <th scope="col" className="sticky left-0 bg-surface px-2 py-2 text-left font-medium text-muted">Üye</th>
                {matrix.data.competencies.map((c) => (
                  <th key={c.id} scope="col" className="h-32 min-w-10 px-1 align-bottom font-medium text-muted">
                    <span className="inline-block origin-bottom-left translate-x-4 -rotate-45 whitespace-nowrap">{c.name}</span>
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {matrix.data.members.map((m) => (
                <tr key={m.user.id}>
                  <th scope="row" className="sticky left-0 bg-surface px-2 py-1 text-left font-normal whitespace-nowrap text-text">{m.user.fullName}</th>
                  {matrix.data.competencies.map((c) => {
                    const lvl = m.levels[c.id];
                    return (
                      <td key={c.id} className="p-0.5">
                        <button
                          disabled={!lvl || !can.manage}
                          title={lvl ? `${c.name}: ${lvl} · ${LEVELS[lvl]}` : "Yok"}
                          aria-label={`${m.user.fullName}, ${c.name}: ${lvl ? `seviye ${lvl}` : "yok"}`}
                          onClick={() => lvl && upsert.mutate({ userId: m.user.id, competencyId: c.id, level: lvl, verified: true }, { onSuccess: () => toast("success", "Doğrulandı."), onError: (e) => toast("error", errorMessage(e)) })}
                          className={cx("tabular flex size-9 items-center justify-center rounded-md font-semibold", lvl ? levelTone[lvl] : "bg-surface-2/40", lvl && lvl >= 4 ? "text-on-primary" : "text-text")}
                        >
                          {lvl ?? ""}
                        </button>
                      </td>
                    );
                  })}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </Card>
  );
}

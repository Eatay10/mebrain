import { Copy, KeyRound, Plus } from "lucide-react";
import { useState } from "react";
import { errorMessage, useApiTokens, useCreateApiToken, useRevokeApiToken, type Schemas } from "../api/hooks";
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
  Select,
  Skeleton,
  useToast,
} from "../components/ui";
import { scopeLabel } from "../i18n/tr";
import { fmtDate, fmtRelative } from "../lib/format";

const ALL_SCOPES = Object.keys(scopeLabel) as Schemas["ApiScope"][];

export function TokensPage() {
  const { can } = useAuth();
  const toast = useToast();
  const tokens = useApiTokens();
  const revoke = useRevokeApiToken();
  const create = useCreateApiToken();
  const [open, setOpen] = useState(false);
  const [name, setName] = useState("Claude MCP");
  const [days, setDays] = useState(30);
  const [scopes, setScopes] = useState<Schemas["ApiScope"][]>(["tasks:read", "reports:read", "projects:read", "events:read"]);
  const [created, setCreated] = useState<string | null>(null);
  const writeScopes: Schemas["ApiScope"][] = ["tasks:write", "events:write"];
  const mcpConfig = `{
  "mcpServers": {
    "cyber-task-hub": {
      "command": "uv",
      "args": ["--directory", "<repo>/apps/mcp", "run", "cth-mcp"],
      "env": { "CTH_API_BASE_URL": "${location.origin}/api/v1", "CTH_API_TOKEN": "<token>" }
    }
  }
}`;
  return (
    <>
      <PageHeader
        title="API & MCP erişimi"
        subtitle="Kişisel API token'ları — entegrasyonlar ve AI asistanları (MCP) için"
        actions={<Button onClick={() => (setOpen(true), setCreated(null))}><Plus className="size-4" />Yeni token</Button>}
      />
      <div className="grid gap-6 xl:grid-cols-3">
        <Card className="xl:col-span-2">
          <CardHeader title="Token'larım" subtitle="Token'ın etkin yetkisi = seçilen kapsamlar ∩ rolünüz. Silme ve yönetim işlemleri token ile yapılamaz." />
          {tokens.error ? <ErrorState message={errorMessage(tokens.error)} /> : !tokens.data ? <Skeleton className="m-5 h-32" /> : !tokens.data.length ? (
            <EmptyState title="Henüz token yok" description="MCP sunucusunu bağlamak için bir token oluşturun." />
          ) : (
            <ul className="divide-y divide-border">
              {tokens.data.map((t) => {
                const dead = !!t.revokedAt || new Date(t.expiresAt) < new Date();
                return (
                  <li key={t.id} className="flex flex-wrap items-center gap-3 px-5 py-3">
                    <KeyRound className="size-4 text-muted" aria-hidden />
                    <div className="min-w-48 flex-1">
                      <p className="font-medium text-text">{t.name} <code className="ml-1 text-xs text-muted">cth_{t.prefix}_…</code></p>
                      <p className="text-xs text-muted">Son kullanım: {fmtRelative(t.lastUsedAt)} · Bitiş: {fmtDate(t.expiresAt)}</p>
                      <div className="mt-1 flex flex-wrap gap-1">{t.scopes.map((s) => <Badge key={s} className="bg-surface-2 text-muted">{s}</Badge>)}</div>
                    </div>
                    {dead ? <Badge className="bg-surface-2 text-muted">{t.revokedAt ? "İptal edildi" : "Süresi doldu"}</Badge> : (
                      <Button variant="secondary" size="sm" onClick={() => confirm("Token iptal edilsin mi? Kullanan entegrasyonlar çalışmayı durdurur.") && revoke.mutate(t.id, { onSuccess: () => toast("success", "Token iptal edildi."), onError: (e) => toast("error", errorMessage(e)) })}>
                        İptal et
                      </Button>
                    )}
                  </li>
                );
              })}
            </ul>
          )}
        </Card>
        <Card>
          <CardHeader title="MCP bağlantısı" subtitle="Claude Desktop / Claude Code yapılandırması" />
          <div className="space-y-3 px-5 py-4 text-sm text-muted">
            <p>AI asistanınız şu araçları kullanabilir: <code>search_tasks</code>, <code>get_task</code>, <code>create_task</code>, <code>transition_task</code>, <code>add_task_comment</code>, <code>get_dashboard</code>, <code>get_task_report</code>, <code>list_projects</code>, <code>list_events</code>.</p>
            <pre className="overflow-x-auto rounded-lg bg-surface-2 p-3 text-xs text-text">{mcpConfig}</pre>
            <p className="text-xs">Task içerikleri asistana <em>güvenilmez içerik</em> olarak işaretlenerek iletilir (prompt injection koruması).</p>
          </div>
        </Card>
      </div>
      <Modal
        open={open}
        onClose={() => setOpen(false)}
        title={created ? "Token oluşturuldu" : "Yeni API token"}
        footer={created ? <Button onClick={() => setOpen(false)}>Kopyaladım, kapat</Button> : (
          <>
            <Button variant="secondary" onClick={() => setOpen(false)}>Vazgeç</Button>
            <Button disabled={!name.trim() || !scopes.length} loading={create.isPending} onClick={() => create.mutate({ name: name.trim(), scopes, expiresInDays: days }, { onSuccess: (r) => setCreated(r.token), onError: (e) => toast("error", errorMessage(e)) })}>Oluştur</Button>
          </>
        )}
      >
        {created ? (
          <div className="space-y-3">
            <p className="rounded-lg bg-warning-soft px-3 py-2 text-sm text-blocked">Bu token yalnızca şimdi gösterilir. Güvenli bir yere kaydedin; sohbetlere veya dokümanlara yapıştırmayın.</p>
            <div className="flex gap-2">
              <Input readOnly value={created} aria-label="Oluşturulan token" className="font-mono text-xs" onFocus={(e) => e.currentTarget.select()} />
              <Button variant="secondary" aria-label="Kopyala" onClick={() => void navigator.clipboard.writeText(created).then(() => toast("success", "Panoya kopyalandı."))}><Copy className="size-4" /></Button>
            </div>
          </div>
        ) : (
          <div className="space-y-4">
            <Field label="Ad" htmlFor="tk-name"><Input id="tk-name" value={name} onChange={(e) => setName(e.target.value)} maxLength={100} /></Field>
            <Field label="Geçerlilik" htmlFor="tk-days">
              <Select id="tk-days" value={days} onChange={(e) => setDays(Number(e.target.value))}>
                {[7, 30, 90].map((d) => <option key={d} value={d}>{d} gün</option>)}
              </Select>
            </Field>
            <fieldset>
              <legend className="mb-2 text-sm font-medium text-text">Kapsamlar</legend>
              <div className="grid gap-2 sm:grid-cols-2">
                {ALL_SCOPES.filter((s) => !(can.readOnly && writeScopes.includes(s))).map((s) => (
                  <label key={s} className="flex items-center gap-2 rounded-lg border border-border px-3 py-2 text-sm">
                    <input type="checkbox" className="size-4 accent-[var(--primary)]" checked={scopes.includes(s)} onChange={(e) => setScopes(e.target.checked ? [...scopes, s] : scopes.filter((x) => x !== s))} />
                    <span>{scopeLabel[s]}</span>
                    <code className="ml-auto text-[10px] text-muted">{s}</code>
                  </label>
                ))}
              </div>
            </fieldset>
          </div>
        )}
      </Modal>
    </>
  );
}

import { Activity, Download, ShieldAlert } from "lucide-react";
import { useState } from "react";
import { Area, AreaChart, CartesianGrid, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import {
  csvUrl,
  errorMessage,
  useAuditLogs,
  useMetricsSummary,
  useSecurityEvents,
  useSecuritySummary,
  type Schemas,
} from "../api/hooks";
import { useAuth } from "../auth";
import {
  Badge,
  Card,
  CardHeader,
  cx,
  EmptyState,
  ErrorState,
  PageHeader,
  Pagination,
  Select,
  Skeleton,
  Stat,
  Tabs,
} from "../components/ui";
import { fmtDateTime, fmtRelative } from "../lib/format";

type Tab = "security" | "performance" | "audit";
const sevTone: Record<Schemas["SecuritySeverity"], string> = {
  HIGH: "bg-danger-soft text-danger",
  MEDIUM: "bg-warning-soft text-blocked",
  LOW: "bg-info-soft text-progress",
  INFO: "bg-surface-2 text-muted",
};
const RULE_LABEL: Record<string, string> = {
  brute_force: "Kaba kuvvet girişimi",
  authz_burst: "Yetkisiz erişim taraması (IDOR)",
  token_abuse: "Geçersiz API token denemeleri",
  mass_export: "Toplu veri dışa aktarımı",
  account_lockout: "Hesap kilitlendi",
  privilege_change: "Yetki yükseltme",
};
const EVENT_TYPES: Schemas["SecurityEventType"][] = [
  "LOGIN_FAILED", "ACCOUNT_LOCKED", "AUTHZ_DENIED", "NOT_FOUND_PROBE", "CSRF_REJECTED", "RATE_LIMITED",
  "API_TOKEN_INVALID", "ROLE_CHANGED", "BULK_EXPORT", "PAYLOAD_TOO_LARGE", "VALIDATION_REJECTED", "LOGIN_SUCCESS",
];

export function SecurityPage() {
  const { can } = useAuth();
  const tabs = [
    ...(can.observe ? [{ value: "security" as Tab, label: "Güvenlik olayları" }, { value: "performance" as Tab, label: "Sistem & API" }] : []),
    { value: "audit" as Tab, label: "Denetim kaydı" },
  ];
  const [tab, setTab] = useState<Tab>(tabs[0]!.value);
  return (
    <>
      <PageHeader title="Güvenlik & İzleme" subtitle="Güvenlik olayları, alarmlar, sistem sağlığı ve denetim kaydı" actions={<Tabs value={tab} onChange={setTab} items={tabs} />} />
      {tab === "security" && <SecurityTab />}
      {tab === "performance" && <PerformanceTab />}
      {tab === "audit" && <AuditTab />}
    </>
  );
}

function SecurityTab() {
  const [window, setWindow] = useState<"1h" | "24h" | "7d">("24h");
  const [type, setType] = useState<Schemas["SecurityEventType"] | "">("");
  const [page, setPage] = useState(1);
  const summary = useSecuritySummary(window);
  const events = useSecurityEvents({ page, type: type || undefined });
  const s = summary.data;
  const c = (t: string) => s?.countsByType[t] ?? 0;
  const timeline = s?.timeline.map((b) => ({
    t: new Date(b.bucket).toLocaleTimeString("tr-TR", { hour: "2-digit", minute: "2-digit", ...(window === "7d" ? { day: "2-digit", month: "short" } : {}) }),
    Olay: b.count,
  }));
  return (
    <div className="space-y-6">
      <div className="flex justify-end">
        <Select aria-label="Zaman penceresi" value={window} onChange={(e) => setWindow(e.target.value as typeof window)} className="w-40">
          <option value="1h">Son 1 saat</option>
          <option value="24h">Son 24 saat</option>
          <option value="7d">Son 7 gün</option>
        </Select>
      </div>
      {summary.error ? (
        <Card><ErrorState message={errorMessage(summary.error)} /></Card>
      ) : (
        <>
          <div className="grid grid-cols-2 gap-4 md:grid-cols-3 xl:grid-cols-6">
            {s ? (
              <>
                <Stat label="Başarısız giriş" value={c("LOGIN_FAILED")} tone="text-blocked" />
                <Stat label="Kilitlenen hesap" value={c("ACCOUNT_LOCKED")} tone="text-danger" />
                <Stat label="Yetki reddi" value={c("AUTHZ_DENIED") + c("NOT_FOUND_PROBE")} tone="text-blocked" />
                <Stat label="Rate limit" value={c("RATE_LIMITED")} />
                <Stat label="Geçersiz token" value={c("API_TOKEN_INVALID")} />
                <Stat label="Açık alarm" value={s.openAlerts.length} tone={s.openAlerts.length ? "text-danger" : "text-done"} />
              </>
            ) : (
              Array.from({ length: 6 }).map((_, i) => <Skeleton key={i} className="h-[92px]" />)
            )}
          </div>
          <div className="grid gap-6 xl:grid-cols-3">
            <Card className="xl:col-span-2">
              <CardHeader title="Olay zaman çizelgesi" subtitle="INFO dışındaki olaylar" />
              <div className="h-64 p-4">
                {!timeline ? <Skeleton className="h-full" /> : !timeline.length ? <EmptyState title="Bu pencerede olay yok" /> : (
                  <ResponsiveContainer width="100%" height="100%">
                    <AreaChart data={timeline}>
                      <CartesianGrid strokeDasharray="3 3" stroke="var(--border)" vertical={false} />
                      <XAxis dataKey="t" tick={{ fill: "var(--text-muted)", fontSize: 11 }} />
                      <YAxis tick={{ fill: "var(--text-muted)", fontSize: 11 }} allowDecimals={false} />
                      <Tooltip contentStyle={{ background: "var(--surface)", border: "1px solid var(--border)", borderRadius: 8, color: "var(--text)" }} />
                      <Area dataKey="Olay" stroke="var(--danger)" fill="var(--danger-soft)" strokeWidth={2} />
                    </AreaChart>
                  </ResponsiveContainer>
                )}
              </div>
            </Card>
            <Card>
              <CardHeader title="Açık alarmlar" />
              {!s ? <Skeleton className="m-5 h-40" /> : !s.openAlerts.length ? (
                <EmptyState title="Alarm yok" description="Kurallar: kaba kuvvet, IDOR taraması, token kötüye kullanımı, toplu dışa aktarım, yetki yükseltme." />
              ) : (
                <ul className="divide-y divide-border">
                  {s.openAlerts.map((a, i) => (
                    <li key={i} className="flex gap-3 px-5 py-3">
                      <ShieldAlert className={cx("mt-0.5 size-5 shrink-0", a.severity === "HIGH" ? "text-danger" : "text-blocked")} aria-hidden />
                      <div className="min-w-0">
                        <p className="text-sm font-medium text-text">{RULE_LABEL[a.rule] ?? a.rule}</p>
                        <p className="text-xs text-muted">{a.sample ? `${a.sample} · ` : ""}{a.count} olay · ilk {fmtRelative(a.firstSeen)}</p>
                      </div>
                      <Badge className={cx("ml-auto self-start", sevTone[a.severity])}>{a.severity}</Badge>
                    </li>
                  ))}
                </ul>
              )}
              {s && s.topSources.length > 0 && (
                <div className="border-t border-border px-5 py-3">
                  <p className="mb-2 text-xs font-medium text-muted uppercase">En çok tetikleyen kaynaklar</p>
                  <ul className="space-y-1 text-sm">
                    {s.topSources.slice(0, 5).map((src) => (
                      <li key={src.ip} className="flex justify-between"><code className="text-text">{src.ip}</code><span className="tabular text-muted">{src.count}</span></li>
                    ))}
                  </ul>
                </div>
              )}
            </Card>
          </div>
        </>
      )}
      <Card>
        <CardHeader
          title="Olay akışı"
          subtitle="15 sn'de bir yenilenir"
          actions={
            <Select aria-label="Olay tipi" value={type} onChange={(e) => (setType(e.target.value as Schemas["SecurityEventType"] | ""), setPage(1))} className="w-56">
              <option value="">Tüm tipler</option>
              {EVENT_TYPES.map((t) => <option key={t} value={t}>{t}</option>)}
            </Select>
          }
        />
        {events.error ? <ErrorState message={errorMessage(events.error)} /> : !events.data ? <Skeleton className="m-5 h-40" /> : !events.data.items.length ? <EmptyState title="Olay yok" /> : (
          <>
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead className="bg-surface-2 text-left text-xs text-muted uppercase">
                  <tr><th scope="col" className="px-5 py-2 font-medium">Zaman</th><th scope="col" className="px-3 py-2 font-medium">Tip</th><th scope="col" className="px-3 py-2 font-medium">Önem</th><th scope="col" className="px-3 py-2 font-medium">Kullanıcı</th><th scope="col" className="px-3 py-2 font-medium">IP</th><th scope="col" className="px-3 py-2 font-medium">Request ID</th></tr>
                </thead>
                <tbody>
                  {events.data.items.map((e) => (
                    <tr key={e.id} className="border-t border-border">
                      <td className="px-5 py-2 whitespace-nowrap text-muted">{fmtDateTime(e.occurredAt)}</td>
                      <td className="px-3 py-2 font-mono text-xs text-text">{e.type}</td>
                      <td className="px-3 py-2"><Badge className={sevTone[e.severity]}>{e.severity}</Badge></td>
                      <td className="px-3 py-2 text-text">{e.user?.fullName ?? "—"}</td>
                      <td className="px-3 py-2 font-mono text-xs text-muted">{e.ip ?? "—"}</td>
                      <td className="px-3 py-2 font-mono text-xs text-muted">{e.requestId?.slice(0, 12) ?? "—"}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
            <Pagination page={page} pageSize={25} total={events.data.total} onPage={setPage} />
          </>
        )}
      </Card>
    </div>
  );
}

function PerformanceTab() {
  const [window, setWindow] = useState<"15m" | "1h" | "24h">("1h");
  const m = useMetricsSummary(window);
  if (m.error) return <Card><ErrorState message={errorMessage(m.error)} /></Card>;
  const d = m.data;
  const total = d?.endpoints.reduce((a, e) => a + e.requests, 0) ?? 0;
  const errors = d?.endpoints.reduce((a, e) => a + e.requests * e.errorRate, 0) ?? 0;
  const p95 = d?.endpoints.length ? Math.max(...d.endpoints.map((e) => e.p95Ms)) : 0;
  return (
    <div className="space-y-6">
      <div className="flex justify-end">
        <Select aria-label="Zaman penceresi" value={window} onChange={(e) => setWindow(e.target.value as typeof window)} className="w-40">
          <option value="15m">Son 15 dakika</option>
          <option value="1h">Son 1 saat</option>
          <option value="24h">Son 24 saat</option>
        </Select>
      </div>
      <div className="grid grid-cols-2 gap-4 md:grid-cols-4">
        {d ? (
          <>
            <Stat label="Çalışma süresi" value={`${Math.floor((d.uptimeSeconds ?? 0) / 3600)} sa ${Math.floor(((d.uptimeSeconds ?? 0) % 3600) / 60)} dk`} tone="text-done" />
            <Stat label="İstek" value={total} />
            <Stat label="5xx hata oranı" value={`%${total ? ((errors / total) * 100).toFixed(2) : "0"}`} tone={errors ? "text-danger" : "text-done"} />
            <Stat label="En yüksek p95" value={`${p95.toFixed(0)} ms`} tone={p95 > 300 ? "text-blocked" : "text-text"} hint="hedef < 300 ms" />
          </>
        ) : (
          Array.from({ length: 4 }).map((_, i) => <Skeleton key={i} className="h-[92px]" />)
        )}
      </div>
      <div className="grid gap-6 xl:grid-cols-3">
        <Card className="xl:col-span-2">
          <CardHeader title="Uç nokta performansı (RED)" subtitle="İstek sayısı, hata oranı, gecikme" />
          {!d ? <Skeleton className="m-5 h-40" /> : !d.endpoints.length ? <EmptyState title="Bu pencerede istek yok" /> : (
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead className="bg-surface-2 text-left text-xs text-muted uppercase">
                  <tr><th scope="col" className="px-5 py-2 font-medium">Uç nokta</th>{["İstek", "Hata", "p50", "p95", "p99"].map((h) => <th key={h} scope="col" className="px-3 py-2 text-right font-medium">{h}</th>)}</tr>
                </thead>
                <tbody>
                  {d.endpoints.slice(0, 20).map((e) => (
                    <tr key={`${e.method} ${e.route}`} className="border-t border-border">
                      <td className="px-5 py-2 font-mono text-xs text-text"><span className="text-muted">{e.method}</span> {e.route.replace("/api/v1", "")}</td>
                      <td className="tabular px-3 text-right">{e.requests}</td>
                      <td className={cx("tabular px-3 text-right", e.errorRate > 0 ? "text-danger" : "text-muted")}>%{(e.errorRate * 100).toFixed(1)}</td>
                      <td className="tabular px-3 text-right text-muted">{e.p50Ms}</td>
                      <td className={cx("tabular px-3 text-right", e.p95Ms > 300 ? "text-blocked" : "text-text")}>{e.p95Ms}</td>
                      <td className="tabular px-3 text-right text-muted">{e.p99Ms}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </Card>
        <Card>
          <CardHeader title="Arka plan işleri" subtitle="Worker" />
          {!d ? <Skeleton className="m-5 h-40" /> : (
            <ul className="divide-y divide-border">
              {d.jobs.map((j) => (
                <li key={j.name} className="flex items-center gap-3 px-5 py-3">
                  <Activity className={cx("size-4", j.lastStatus === "SUCCESS" ? "text-done" : j.lastStatus === "FAILED" ? "text-danger" : "text-muted")} aria-hidden />
                  <div className="min-w-0 flex-1">
                    <p className="font-mono text-xs text-text">{j.name}</p>
                    <p className="text-xs text-muted">{j.lastRunAt ? `${fmtRelative(j.lastRunAt)} · ${j.lastDurationMs ?? 0} ms` : "Henüz çalışmadı"}</p>
                  </div>
                  <Badge className={j.lastStatus === "SUCCESS" ? "bg-success-soft text-done" : j.lastStatus === "FAILED" ? "bg-danger-soft text-danger" : "bg-surface-2 text-muted"}>{j.lastStatus}</Badge>
                </li>
              ))}
            </ul>
          )}
        </Card>
      </div>
    </div>
  );
}

function AuditTab() {
  const [page, setPage] = useState(1);
  const [action, setAction] = useState("");
  const logs = useAuditLogs({ page, action: action || undefined });
  return (
    <Card>
      <CardHeader
        title="Denetim kaydı"
        subtitle="Değiştirilemez (append-only) — kim, ne, ne zaman, nereden"
        actions={
          <>
            <Select aria-label="İşlem" value={action} onChange={(e) => (setAction(e.target.value), setPage(1))} className="w-56">
              <option value="">Tüm işlemler</option>
              {["auth.login", "task.create", "task.update", "task.transition", "task.delete", "user.role_change", "user.update", "project.create", "report.export", "api_token.create", "participation.decide"].map((a) => (
                <option key={a} value={a}>{a}</option>
              ))}
            </Select>
            <a href={csvUrl("/audit-logs", { action: action || undefined })} className="inline-flex h-10 items-center gap-2 rounded-lg border border-border bg-surface px-3 text-sm text-text hover:bg-surface-2">
              <Download className="size-4" />CSV
            </a>
          </>
        }
      />
      {logs.error ? <ErrorState message={errorMessage(logs.error)} /> : !logs.data ? <Skeleton className="m-5 h-40" /> : !logs.data.items.length ? <EmptyState title="Kayıt yok" /> : (
        <>
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead className="bg-surface-2 text-left text-xs text-muted uppercase">
                <tr><th scope="col" className="px-5 py-2 font-medium">Zaman</th><th scope="col" className="px-3 py-2 font-medium">Aktör</th><th scope="col" className="px-3 py-2 font-medium">İşlem</th><th scope="col" className="px-3 py-2 font-medium">Varlık</th><th scope="col" className="px-3 py-2 font-medium">Değişiklik</th><th scope="col" className="px-3 py-2 font-medium">IP</th></tr>
              </thead>
              <tbody>
                {logs.data.items.map((l) => (
                  <tr key={l.id} className="border-t border-border align-top">
                    <td className="px-5 py-2 whitespace-nowrap text-muted">{fmtDateTime(l.occurredAt)}</td>
                    <td className="px-3 py-2 text-text">{l.actor?.fullName ?? l.actorType}{l.actorType === "API_TOKEN" && <Badge className="ml-1 bg-primary-soft text-primary">API</Badge>}</td>
                    <td className="px-3 py-2 font-mono text-xs text-text">{l.action}</td>
                    <td className="px-3 py-2 text-xs text-muted">{l.entityType ?? "—"}</td>
                    <td className="max-w-xs px-3 py-2 font-mono text-xs break-all text-muted">{l.changes ? JSON.stringify(l.changes).slice(0, 140) : "—"}</td>
                    <td className="px-3 py-2 font-mono text-xs text-muted">{l.ip ?? "—"}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          <Pagination page={page} pageSize={25} total={logs.data.total} onPage={setPage} />
        </>
      )}
    </Card>
  );
}

/** Oturum bağlamı. Arayüz rol bazlı gizler; yetkiyi her zaman API zorlar. */
import { createContext, useContext, type ReactNode } from "react";
import { Navigate, useLocation } from "react-router";
import { ApiError, useMe, type Schemas } from "./api/hooks";
import { ErrorState, Spinner } from "./components/ui";

type Ctx = {
  session: Schemas["Session"];
  user: Schemas["User"];
  can: {
    manage: boolean; // yönetici veya direktör (yazma)
    direct: boolean; // direktör
    readOnly: boolean; // denetmen
    observe: boolean; // güvenlik/observability ekranları
    audit: boolean;
  };
  managesTeam: (teamId?: string | null) => boolean;
};

const AuthCtx = createContext<Ctx | null>(null);

export function useAuth(): Ctx {
  const ctx = useContext(AuthCtx);
  if (!ctx) throw new Error("useAuth AuthGate içinde kullanılmalı");
  return ctx;
}

export function AuthGate({ children }: { children: ReactNode }) {
  const me = useMe();
  const location = useLocation();
  if (me.isPending) return <Spinner label="Oturum kontrol ediliyor…" />;
  if (me.error instanceof ApiError && me.error.status === 401) {
    return <Navigate to="/login" replace state={{ from: location.pathname }} />;
  }
  if (me.error) return <ErrorState message="Sunucuya ulaşılamıyor." onRetry={() => void me.refetch()} />;
  if (!me.data) return <Navigate to="/login" replace />;
  const session = me.data;
  const role = session.user.role;
  const managed = new Set(session.managedTeamIds ?? []);
  const value: Ctx = {
    session,
    user: session.user,
    can: {
      manage: role === "MANAGER" || role === "DIRECTOR",
      direct: role === "DIRECTOR",
      readOnly: role === "AUDITOR",
      observe: role === "DIRECTOR" || role === "AUDITOR",
      audit: role !== "EMPLOYEE",
    },
    managesTeam: (teamId) => role === "DIRECTOR" || (!!teamId && managed.has(teamId)),
  };
  return <AuthCtx.Provider value={value}>{children}</AuthCtx.Provider>;
}

import {
  Award,
  Bell,
  BriefcaseBusiness,
  CalendarDays,
  ChartColumn,
  KeyRound,
  LayoutDashboard,
  ListChecks,
  LogOut,
  Megaphone,
  Menu,
  Moon,
  ShieldAlert,
  Sun,
  Users,
} from "lucide-react";
import { useEffect, useRef, useState, type ReactNode } from "react";
import { Link, NavLink, Outlet, useNavigate } from "react-router";
import { useLogout, useMarkRead, useNotifications, useUnreadCount } from "../api/hooks";
import { useAuth } from "../auth";
import { roleLabel } from "../i18n/tr";
import { fmtRelative } from "../lib/format";
import { Avatar, Button, cx, EmptyState, Spinner } from "./ui";

type NavItem = { to: string; label: string; icon: ReactNode; show?: boolean };

function useTheme(): [string, () => void] {
  const [theme, setTheme] = useState(() => localStorage.getItem("cth-theme") ?? "light");
  useEffect(() => {
    document.documentElement.dataset.theme = theme;
    localStorage.setItem("cth-theme", theme);
  }, [theme]);
  return [theme, () => setTheme((t) => (t === "dark" ? "light" : "dark"))];
}

function NotificationBell() {
  const [open, setOpen] = useState(false);
  const unread = useUnreadCount();
  const list = useNotifications();
  const mark = useMarkRead();
  const navigate = useNavigate();
  const box = useRef<HTMLDivElement>(null);
  useEffect(() => {
    if (!open) return;
    const close = (e: MouseEvent) => !box.current?.contains(e.target as Node) && setOpen(false);
    const esc = (e: KeyboardEvent) => e.key === "Escape" && setOpen(false);
    document.addEventListener("mousedown", close);
    document.addEventListener("keydown", esc);
    return () => {
      document.removeEventListener("mousedown", close);
      document.removeEventListener("keydown", esc);
    };
  }, [open]);
  const count = unread.data?.count ?? 0;
  return (
    <div className="relative" ref={box}>
      <button
        onClick={() => setOpen((o) => !o)}
        className="relative rounded-lg p-2 text-muted hover:bg-surface-2 hover:text-text"
        aria-label={`Bildirimler${count ? `, ${count} okunmamış` : ""}`}
        aria-expanded={open}
      >
        <Bell className="size-5" />
        {count > 0 && (
          <span className="tabular absolute -top-0.5 -right-0.5 min-w-5 rounded-full bg-danger px-1 text-center text-[10px] leading-5 font-semibold text-on-primary">
            {count > 99 ? "99+" : count}
          </span>
        )}
      </button>
      {open && (
        <div className="absolute right-0 z-30 mt-2 w-[min(24rem,calc(100vw-2rem))] rounded-xl border border-border bg-surface shadow-xl">
          <div className="flex items-center justify-between border-b border-border px-4 py-3">
            <p className="font-semibold">Bildirimler</p>
            <Button variant="ghost" size="sm" disabled={!count} onClick={() => mark.mutate(undefined)}>
              Tümünü okundu yap
            </Button>
          </div>
          <div className="max-h-96 overflow-y-auto">
            {list.isPending ? (
              <Spinner />
            ) : !list.data?.items.length ? (
              <EmptyState title="Bildirim yok" />
            ) : (
              <ul>
                {list.data.items.map((n) => (
                  <li key={n.id}>
                    <button
                      className={cx(
                        "flex w-full gap-3 border-b border-border px-4 py-3 text-left hover:bg-surface-2",
                        !n.readAt && "bg-primary-soft/40",
                      )}
                      onClick={() => {
                        if (!n.readAt) mark.mutate(n.id);
                        setOpen(false);
                        if (n.entityType === "task" && n.entityId) navigate(`/tasks?open=${n.entityId}`);
                        else if (n.entityType === "event") navigate("/events");
                        else if (n.entityType === "announcement") navigate("/announcements");
                      }}
                    >
                      <span className={cx("mt-1.5 size-2 shrink-0 rounded-full", n.readAt ? "bg-transparent" : "bg-primary")} />
                      <span className="min-w-0">
                        <span className="block text-sm text-text">{n.title}</span>
                        <span className="text-xs text-muted">{fmtRelative(n.createdAt)}</span>
                      </span>
                    </button>
                  </li>
                ))}
              </ul>
            )}
          </div>
        </div>
      )}
    </div>
  );
}

export function Layout() {
  const { user, can } = useAuth();
  const [theme, toggleTheme] = useTheme();
  const [mobileOpen, setMobileOpen] = useState(false);
  const logout = useLogout();
  const navigate = useNavigate();
  const nav: NavItem[] = [
    { to: "/", label: "Dashboard", icon: <LayoutDashboard className="size-4" /> },
    { to: "/tasks", label: "Task'lar", icon: <ListChecks className="size-4" /> },
    { to: "/projects", label: "Projeler", icon: <BriefcaseBusiness className="size-4" /> },
    { to: "/events", label: "Etkinlikler", icon: <CalendarDays className="size-4" /> },
    { to: "/competencies", label: "Yetkinlikler", icon: <Award className="size-4" /> },
    { to: "/reports", label: "Raporlar", icon: <ChartColumn className="size-4" /> },
    { to: "/announcements", label: "Duyurular", icon: <Megaphone className="size-4" /> },
    { to: "/security", label: "Güvenlik & İzleme", icon: <ShieldAlert className="size-4" />, show: can.observe || can.audit },
    { to: "/admin", label: "Kullanıcı & Ekip", icon: <Users className="size-4" />, show: can.direct },
    { to: "/settings/tokens", label: "API & MCP", icon: <KeyRound className="size-4" /> },
  ];
  const sidebar = (
    <nav aria-label="Ana menü" className="flex h-full flex-col bg-sidebar text-sidebar-text">
      <Link to="/" className="flex items-center gap-2 px-5 py-5 text-white" onClick={() => setMobileOpen(false)}>
        <img src="/favicon.svg" alt="" className="size-8" />
        <span className="text-[15px] font-semibold tracking-tight">Cyber Task Hub</span>
      </Link>
      <ul className="flex-1 space-y-0.5 px-3">
        {nav
          .filter((n) => n.show !== false)
          .map((n) => (
            <li key={n.to}>
              <NavLink
                to={n.to}
                end={n.to === "/"}
                onClick={() => setMobileOpen(false)}
                className={({ isActive }) =>
                  cx(
                    "flex items-center gap-3 rounded-lg px-3 py-2 text-sm transition-colors",
                    isActive ? "bg-sidebar-active font-medium text-white" : "hover:bg-sidebar-active hover:text-white",
                  )
                }
              >
                {n.icon}
                {n.label}
              </NavLink>
            </li>
          ))}
      </ul>
      <div className="border-t border-white/10 px-5 py-4 text-xs">
        <p className="text-white">{user.fullName}</p>
        <p>
          {roleLabel[user.role]}
          {user.teamName ? ` · ${user.teamName}` : ""}
        </p>
      </div>
    </nav>
  );
  return (
    <div className="flex h-full">
      <aside className="hidden w-64 shrink-0 lg:block">{sidebar}</aside>
      {mobileOpen && (
        <div className="fixed inset-0 z-40 lg:hidden">
          <div className="absolute inset-0 bg-black/50" onClick={() => setMobileOpen(false)} aria-hidden />
          <aside className="relative h-full w-64">{sidebar}</aside>
        </div>
      )}
      <div className="flex min-w-0 flex-1 flex-col">
        <header className="flex h-16 shrink-0 items-center justify-between gap-3 border-b border-border bg-surface px-4 lg:px-8">
          <button className="rounded-lg p-2 text-muted hover:bg-surface-2 lg:hidden" onClick={() => setMobileOpen(true)} aria-label="Menüyü aç">
            <Menu className="size-5" />
          </button>
          <div className="hidden text-sm text-muted sm:block">
            {can.readOnly && <span className="rounded-full bg-warning-soft px-2.5 py-1 text-xs font-medium text-blocked">Salt okunur denetmen görünümü</span>}
          </div>
          <div className="ml-auto flex items-center gap-1">
            <button onClick={toggleTheme} className="rounded-lg p-2 text-muted hover:bg-surface-2 hover:text-text" aria-label={theme === "dark" ? "Açık temaya geç" : "Koyu temaya geç"}>
              {theme === "dark" ? <Sun className="size-5" /> : <Moon className="size-5" />}
            </button>
            <NotificationBell />
            <div className="mx-2 hidden h-6 w-px bg-border sm:block" />
            <Avatar name={user.fullName} />
            <Button
              variant="ghost"
              size="sm"
              aria-label="Çıkış yap"
              onClick={() => logout.mutate(undefined, { onSettled: () => navigate("/login") })}
            >
              <LogOut className="size-4" />
              <span className="hidden sm:inline">Çıkış</span>
            </Button>
          </div>
        </header>
        <main className="min-w-0 flex-1 overflow-y-auto px-4 py-6 lg:px-8">
          <Outlet />
        </main>
      </div>
    </div>
  );
}

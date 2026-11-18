import {
  Award,
  Bell,
  BriefcaseBusiness,
  CalendarCheck,
  CalendarDays,
  ChartNoAxesColumn,
  ChevronDown,
  Code,
  House,
  LogOut,
  Megaphone,
  Menu,
  Moon,
  Search,
  Shield,
  ShieldAlert,
  Sun,
  Users,
} from "lucide-react";
import { useEffect, useRef, useState, type ReactNode } from "react";
import { Link, NavLink, Outlet, useLocation, useNavigate } from "react-router";
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

const PAGE_TITLE: Array<[RegExp, string]> = [
  [/^\/$/, "Genel Bakış"],
  [/^\/tasks/, "Görevler"],
  [/^\/projects/, "Projeler"],
  [/^\/events/, "Etkinlikler"],
  [/^\/competencies/, "Yetkinlikler"],
  [/^\/reports/, "Raporlar"],
  [/^\/announcements/, "Duyurular"],
  [/^\/security/, "Güvenlik & İzleme"],
  [/^\/admin/, "Organizasyon"],
  [/^\/settings\/tokens/, "API & MCP"],
];

function useDismiss(open: boolean, setOpen: (v: boolean) => void) {
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
  }, [open, setOpen]);
  return box;
}

function UserMenu({ theme, toggleTheme }: { theme: string; toggleTheme: () => void }) {
  const { user } = useAuth();
  const [open, setOpen] = useState(false);
  const box = useDismiss(open, setOpen);
  const logout = useLogout();
  const navigate = useNavigate();
  return (
    <div className="relative" ref={box}>
      <button
        onClick={() => setOpen((o) => !o)}
        className="flex items-center gap-1.5 rounded-full p-1 pr-2 hover:bg-surface-2"
        aria-label="Kullanıcı menüsü"
        aria-expanded={open}
      >
        <Avatar name={user.fullName} size="lg" />
        <ChevronDown className="size-4 text-muted" aria-hidden />
      </button>
      {open && (
        <div className="absolute right-0 z-30 mt-2 w-60 overflow-hidden rounded-xl border border-border bg-surface shadow-xl">
          <div className="border-b border-border px-4 py-3">
            <p className="text-sm font-semibold text-text">{user.fullName}</p>
            <p className="text-xs text-muted">
              {roleLabel[user.role]}
              {user.teamName ? ` · ${user.teamName}` : ""}
            </p>
          </div>
          <button onClick={toggleTheme} className="flex w-full items-center gap-2 px-4 py-2.5 text-left text-sm hover:bg-surface-2">
            {theme === "dark" ? <Sun className="size-4" /> : <Moon className="size-4" />}
            {theme === "dark" ? "Açık tema" : "Koyu tema"}
          </button>
          <button
            onClick={() => logout.mutate(undefined, { onSettled: () => navigate("/login") })}
            className="flex w-full items-center gap-2 px-4 py-2.5 text-left text-sm text-danger hover:bg-surface-2"
          >
            <LogOut className="size-4" /> Çıkış yap
          </button>
        </div>
      )}
    </div>
  );
}

function GlobalSearch() {
  const navigate = useNavigate();
  const [q, setQ] = useState("");
  return (
    <form
      role="search"
      className="relative hidden w-full max-w-sm md:block"
      onSubmit={(e) => {
        e.preventDefault();
        if (q.trim()) navigate(`/tasks?q=${encodeURIComponent(q.trim())}`);
      }}
    >
      <Search className="pointer-events-none absolute top-1/2 left-3.5 size-4 -translate-y-1/2 text-muted" aria-hidden />
      <input
        value={q}
        onChange={(e) => setQ(e.target.value)}
        maxLength={100}
        placeholder="Görev ara…"
        aria-label="Görev ara"
        className="h-11 w-full rounded-xl border border-border bg-surface-2/60 pr-3 pl-10 text-sm text-text placeholder:text-muted focus:border-primary focus:bg-surface focus:outline-none"
      />
    </form>
  );
}

export function Layout() {
  const { user, can } = useAuth();
  const [theme, toggleTheme] = useTheme();
  const [mobileOpen, setMobileOpen] = useState(false);
  const { pathname } = useLocation();
  const title = PAGE_TITLE.find(([re]) => re.test(pathname))?.[1] ?? "";
  const nav: NavItem[] = [
    { to: "/", label: "Genel Bakış", icon: <House className="size-5" /> },
    { to: "/tasks", label: "Görevler", icon: <CalendarCheck className="size-5" /> },
    { to: "/projects", label: "Projeler", icon: <BriefcaseBusiness className="size-5" /> },
    { to: "/events", label: "Etkinlikler", icon: <CalendarDays className="size-5" /> },
    { to: "/competencies", label: "Yetkinlikler", icon: <Award className="size-5" /> },
    { to: "/reports", label: "Raporlar", icon: <ChartNoAxesColumn className="size-5" /> },
    { to: "/announcements", label: "Duyurular", icon: <Megaphone className="size-5" /> },
    { to: "/security", label: "Güvenlik & İzleme", icon: <ShieldAlert className="size-5" />, show: can.observe || can.audit },
    { to: "/admin", label: "Organizasyon", icon: <Users className="size-5" />, show: can.direct },
  ];
  const link = (n: NavItem, small = false) => (
    <NavLink
      to={n.to}
      end={n.to === "/"}
      onClick={() => setMobileOpen(false)}
      className={({ isActive }) =>
        cx(
          "flex items-center gap-3.5 rounded-xl px-4 transition-colors",
          small ? "py-2 text-sm" : "py-2.5 text-[15px]",
          isActive ? "bg-accent font-semibold text-on-accent shadow-sm" : "hover:bg-sidebar-active hover:text-white",
        )
      }
    >
      {n.icon}
      {n.label}
    </NavLink>
  );
  const sidebar = (
    <nav aria-label="Ana menü" className="flex h-full flex-col bg-sidebar text-sidebar-text">
      <Link to="/" className="flex items-center gap-3 px-6 pt-7 pb-8 text-white" onClick={() => setMobileOpen(false)}>
        <Shield className="size-11 shrink-0 fill-sidebar stroke-accent" strokeWidth={2.4} aria-hidden />
        <span className="text-xl leading-tight font-semibold tracking-tight">
          Cyber
          <br />
          Task Hub
        </span>
      </Link>
      <ul className="flex-1 space-y-1.5 overflow-y-auto px-3">
        {nav
          .filter((n) => n.show !== false)
          .map((n) => (
            <li key={n.to}>{link(n)}</li>
          ))}
      </ul>
      <div className="mx-4 border-t border-white/15 py-3">
        {link({ to: "/settings/tokens", label: "API & MCP", icon: <Code className="size-5" /> }, true)}
      </div>
      <div className="mx-4 flex items-center gap-3 border-t border-white/15 py-4">
        <Avatar name={user.fullName} size="lg" />
        <div className="min-w-0 text-sm">
          <p className="truncate font-medium text-white">{user.fullName}</p>
          <p className="truncate text-xs">{roleLabel[user.role]}</p>
        </div>
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
        <header className="flex h-16 shrink-0 items-center gap-4 border-b border-border bg-surface px-4 lg:px-8">
          <button className="rounded-lg p-2 text-muted hover:bg-surface-2 lg:hidden" onClick={() => setMobileOpen(true)} aria-label="Menüyü aç">
            <Menu className="size-5" />
          </button>
          <nav aria-label="Konum" className="hidden min-w-0 items-center gap-2 text-sm sm:flex">
            <span className="text-muted">Çalışma Alanı</span>
            <span className="text-muted" aria-hidden>/</span>
            <span className="truncate font-semibold text-text" aria-current="page">{title}</span>
          </nav>
          {can.readOnly && <span className="hidden rounded-full bg-warning-soft px-2.5 py-1 text-xs font-medium text-blocked xl:inline">Salt okunur denetmen görünümü</span>}
          <div className="ml-auto flex flex-1 items-center justify-end gap-2">
            <GlobalSearch />
            <NotificationBell />
            <UserMenu theme={theme} toggleTheme={toggleTheme} />
          </div>
        </header>
        <main className="min-w-0 flex-1 overflow-y-auto px-4 py-6 lg:px-8">
          <Outlet />
        </main>
      </div>
    </div>
  );
}

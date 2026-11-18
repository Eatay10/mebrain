/** Yeniden kullanılabilir UI bileşenleri — renkler sadece token'lardan (R-TS-05). */
import { AlertTriangle, Inbox, Loader2, X } from "lucide-react";
import {
  createContext,
  forwardRef,
  useCallback,
  useContext,
  useEffect,
  useId,
  useRef,
  useState,
  type ButtonHTMLAttributes,
  type InputHTMLAttributes,
  type ReactNode,
  type SelectHTMLAttributes,
  type TextareaHTMLAttributes,
} from "react";
import type { Schemas } from "../api/hooks";
import { priorityLabel, statusLabel } from "../i18n/tr";
import { initials } from "../lib/format";

export function cx(...parts: Array<string | false | null | undefined>): string {
  return parts.filter(Boolean).join(" ");
}

// ---------------------------------------------------------------- Button
type Variant = "primary" | "accent" | "secondary" | "ghost" | "danger";
const variants: Record<Variant, string> = {
  primary: "bg-primary text-on-primary hover:bg-primary-hover",
  accent: "bg-accent text-on-accent font-semibold hover:bg-accent-hover",
  secondary: "bg-surface text-text border border-border hover:bg-surface-2",
  ghost: "text-muted hover:text-text hover:bg-surface-2",
  danger: "bg-danger text-on-primary hover:opacity-90",
};

export const Button = forwardRef<
  HTMLButtonElement,
  ButtonHTMLAttributes<HTMLButtonElement> & { variant?: Variant; size?: "sm" | "md"; loading?: boolean }
>(function Button({ variant = "primary", size = "md", loading, className, children, disabled, ...rest }, ref) {
  return (
    <button
      ref={ref}
      className={cx(
        "inline-flex items-center justify-center gap-2 rounded-lg font-medium transition-colors disabled:cursor-not-allowed disabled:opacity-50",
        size === "sm" ? "h-8 px-3 text-sm" : "h-10 px-4 text-sm",
        variants[variant],
        className,
      )}
      disabled={disabled || loading}
      {...rest}
    >
      {loading && <Loader2 className="size-4 animate-spin" aria-hidden />}
      {children}
    </button>
  );
});

// ---------------------------------------------------------------- Form controls
const control =
  "w-full rounded-lg border border-border bg-surface px-3 text-sm text-text placeholder:text-muted focus:border-primary focus:outline-none focus:ring-2 focus:ring-primary/30 disabled:opacity-60";

export function Field({ label, error, hint, children, htmlFor }: {
  label: string;
  error?: string;
  hint?: string;
  children: ReactNode;
  htmlFor: string;
}) {
  return (
    <div className="space-y-1.5">
      <label htmlFor={htmlFor} className="block text-sm font-medium text-text">
        {label}
      </label>
      {children}
      {error ? (
        <p role="alert" className="text-xs text-danger">
          {error}
        </p>
      ) : hint ? (
        <p className="text-xs text-muted">{hint}</p>
      ) : null}
    </div>
  );
}

export const Input = forwardRef<HTMLInputElement, InputHTMLAttributes<HTMLInputElement>>(function Input(
  { className, ...rest },
  ref,
) {
  return <input ref={ref} className={cx(control, "h-10", className)} {...rest} />;
});

export const Select = forwardRef<HTMLSelectElement, SelectHTMLAttributes<HTMLSelectElement>>(function Select(
  { className, children, ...rest },
  ref,
) {
  return (
    <select ref={ref} className={cx(control, "h-10 pr-8", className)} {...rest}>
      {children}
    </select>
  );
});

export const Textarea = forwardRef<HTMLTextAreaElement, TextareaHTMLAttributes<HTMLTextAreaElement>>(
  function Textarea({ className, ...rest }, ref) {
    return <textarea ref={ref} className={cx(control, "min-h-24 py-2", className)} {...rest} />;
  },
);

// ---------------------------------------------------------------- Layout primitives
export function Card({ className, children }: { className?: string; children: ReactNode }) {
  return <section className={cx("rounded-xl border border-border bg-surface shadow-card", className)}>{children}</section>;
}

export function CardHeader({ title, subtitle, actions }: { title: string; subtitle?: string; actions?: ReactNode }) {
  return (
    <div className="flex flex-wrap items-start justify-between gap-3 border-b border-border px-5 py-4">
      <div>
        <h2 className="text-base font-semibold text-text">{title}</h2>
        {subtitle && <p className="mt-0.5 text-sm text-muted">{subtitle}</p>}
      </div>
      {actions && <div className="flex flex-wrap items-center gap-2">{actions}</div>}
    </div>
  );
}

export function PageHeader({ title, subtitle, actions }: { title: string; subtitle?: string; actions?: ReactNode }) {
  return (
    <header className="mb-6 flex flex-wrap items-end justify-between gap-4">
      <div>
        <h1 className="text-2xl font-semibold tracking-tight text-text">{title}</h1>
        {subtitle && <p className="mt-1 text-sm text-muted">{subtitle}</p>}
      </div>
      {actions && <div className="flex flex-wrap items-center gap-2">{actions}</div>}
    </header>
  );
}

// ---------------------------------------------------------------- States
export function Spinner({ label = "Yükleniyor…" }: { label?: string }) {
  return (
    <div role="status" className="flex items-center justify-center gap-2 py-12 text-sm text-muted">
      <Loader2 className="size-5 animate-spin" aria-hidden />
      {label}
    </div>
  );
}

export function Skeleton({ className }: { className?: string }) {
  return <div className={cx("animate-pulse rounded-lg bg-surface-2", className)} aria-hidden />;
}

export function EmptyState({ title, description, action }: { title: string; description?: string; action?: ReactNode }) {
  return (
    <div className="flex flex-col items-center justify-center gap-2 px-6 py-12 text-center">
      <Inbox className="size-8 text-muted" aria-hidden />
      <p className="font-medium text-text">{title}</p>
      {description && <p className="max-w-sm text-sm text-muted">{description}</p>}
      {action && <div className="mt-2">{action}</div>}
    </div>
  );
}

export function ErrorState({ message, onRetry }: { message: string; onRetry?: () => void }) {
  return (
    <div role="alert" className="flex flex-col items-center justify-center gap-2 px-6 py-12 text-center">
      <AlertTriangle className="size-8 text-danger" aria-hidden />
      <p className="font-medium text-text">Veriler yüklenemedi</p>
      <p className="max-w-md text-sm text-muted">{message}</p>
      {onRetry && (
        <Button variant="secondary" size="sm" onClick={onRetry} className="mt-2">
          Tekrar dene
        </Button>
      )}
    </div>
  );
}

// ---------------------------------------------------------------- Badges
const statusStyle: Record<Schemas["TaskStatus"], string> = {
  TODO: "bg-surface-2 text-todo",
  IN_PROGRESS: "bg-info-soft text-progress",
  BLOCKED: "bg-warning-soft text-blocked",
  DONE: "bg-success-soft text-done",
};
const priorityStyle: Record<Schemas["TaskPriority"], string> = {
  LOW: "text-muted",
  MEDIUM: "text-progress",
  HIGH: "text-blocked",
  CRITICAL: "text-danger font-semibold",
};

export function Badge({ className, children }: { className?: string; children: ReactNode }) {
  return (
    <span className={cx("inline-flex items-center gap-1 whitespace-nowrap rounded-full px-2 py-0.5 text-xs font-medium", className)}>
      {children}
    </span>
  );
}

export function StatusBadge({ status }: { status: Schemas["TaskStatus"] }) {
  return (
    <Badge className={statusStyle[status]}>
      <span className="size-1.5 rounded-full bg-current" aria-hidden />
      {statusLabel[status]}
    </Badge>
  );
}

export function PriorityBadge({ priority }: { priority: Schemas["TaskPriority"] }) {
  return <span className={cx("text-xs", priorityStyle[priority])}>{priorityLabel[priority]}</span>;
}

export function Avatar({ name, size = "md" }: { name: string; size?: "sm" | "md" | "lg" }) {
  return (
    <span
      aria-hidden
      className={cx(
        "inline-flex shrink-0 items-center justify-center rounded-full bg-primary-soft font-semibold text-primary",
        size === "sm" ? "size-6 text-[10px]" : size === "lg" ? "size-10 text-sm" : "size-8 text-xs",
      )}
    >
      {initials(name)}
    </span>
  );
}

/** Grafik açıklamaları: renk kutusu seri renginde, metin okunur kalsın diye nötr. */
export const legendText = (value: string) => <span style={{ color: "var(--text-muted)" }}>{value}</span>;

export function ProgressBar({ counts }: { counts: Schemas["StatusCounts"] }) {
  const total = counts.total || 1;
  const parts: Array<[number, string, string]> = [
    [counts.done, "bg-chart-done", "Tamamlandı"],
    [counts.inProgress, "bg-chart-progress", "Devam ediyor"],
    [counts.blocked, "bg-chart-blocked", "Bloklu"],
    [counts.todo, "bg-chart-todo", "Başlanmadı"],
  ];
  return (
    <div
      className="flex h-2 w-full overflow-hidden rounded-full bg-surface-2"
      role="img"
      aria-label={parts.map(([n, , l]) => `${l}: ${n}`).join(", ")}
    >
      {parts.map(([n, cls, l]) => (n ? <span key={l} className={cls} style={{ width: `${(n / total) * 100}%` }} /> : null))}
    </div>
  );
}

// ---------------------------------------------------------------- Pagination
export function Pagination({ page, pageSize, total, onPage }: {
  page: number;
  pageSize: number;
  total: number;
  onPage: (p: number) => void;
}) {
  const pages = Math.max(1, Math.ceil(total / pageSize));
  return (
    <nav className="flex items-center justify-between gap-3 border-t border-border px-5 py-3 text-sm text-muted" aria-label="Sayfalama">
      <span className="tabular">
        {total === 0 ? 0 : (page - 1) * pageSize + 1}–{Math.min(page * pageSize, total)} / {total}
      </span>
      <div className="flex gap-2">
        <Button variant="secondary" size="sm" disabled={page <= 1} onClick={() => onPage(page - 1)}>
          Önceki
        </Button>
        <Button variant="secondary" size="sm" disabled={page >= pages} onClick={() => onPage(page + 1)}>
          Sonraki
        </Button>
      </div>
    </nav>
  );
}

// ---------------------------------------------------------------- Modal (erişilebilir dialog)
export function Modal({ open, onClose, title, children, footer, wide }: {
  open: boolean;
  onClose: () => void;
  title: string;
  children: ReactNode;
  footer?: ReactNode;
  wide?: boolean;
}) {
  const ref = useRef<HTMLDialogElement>(null);
  const titleId = useId();
  useEffect(() => {
    const d = ref.current;
    if (!d) return;
    if (open && !d.open) d.showModal();
    if (!open && d.open) d.close();
  }, [open]);
  return (
    <dialog
      ref={ref}
      aria-labelledby={titleId}
      onClose={onClose}
      onCancel={onClose}
      className={cx(
        "m-auto w-[calc(100%-2rem)] rounded-xl border border-border bg-surface p-0 text-text shadow-2xl backdrop:bg-black/50",
        wide ? "max-w-3xl" : "max-w-lg",
      )}
    >
      {open && (
        <div className="flex max-h-[85vh] flex-col">
          <div className="flex items-center justify-between border-b border-border px-5 py-4">
            <h2 id={titleId} className="text-base font-semibold">
              {title}
            </h2>
            <button onClick={onClose} className="rounded-md p-1 text-muted hover:bg-surface-2 hover:text-text" aria-label="Kapat">
              <X className="size-5" />
            </button>
          </div>
          <div className="overflow-y-auto px-5 py-4">{children}</div>
          {footer && <div className="flex justify-end gap-2 border-t border-border px-5 py-3">{footer}</div>}
        </div>
      )}
    </dialog>
  );
}

// ---------------------------------------------------------------- Toast
type Toast = { id: number; kind: "success" | "error"; text: string };
const ToastCtx = createContext<(kind: Toast["kind"], text: string) => void>(() => undefined);

export function ToastProvider({ children }: { children: ReactNode }) {
  const [items, setItems] = useState<Toast[]>([]);
  const push = useCallback((kind: Toast["kind"], text: string) => {
    const id = Date.now() + Math.random();
    setItems((xs) => [...xs, { id, kind, text }]);
    setTimeout(() => setItems((xs) => xs.filter((x) => x.id !== id)), 4500);
  }, []);
  return (
    <ToastCtx.Provider value={push}>
      {children}
      <div aria-live="polite" className="pointer-events-none fixed right-4 bottom-4 z-50 flex w-80 flex-col gap-2">
        {items.map((t) => (
          <div
            key={t.id}
            role={t.kind === "error" ? "alert" : "status"}
            className={cx(
              "pointer-events-auto rounded-lg border px-4 py-3 text-sm shadow-lg",
              t.kind === "error" ? "border-danger/40 bg-danger-soft text-danger" : "border-done/40 bg-success-soft text-done",
            )}
          >
            {t.text}
          </div>
        ))}
      </div>
    </ToastCtx.Provider>
  );
}

export function useToast() {
  return useContext(ToastCtx);
}

// ---------------------------------------------------------------- Tabs
export function Tabs<T extends string>({ value, onChange, items }: {
  value: T;
  onChange: (v: T) => void;
  items: Array<{ value: T; label: string }>;
}) {
  return (
    <div role="tablist" className="inline-flex rounded-lg border border-border bg-surface-2 p-0.5">
      {items.map((it) => (
        <button
          key={it.value}
          role="tab"
          aria-selected={value === it.value}
          onClick={() => onChange(it.value)}
          className={cx(
            "rounded-md px-3 py-1.5 text-sm font-medium transition-colors",
            value === it.value ? "bg-surface text-text shadow-card" : "text-muted hover:text-text",
          )}
        >
          {it.label}
        </button>
      ))}
    </div>
  );
}

export function Stat({ label, value, tone, hint }: { label: string; value: ReactNode; tone?: string; hint?: string }) {
  return (
    <div className="rounded-xl border border-border bg-surface p-4 shadow-card">
      <p className="text-xs font-medium tracking-wide text-muted uppercase">{label}</p>
      <p className={cx("tabular mt-1 text-2xl font-semibold", tone ?? "text-text")}>{value}</p>
      {hint && <p className="mt-1 text-xs text-muted">{hint}</p>}
    </div>
  );
}

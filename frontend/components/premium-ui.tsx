"use client";

import {
  ReactNode,
  useEffect,
  useState,
} from "react";

type Tone = "default" | "success" | "warning" | "danger" | "info";

const toneClasses: Record<Tone, string> = {
  default:
    "border-[var(--border)] bg-[var(--surface)] text-[var(--foreground)]",
  success:
    "border-emerald-200 bg-emerald-50 text-emerald-800 dark:border-emerald-900 dark:bg-emerald-950/40 dark:text-emerald-300",
  warning:
    "border-amber-200 bg-amber-50 text-amber-800 dark:border-amber-900 dark:bg-amber-950/40 dark:text-amber-300",
  danger:
    "border-red-200 bg-red-50 text-red-800 dark:border-red-900 dark:bg-red-950/40 dark:text-red-300",
  info:
    "border-blue-200 bg-blue-50 text-blue-800 dark:border-blue-900 dark:bg-blue-950/40 dark:text-blue-300",
};

export function PremiumCard({
  children,
  className = "",
  interactive = false,
}: {
  children: ReactNode;
  className?: string;
  interactive?: boolean;
}) {
  return (
    <section
      className={[
        "rounded-2xl border border-[var(--border)] bg-[var(--surface)] p-5 shadow-sm",
        "transition-all duration-200",
        interactive
          ? "cursor-pointer hover:-translate-y-0.5 hover:shadow-md active:translate-y-0"
          : "",
        className,
      ].join(" ")}
    >
      {children}
    </section>
  );
}

export function DataCard({
  label,
  value,
  detail,
  trend,
  tone = "default",
}: {
  label: string;
  value: string;
  detail?: string;
  trend?: string;
  tone?: Tone;
}) {
  return (
    <PremiumCard>
      <div className="flex items-start justify-between gap-4">
        <div className="min-w-0">
          <p className="text-sm font-medium text-[var(--muted)]">{label}</p>
          <p className="mt-2 truncate text-2xl font-bold tracking-tight text-[var(--foreground)]">
            {value}
          </p>
          {detail && (
            <p className="mt-1 text-xs text-[var(--muted)]">{detail}</p>
          )}
        </div>

        {trend && (
          <span
            className={`rounded-full border px-2.5 py-1 text-xs font-semibold ${toneClasses[tone]}`}
          >
            {trend}
          </span>
        )}
      </div>
    </PremiumCard>
  );
}

export function StatusBadge({
  children,
  tone = "default",
}: {
  children: ReactNode;
  tone?: Tone;
}) {
  return (
    <span
      className={`inline-flex items-center gap-1.5 rounded-full border px-2.5 py-1 text-xs font-semibold ${toneClasses[tone]}`}
    >
      <span className="h-1.5 w-1.5 rounded-full bg-current opacity-80" />
      {children}
    </span>
  );
}

export function ProgressBar({
  value,
  label,
  showValue = true,
}: {
  value: number;
  label?: string;
  showValue?: boolean;
}) {
  const safeValue = Math.min(100, Math.max(0, value));

  return (
    <div className="space-y-2">
      {(label || showValue) && (
        <div className="flex items-center justify-between gap-3 text-xs">
          {label ? (
            <span className="font-medium text-[var(--foreground)]">
              {label}
            </span>
          ) : (
            <span />
          )}
          {showValue && (
            <span className="font-semibold text-[var(--muted)]">
              {safeValue}%
            </span>
          )}
        </div>
      )}

      <div className="h-2 overflow-hidden rounded-full bg-black/5 dark:bg-white/10">
        <div
          className="h-full rounded-full bg-[var(--accent)] transition-all duration-500"
          style={{ width: `${safeValue}%` }}
        />
      </div>
    </div>
  );
}

export function Toggle({
  checked,
  onChange,
  label,
  description,
}: {
  checked: boolean;
  onChange: (value: boolean) => void;
  label?: string;
  description?: string;
}) {
  return (
    <div className="flex items-center justify-between gap-4">
      <div className="min-w-0">
        {label && (
          <p className="text-sm font-semibold text-[var(--foreground)]">
            {label}
          </p>
        )}
        {description && (
          <p className="mt-1 text-xs text-[var(--muted)]">{description}</p>
        )}
      </div>

      <button
        type="button"
        role="switch"
        aria-checked={checked}
        onClick={() => onChange(!checked)}
        className={[
          "relative h-7 w-12 shrink-0 rounded-full border transition",
          checked
            ? "border-[var(--accent)] bg-[var(--accent)]"
            : "border-[var(--border)] bg-black/10 dark:bg-white/10",
        ].join(" ")}
      >
        <span
          className={[
            "absolute top-1 h-5 w-5 rounded-full bg-white shadow-sm transition",
            checked ? "left-6" : "left-1",
          ].join(" ")}
        />
      </button>
    </div>
  );
}

export function EmptyState({
  title,
  description,
  action,
}: {
  title: string;
  description: string;
  action?: ReactNode;
}) {
  return (
    <PremiumCard className="flex min-h-56 flex-col items-center justify-center text-center">
      <div className="mb-4 flex h-12 w-12 items-center justify-center rounded-2xl bg-[var(--accent-soft)] text-xl text-[var(--accent)]">
        +
      </div>
      <h3 className="text-base font-bold text-[var(--foreground)]">
        {title}
      </h3>
      <p className="mt-2 max-w-md text-sm leading-6 text-[var(--muted)]">
        {description}
      </p>
      {action && <div className="mt-5">{action}</div>}
    </PremiumCard>
  );
}

export function CompactDataRow({
  title,
  subtitle,
  value,
  badge,
}: {
  title: string;
  subtitle?: string;
  value?: string;
  badge?: ReactNode;
}) {
  return (
    <div className="flex items-center justify-between gap-4 border-b border-[var(--border)] py-3 last:border-b-0">
      <div className="min-w-0">
        <p className="truncate text-sm font-semibold text-[var(--foreground)]">
          {title}
        </p>
        {subtitle && (
          <p className="mt-0.5 truncate text-xs text-[var(--muted)]">
            {subtitle}
          </p>
        )}
      </div>

      <div className="flex shrink-0 items-center gap-3">
        {badge}
        {value && (
          <span className="text-sm font-semibold text-[var(--foreground)]">
            {value}
          </span>
        )}
      </div>
    </div>
  );
}

export function Accordion({
  title,
  children,
  defaultOpen = false,
}: {
  title: string;
  children: ReactNode;
  defaultOpen?: boolean;
}) {
  const [open, setOpen] = useState(defaultOpen);

  return (
    <div className="overflow-hidden rounded-2xl border border-[var(--border)] bg-[var(--surface)]">
      <button
        type="button"
        onClick={() => setOpen(!open)}
        aria-expanded={open}
        className="flex w-full items-center justify-between gap-4 p-4 text-left"
      >
        <span className="text-sm font-semibold text-[var(--foreground)]">
          {title}
        </span>
        <span className="text-lg text-[var(--muted)]">
          {open ? "−" : "+"}
        </span>
      </button>

      {open && (
        <div className="border-t border-[var(--border)] px-4 pb-4 pt-3 text-sm leading-6 text-[var(--muted)]">
          {children}
        </div>
      )}
    </div>
  );
}

export function Modal({
  open,
  title,
  description,
  children,
  onClose,
  confirmLabel = "Confirm",
  onConfirm,
}: {
  open: boolean;
  title: string;
  description?: string;
  children?: ReactNode;
  onClose: () => void;
  confirmLabel?: string;
  onConfirm?: () => void;
}) {
  useEffect(() => {
    if (!open) return;

    const handleKey = (event: KeyboardEvent) => {
      if (event.key === "Escape") onClose();
    };

    document.addEventListener("keydown", handleKey);

    return () => document.removeEventListener("keydown", handleKey);
  }, [open, onClose]);

  if (!open) return null;

  return (
    <div className="fixed inset-0 z-[120] flex items-end justify-center bg-black/50 p-4 backdrop-blur-sm sm:items-center">
      <div
        role="dialog"
        aria-modal="true"
        className="max-h-[calc(100dvh-2rem)] w-full max-w-lg overflow-y-auto rounded-3xl border border-[var(--border)] bg-[var(--surface)] p-6 shadow-2xl"
      >
        <div className="flex items-start justify-between gap-4">
          <div>
            <h2 className="text-lg font-bold text-[var(--foreground)]">
              {title}
            </h2>
            {description && (
              <p className="mt-1 text-sm leading-6 text-[var(--muted)]">
                {description}
              </p>
            )}
          </div>

          <button
            type="button"
            onClick={onClose}
            aria-label="Close"
            className="rounded-xl px-2 py-1 text-xl text-[var(--muted)] hover:bg-black/5 dark:hover:bg-white/10"
          >
            ×
          </button>
        </div>

        {children && <div className="mt-5">{children}</div>}

        {onConfirm && (
          <div className="mt-6 flex flex-col-reverse gap-2 sm:flex-row sm:justify-end">
            <button
              type="button"
              onClick={onClose}
              className="rounded-xl border border-[var(--border)] px-4 py-2.5 text-sm font-semibold text-[var(--foreground)]"
            >
              Cancel
            </button>
            <button
              type="button"
              onClick={onConfirm}
              className="rounded-xl bg-[var(--accent)] px-4 py-2.5 text-sm font-semibold text-white"
            >
              {confirmLabel}
            </button>
          </div>
        )}
      </div>
    </div>
  );
}

export function ProfileCard({
  name,
  subtitle,
  initials,
  action,
}: {
  name: string;
  subtitle?: string;
  initials: string;
  action?: ReactNode;
}) {
  return (
    <PremiumCard>
      <div className="flex items-center gap-4">
        <div className="flex h-12 w-12 shrink-0 items-center justify-center rounded-full bg-[var(--accent)] text-sm font-bold text-white">
          {initials.slice(0, 2).toUpperCase()}
        </div>

        <div className="min-w-0 flex-1">
          <p className="truncate text-sm font-bold text-[var(--foreground)]">
            {name}
          </p>
          {subtitle && (
            <p className="mt-1 truncate text-xs text-[var(--muted)]">
              {subtitle}
            </p>
          )}
        </div>

        {action}
      </div>
    </PremiumCard>
  );
}

export function ThemeToggle() {
  const [dark, setDark] = useState(false);

  useEffect(() => {
    const saved = localStorage.getItem("gsos_theme");
    const prefersDark = window.matchMedia(
      "(prefers-color-scheme: dark)",
    ).matches;

    const enabled = saved === "dark" || (!saved && prefersDark);

    document.documentElement.classList.toggle("dark", enabled);
    setDark(enabled);
  }, []);

  function toggle() {
    const next = !dark;
    document.documentElement.classList.toggle("dark", next);
    localStorage.setItem("gsos_theme", next ? "dark" : "light");
    setDark(next);
  }

  return (
    <button
      type="button"
      onClick={toggle}
      aria-label={dark ? "Switch to light mode" : "Switch to dark mode"}
      className="rounded-xl border border-[var(--border)] bg-[var(--surface)] px-3 py-2 text-sm font-semibold text-[var(--foreground)] transition hover:bg-black/5 dark:hover:bg-white/10"
    >
      {dark ? "☀ Light" : "☾ Dark"}
    </button>
  );
}

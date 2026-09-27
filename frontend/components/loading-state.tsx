"use client";

type LoadingStateProps = {
  label?: string;
};

export function LoadingState({
  label = "Loading…",
}: LoadingStateProps) {
  return (
    <div
      role="status"
      aria-live="polite"
      className="rounded-2xl border border-[var(--border)] bg-[var(--surface)] p-5 text-sm text-[var(--muted)]"
    >
      {label}
    </div>
  );
}

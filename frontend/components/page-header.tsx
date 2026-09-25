import { Icon } from "./icon";

export function PageHeader({
  eyebrow,
  title,
  description,
  action,
}: {
  eyebrow: string;
  title: string;
  description: string;
  action?: { label: string; icon?: "plus" | "scan" };
}) {
  return (
    <div className="mb-7 flex flex-col gap-5 sm:flex-row sm:items-end sm:justify-between">
      <div>
        <p className="mb-2 text-[11px] font-semibold uppercase tracking-[0.16em] text-[var(--accent)]">
          {eyebrow}
        </p>
        <h1 className="text-2xl font-semibold tracking-[-0.03em] sm:text-3xl">{title}</h1>
        <p className="mt-2 max-w-2xl text-sm leading-6 text-[var(--muted)]">{description}</p>
      </div>

      {action && (
        <button className="flex h-11 items-center justify-center gap-2 rounded-xl bg-[var(--foreground)] px-4 text-sm font-semibold text-white hover:opacity-90">
          <Icon name={action.icon ?? "plus"} size={17} />
          {action.label}
        </button>
      )}
    </div>
  );
}

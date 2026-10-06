"use client";

import { useRouter } from "next/navigation";
import { Icon, type IconName } from "./icon";

type PageHeaderProps = {
  eyebrow?: string;
  title: string;
  description?: string;
  back?: boolean;
  backLabel?: string;
  backHref?: string;
  action?: {
    label: string;
    icon?: "plus" | "scan";
    onClick?: () => void;
  };
};

export function PageHeader({
  eyebrow,
  title,
  description,
  back = false,
  backLabel = "Back",
  backHref,
  action,
}: PageHeaderProps) {
  const router = useRouter();

  const handleBack = () => {
    if (backHref) {
      router.push(backHref);
      return;
    }

    router.back();
  };

  return (
    <div className="mb-7 flex flex-col gap-4 border-b border-[var(--border)] pb-6 sm:flex-row sm:items-end sm:justify-between">
      <div className="min-w-0">
        {back && (
          <button
            type="button"
            onClick={handleBack}
            className="mb-3 inline-flex items-center gap-2 text-sm font-medium text-neutral-500 transition hover:text-neutral-950"
          >
            <Icon name="arrow-left" size={16} />
            {backLabel}
          </button>
        )}

        {eyebrow && (
          <div className="mb-2 text-[10px] font-bold uppercase tracking-[0.18em] text-[var(--accent)]">
            {eyebrow}
          </div>
        )}

        <h1 className="gsos-page-title text-[1.75rem] font-semibold sm:text-3xl">
          {title}
        </h1>

        {description && (
          <p className="mt-2 max-w-2xl text-sm leading-6 text-[var(--muted)]">
            {description}
          </p>
        )}
      </div>

      {action && (
        <button
          type="button"
          onClick={action.onClick}
          className="inline-flex min-h-12 w-full shrink-0 items-center justify-center gap-2 rounded-xl bg-[var(--accent-strong)] px-5 text-sm font-semibold text-white shadow-sm transition hover:bg-[var(--accent)] active:scale-[.98] focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-[var(--accent)] sm:w-auto"
        >
          {action.icon && (
            <Icon name={action.icon as IconName} size={16} />
          )}
          {action.label}
        </button>
      )}
    </div>
  );
}

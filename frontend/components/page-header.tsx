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
    <div className="mb-6 flex flex-col gap-4 sm:flex-row sm:items-end sm:justify-between">
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
          <div className="mb-1 text-[10px] font-semibold uppercase tracking-[0.18em] text-neutral-400">
            {eyebrow}
          </div>
        )}

        <h1 className="text-2xl font-semibold tracking-[-0.03em] text-neutral-950 sm:text-3xl">
          {title}
        </h1>

        {description && (
          <p className="mt-1 max-w-2xl text-sm leading-6 text-neutral-500">
            {description}
          </p>
        )}
      </div>

      {action && (
        <button
          type="button"
          onClick={action.onClick}
          className="inline-flex h-10 shrink-0 items-center justify-center gap-2 rounded-xl bg-neutral-900 px-4 text-sm font-semibold text-white transition hover:bg-neutral-800"
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

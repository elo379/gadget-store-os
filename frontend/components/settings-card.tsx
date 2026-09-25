import Link from "next/link";

export function SettingsCard({
  eyebrow,
  title,
  description,
  href,
}: {
  eyebrow: string;
  title: string;
  description: string;
  href: string;
}) {
  return (
    <Link
      href={href}
      className="group rounded-2xl border border-[var(--border)] bg-white p-6 transition hover:-translate-y-0.5 hover:border-neutral-300 hover:shadow-sm"
    >
      <p className="text-[10px] font-semibold uppercase tracking-[0.16em] text-[var(--accent)]">
        {eyebrow}
      </p>

      <h2 className="mt-3 text-base font-semibold tracking-[-0.02em]">
        {title}
      </h2>

      <p className="mt-2 text-sm leading-6 text-[var(--muted)]">
        {description}
      </p>

      <p className="mt-5 text-sm font-semibold text-neutral-900 transition group-hover:translate-x-0.5">
        Manage →
      </p>
    </Link>
  );
}

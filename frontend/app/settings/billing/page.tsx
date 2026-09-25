import { AppShell } from "@/components/app-shell";

export default function BillingSettingsPage() {
  return (
    <AppShell>
      <div className="mb-7">
        <p className="text-[11px] font-semibold uppercase tracking-[0.16em] text-[var(--accent)]">
          SaaS
        </p>

        <h1 className="mt-2 text-2xl font-semibold tracking-[-0.03em]">
          Subscription
        </h1>

        <p className="mt-2 text-sm text-[var(--muted)]">
          Subscription and billing controls for the future SaaS platform.
        </p>
      </div>

      <section className="max-w-2xl rounded-2xl border border-[var(--border)] bg-white p-6 sm:p-8">
        <div className="flex items-start justify-between gap-5">
          <div>
            <p className="text-xs font-semibold text-[var(--muted)]">
              Current plan
            </p>

            <h2 className="mt-2 text-xl font-semibold">
              Pilot workspace
            </h2>
          </div>

          <span className="rounded-full bg-[var(--accent-soft)] px-3 py-1 text-xs font-semibold text-[var(--accent)]">
            Active
          </span>
        </div>

        <div className="mt-7 grid gap-4 sm:grid-cols-3">
          <div className="rounded-xl bg-[#fafaf8] p-4">
            <p className="text-[10px] uppercase tracking-[0.12em] text-neutral-400">
              Organizations
            </p>
            <p className="mt-2 text-lg font-semibold">1</p>
          </div>

          <div className="rounded-xl bg-[#fafaf8] p-4">
            <p className="text-[10px] uppercase tracking-[0.12em] text-neutral-400">
              Members
            </p>
            <p className="mt-2 text-lg font-semibold">3</p>
          </div>

          <div className="rounded-xl bg-[#fafaf8] p-4">
            <p className="text-[10px] uppercase tracking-[0.12em] text-neutral-400">
              Billing
            </p>
            <p className="mt-2 text-lg font-semibold">Not active</p>
          </div>
        </div>

        <div className="mt-7 border-t border-[var(--border)] pt-6">
          <p className="text-xs leading-5 text-[var(--muted)]">
            Payment provider integration and subscription mutations will be
            enabled after the SaaS billing contract is finalized.
          </p>
        </div>
      </section>
    </AppShell>
  );
}

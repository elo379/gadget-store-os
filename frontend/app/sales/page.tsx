import Link from "next/link";
import { AppShell } from "@/components/app-shell";
import { PageHeader } from "@/components/page-header";

export default function SalesPage() {
  return (
    <AppShell>
      <PageHeader
        eyebrow="Point of sale"
        title="Sales"
        description="Process transactions quickly and monitor today's selling activity."
      />

      <div className="grid gap-5 lg:grid-cols-[1.4fr_0.8fr]">
        <section className="rounded-2xl border border-[var(--border)] bg-white p-6">
          <p className="text-xs font-semibold text-[var(--muted)]">Today's activity</p>
          <div className="mt-6 grid gap-6 sm:grid-cols-3">
            <div>
              <p className="text-xs text-[var(--muted)]">Transactions</p>
              <p className="mt-2 text-2xl font-semibold">24</p>
            </div>
            <div>
              <p className="text-xs text-[var(--muted)]">Revenue</p>
              <p className="mt-2 text-2xl font-semibold">₦1.24m</p>
            </div>
            <div>
              <p className="text-xs text-[var(--muted)]">Gross profit</p>
              <p className="mt-2 text-2xl font-semibold">₦318k</p>
            </div>
          </div>
        </section>

        <Link
          href="/sales/pos"
          className="rounded-2xl bg-neutral-900 p-6 text-white transition hover:bg-neutral-800"
        >
          <p className="text-[10px] font-semibold uppercase tracking-[0.16em] text-neutral-400">
            Point of sale
          </p>
          <p className="mt-4 text-2xl font-semibold tracking-[-0.03em]">
            Open POS
          </p>
          <p className="mt-2 text-sm text-neutral-400">
            Scan products and build a customer order.
          </p>
          <p className="mt-8 text-sm font-semibold">Start checkout →</p>
        </Link>
      </div>
    </AppShell>
  );
}

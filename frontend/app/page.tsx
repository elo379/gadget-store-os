import { AppShell } from "@/components/app-shell";

export default function DashboardPage() {
  return (
    <AppShell>
      <div>
        <p className="text-[11px] font-semibold uppercase tracking-[0.16em] text-[var(--accent)]">
          Store overview
        </p>

        <h1 className="mt-2 text-2xl font-semibold tracking-[-0.03em] sm:text-3xl">
          Dashboard
        </h1>

        <p className="mt-2 text-sm text-[var(--muted)]">
          Your store at a glance.
        </p>

        <div className="mt-7 grid gap-4 md:grid-cols-2 xl:grid-cols-4">
          {[
            ["Today's sales", "₦1,245,000"],
            ["Gross profit", "₦318,400"],
            ["Inventory units", "142"],
            ["Open orders", "18"],
          ].map(([label, value]) => (
            <section
              key={label}
              className="rounded-2xl border border-[var(--border)] bg-white p-5"
            >
              <p className="text-xs font-semibold text-[var(--muted)]">
                {label}
              </p>

              <p className="mt-4 text-2xl font-semibold tracking-[-0.03em]">
                {value}
              </p>
            </section>
          ))}
        </div>

        <div className="mt-5 rounded-2xl border border-[var(--border)] bg-white p-6">
          <p className="text-sm font-semibold">
            Store workspace ready
          </p>

          <p className="mt-2 text-sm leading-6 text-[var(--muted)]">
            GSOS is connected to its authenticated application layer.
          </p>
        </div>
      </div>
    </AppShell>
  );
}

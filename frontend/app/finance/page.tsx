import { AppShell } from "@/components/app-shell";
import { PageHeader } from "@/components/page-header";

export default function FinancePage() {
  return (
    <AppShell>
      <PageHeader
        eyebrow="Financial control"
        title="Finance"
        description="Revenue, cost of goods, gross profit, expenses and operating performance."
      />

      <div className="grid gap-4 md:grid-cols-3">
        {[
          ["Revenue", "₦1,245,000"],
          ["COGS", "₦926,600"],
          ["Gross profit", "₦318,400"],
        ].map(([label, value]) => (
          <section key={label} className="rounded-2xl border border-[var(--border)] bg-white p-6">
            <p className="text-xs font-semibold text-[var(--muted)]">{label}</p>
            <p className="mt-4 text-2xl font-semibold">{value}</p>
          </section>
        ))}
      </div>
    </AppShell>
  );
}

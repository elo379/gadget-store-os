import { AppShell } from "@/components/app-shell";
import { PageHeader } from "@/components/page-header";

export default function ReportsPage() {
  return (
    <AppShell>
      <PageHeader
        eyebrow="Business intelligence"
        title="Reports"
        description="Sales, inventory, products, staff performance and expenses."
      />

      <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-3">
        {[
          "Sales report",
          "Product performance",
          "Staff sales",
          "Inventory report",
          "Expense report",
          "Customer report",
        ].map((name) => (
          <section key={name} className="rounded-2xl border border-[var(--border)] bg-white p-6">
            <h2 className="text-sm font-semibold">{name}</h2>
            <p className="mt-2 text-xs leading-5 text-[var(--muted)]">
              Open this report and choose the required period.
            </p>
            <button className="mt-5 text-sm font-semibold text-[var(--accent)]">
              View report →
            </button>
          </section>
        ))}
      </div>
    </AppShell>
  );
}

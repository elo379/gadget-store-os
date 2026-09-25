import { AppShell } from "@/components/app-shell";
import { DataTable } from "@/components/data-table";
import { PageHeader } from "@/components/page-header";

export default function InventoryPage() {
  return (
    <AppShell>
      <PageHeader eyebrow="Stock control" title="Inventory"
        description="Monitor quantities, locations, reservations and stock health."
        action={{ label: "Stock movement" }} />

      <div className="mb-6 grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
        {[
          ["Total units", "142", "Across active inventory"],
          ["Low stock", "7", "Needs attention"],
          ["Reserved", "12", "Allocated to orders"],
          ["Locations", "1", "Active store location"],
        ].map(([label, value, note]) => (
          <div key={label} className="rounded-2xl border border-[var(--border)] bg-white p-5">
            <p className="text-xs font-semibold">{label}</p>
            <p className="mt-1 text-[11px] text-[var(--muted)]">{note}</p>
            <p className="mt-5 text-2xl font-semibold tracking-[-0.03em]">{value}</p>
          </div>
        ))}
      </div>

      <DataTable
        columns={[
          { label: "Product", key: "product" },
          { label: "Location", key: "location" },
          { label: "Quantity", key: "quantity" },
          { label: "Reserved", key: "reserved" },
          { label: "Status", key: "status" },
        ]}
        rows={[
          { product: "iPhone 15 Pro 256GB", location: "Main Store", quantity: "5", reserved: "1", status: "Healthy" },
          { product: "Samsung Galaxy S24", location: "Main Store", quantity: "3", reserved: "0", status: "Low stock" },
          { product: "USB-C Fast Charger 25W", location: "Main Store", quantity: "42", reserved: "4", status: "Healthy" },
        ]}
      />
    </AppShell>
  );
}

import { AppShell } from "@/components/app-shell";
import { DataTable } from "@/components/data-table";
import { PageHeader } from "@/components/page-header";

export default function ProductsPage() {
  return (
    <AppShell>
      <PageHeader eyebrow="Catalog" title="Products"
        description="Manage the store catalogue, SKUs, product types and active selling inventory."
        action={{ label: "Add product" }} />

      <div className="mb-5 flex flex-wrap gap-2">
        {["All products", "Smartphones", "Accessories", "Serialized"].map((item, i) => (
          <button key={item}
            className={`rounded-xl px-4 py-2 text-xs font-semibold ${
              i === 0 ? "bg-neutral-900 text-white" : "border border-[var(--border)] bg-white text-neutral-600"
            }`}>
            {item}
          </button>
        ))}
      </div>

      <DataTable
        columns={[
          { label: "Product", key: "product" },
          { label: "SKU", key: "sku" },
          { label: "Category", key: "category" },
          { label: "Type", key: "type" },
          { label: "Status", key: "status" },
        ]}
        rows={[
          { product: "iPhone 15 Pro", sku: "IP15P-256-BLK", category: "Smartphones", type: "Serialized", status: "Active" },
          { product: "Samsung Galaxy S24", sku: "S24-256-GRY", category: "Smartphones", type: "Serialized", status: "Active" },
          { product: "USB-C Fast Charger 25W", sku: "CHR25-USBC", category: "Accessories", type: "Stock", status: "Active" },
        ]}
      />
    </AppShell>
  );
}

import { AppShell } from "@/components/app-shell";
import { DataTable } from "@/components/data-table";
import { PageHeader } from "@/components/page-header";

export default function PurchasingPage() {
  return (
    <AppShell>
      <PageHeader
        eyebrow="Supply chain"
        title="Purchasing"
        description="Manage suppliers, purchase orders and receiving."
        action={{ label: "New purchase" }}
      />

      <DataTable
        columns={[
          { label: "Reference", key: "ref" },
          { label: "Supplier", key: "supplier" },
          { label: "Items", key: "items" },
          { label: "Total", key: "total" },
          { label: "Status", key: "status" },
        ]}
        rows={[
          { ref: "PO-1042", supplier: "Pilot Supplier", items: "8", total: "₦4,820,000", status: "Received" },
          { ref: "PO-1043", supplier: "Pilot Supplier", items: "12", total: "₦680,000", status: "Pending" },
        ]}
      />
    </AppShell>
  );
}

import { AppShell } from "@/components/app-shell";
import { DataTable } from "@/components/data-table";
import { PageHeader } from "@/components/page-header";

export default function CustomersPage() {
  return (
    <AppShell>
      <PageHeader
        eyebrow="Customer records"
        title="Customers"
        description="Profiles, purchase history, returns and warranty records."
        action={{ label: "Add customer" }}
      />

      <DataTable
        columns={[
          { label: "Customer", key: "name" },
          { label: "Phone", key: "phone" },
          { label: "Purchases", key: "purchases" },
          { label: "Status", key: "status" },
        ]}
        rows={[
          { name: "Walk-in Customer", phone: "0803 000 0000", purchases: "12", status: "Active" },
          { name: "A. Johnson", phone: "0814 000 0000", purchases: "5", status: "Active" },
          { name: "C. Williams", phone: "0902 000 0000", purchases: "2", status: "Active" },
        ]}
      />
    </AppShell>
  );
}

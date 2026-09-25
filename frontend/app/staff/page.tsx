import { AppShell } from "@/components/app-shell";
import { DataTable } from "@/components/data-table";
import { PageHeader } from "@/components/page-header";

export default function StaffPage() {
  return (
    <AppShell>
      <PageHeader
        eyebrow="Team"
        title="Staff"
        description="Staff profiles, attendance and operational access."
        action={{ label: "Add staff" }}
      />

      <DataTable
        columns={[
          { label: "Staff", key: "name" },
          { label: "Role", key: "role" },
          { label: "Today", key: "today" },
          { label: "Status", key: "status" },
        ]}
        rows={[
          { name: "Store Manager", role: "Manager", today: "8h 12m", status: "Clocked in" },
          { name: "Sales Staff", role: "Sales", today: "7h 48m", status: "Clocked in" },
          { name: "Inventory Staff", role: "Inventory", today: "—", status: "Off duty" },
        ]}
      />
    </AppShell>
  );
}

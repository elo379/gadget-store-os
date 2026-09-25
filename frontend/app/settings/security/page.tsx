import { AppShell } from "@/components/app-shell";
import { DataTable } from "@/components/data-table";

export default function SecuritySettingsPage() {
  return (
    <AppShell>
      <div className="mb-7">
        <p className="text-[11px] font-semibold uppercase tracking-[0.16em] text-[var(--accent)]">
          Security
        </p>

        <h1 className="mt-2 text-2xl font-semibold tracking-[-0.03em]">
          Security & audit
        </h1>

        <p className="mt-2 text-sm text-[var(--muted)]">
          Review administrative and sensitive workspace activity.
        </p>
      </div>

      <DataTable
        columns={[
          { label: "Action", key: "action" },
          { label: "Actor", key: "actor" },
          { label: "Entity", key: "entity" },
          { label: "Time", key: "time" },
        ]}
        rows={[
          {
            action: "Signed in",
            actor: "Store Owner",
            entity: "Authentication",
            time: "Today, 09:12",
          },
          {
            action: "Inventory adjustment",
            actor: "Store Manager",
            entity: "Inventory",
            time: "Today, 10:41",
          },
          {
            action: "Role updated",
            actor: "Store Owner",
            entity: "Manager role",
            time: "Yesterday",
          },
        ]}
      />
    </AppShell>
  );
}

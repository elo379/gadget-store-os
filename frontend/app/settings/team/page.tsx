import { AppShell } from "@/components/app-shell";
import { DataTable } from "@/components/data-table";

export default function TeamSettingsPage() {
  return (
    <AppShell>
      <div className="mb-7 flex flex-col gap-4 sm:flex-row sm:items-end sm:justify-between">
        <div>
          <p className="text-[11px] font-semibold uppercase tracking-[0.16em] text-[var(--accent)]">
            Access
          </p>

          <h1 className="mt-2 text-2xl font-semibold tracking-[-0.03em]">
            Team & members
          </h1>

          <p className="mt-2 text-sm text-[var(--muted)]">
            Manage who can access this organization.
          </p>
        </div>

        <button className="h-11 rounded-xl bg-neutral-900 px-4 text-sm font-semibold text-white">
          Invite member
        </button>
      </div>

      <DataTable
        columns={[
          { label: "Member", key: "member" },
          { label: "Access", key: "access" },
          { label: "Status", key: "status" },
          { label: "Last activity", key: "activity" },
        ]}
        rows={[
          {
            member: "Store Owner",
            access: "Owner",
            status: "Active",
            activity: "Today",
          },
          {
            member: "Store Manager",
            access: "Manager",
            status: "Active",
            activity: "Today",
          },
          {
            member: "Sales Staff",
            access: "Sales",
            status: "Active",
            activity: "Yesterday",
          },
        ]}
      />
    </AppShell>
  );
}

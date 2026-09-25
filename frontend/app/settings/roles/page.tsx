import { AppShell } from "@/components/app-shell";

const roles = [
  {
    name: "Owner",
    description: "Full organization authority.",
    permissions: "All permissions",
  },
  {
    name: "Manager",
    description: "Operational management access.",
    permissions: "Configured permissions",
  },
  {
    name: "Sales",
    description: "Sales and customer workflows.",
    permissions: "Sales, customers",
  },
  {
    name: "Inventory",
    description: "Inventory and stock operations.",
    permissions: "Inventory, products",
  },
];

export default function RolesPage() {
  return (
    <AppShell>
      <div className="mb-7">
        <p className="text-[11px] font-semibold uppercase tracking-[0.16em] text-[var(--accent)]">
          Authorization
        </p>

        <h1 className="mt-2 text-2xl font-semibold tracking-[-0.03em]">
          Roles & permissions
        </h1>

        <p className="mt-2 text-sm text-[var(--muted)]">
          Roles define access while permissions define what each role can do.
        </p>
      </div>

      <div className="grid gap-4 lg:grid-cols-2">
        {roles.map((role) => (
          <section
            key={role.name}
            className="rounded-2xl border border-[var(--border)] bg-white p-6"
          >
            <div className="flex items-start justify-between gap-4">
              <div>
                <h2 className="text-base font-semibold">{role.name}</h2>
                <p className="mt-1 text-sm text-[var(--muted)]">
                  {role.description}
                </p>
              </div>

              <button className="text-sm font-semibold text-[var(--accent)]">
                Manage
              </button>
            </div>

            <div className="mt-6 rounded-xl bg-[#fafaf8] px-4 py-3">
              <p className="text-[10px] font-semibold uppercase tracking-[0.12em] text-neutral-400">
                Access
              </p>

              <p className="mt-1 text-sm">{role.permissions}</p>
            </div>
          </section>
        ))}
      </div>
    </AppShell>
  );
}

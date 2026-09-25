import { AppShell } from "@/components/app-shell";
import { PageHeader } from "@/components/page-header";

export default function SettingsPage() {
  return (
    <AppShell>
      <PageHeader
        eyebrow="Administration"
        title="Settings"
        description="Store configuration, users, roles, permissions and operational controls."
      />

      <div className="grid gap-4 md:grid-cols-2">
        {[
          ["Store profile", "Business identity and operating information."],
          ["Roles & permissions", "Control what managers and staff can access."],
          ["Locations", "Configure store and future branch locations."],
          ["Security & audit", "Review sensitive actions and security activity."],
        ].map(([title, description]) => (
          <section key={title} className="rounded-2xl border border-[var(--border)] bg-white p-6">
            <h2 className="text-sm font-semibold">{title}</h2>
            <p className="mt-2 text-xs leading-5 text-[var(--muted)]">{description}</p>
            <button className="mt-5 text-sm font-semibold text-[var(--accent)]">
              Manage →
            </button>
          </section>
        ))}
      </div>
    </AppShell>
  );
}

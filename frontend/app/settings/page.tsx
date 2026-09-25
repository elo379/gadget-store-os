import { AppShell } from "@/components/app-shell";
import { SettingsCard } from "@/components/settings-card";

export default function SettingsPage() {
  return (
    <AppShell>
      <div className="mb-8">
        <p className="text-[11px] font-semibold uppercase tracking-[0.16em] text-[var(--accent)]">
          Administration
        </p>

        <h1 className="mt-2 text-2xl font-semibold tracking-[-0.03em] sm:text-3xl">
          Settings
        </h1>

        <p className="mt-2 max-w-2xl text-sm leading-6 text-[var(--muted)]">
          Configure your organization, team access, security and future
          subscription controls.
        </p>
      </div>

      <div className="grid gap-4 md:grid-cols-2">
        <SettingsCard
          eyebrow="Organization"
          title="Store profile"
          description="Business identity, operating information and organization status."
          href="/settings/organization"
        />

        <SettingsCard
          eyebrow="Access"
          title="Team & members"
          description="Manage store users, invitations, membership and access status."
          href="/settings/team"
        />

        <SettingsCard
          eyebrow="Authorization"
          title="Roles & permissions"
          description="Configure roles and the permissions assigned to each role."
          href="/settings/roles"
        />

        <SettingsCard
          eyebrow="Security"
          title="Security & audit"
          description="Review sensitive activity and administrative actions."
          href="/settings/security"
        />

        <SettingsCard
          eyebrow="SaaS"
          title="Subscription"
          description="Subscription status, plan information and future billing controls."
          href="/settings/billing"
        />

        <section className="rounded-2xl border border-dashed border-neutral-300 bg-[#fafaf8] p-6">
          <p className="text-[10px] font-semibold uppercase tracking-[0.16em] text-neutral-400">
            Architecture
          </p>

          <h2 className="mt-3 text-base font-semibold">
            Multi-organization ready
          </h2>

          <p className="mt-2 text-sm leading-6 text-[var(--muted)]">
            GSOS keeps organization context separate from user identity so the
            platform can support multiple stores without mixing tenant data.
          </p>
        </section>
      </div>
    </AppShell>
  );
}

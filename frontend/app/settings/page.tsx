"use client";

import Link from "next/link";
import { ThemeToggle, Toggle } from "@/components/premium-ui";

import { useOrganization } from "@/components/organization-provider";

export default function SettingsPage() {
  const { organizationId, setOrganizationId } = useOrganization();

  return (
    <div className="space-y-6">
      <header>
        <p className="text-sm font-medium text-[var(--muted)]">Administration</p>
        <div className="flex flex-col gap-4 sm:flex-row sm:items-end sm:justify-between">
          <div>
            <p className="text-sm font-medium text-[var(--muted)]">
              Store configuration
            </p>
            <h1 className="text-3xl font-semibold tracking-tight">
              Settings
            </h1>
            <p className="mt-1 text-sm text-[var(--muted)]">
              Manage your workspace and experience.
            </p>
          </div>
          <ThemeToggle />
        </div>
        <p className="mt-1 text-sm text-[var(--muted)]">
          Configure the current store workspace.
        </p>
      </header>

      <section className="rounded-2xl border bg-white p-6">
        <h2 className="font-semibold">Organization</h2>

        <div className="mt-5 grid gap-5 md:grid-cols-2">
          <label className="space-y-2">
            <span className="text-sm text-[var(--muted)]">Organization ID</span>
            <input
              value={organizationId ?? ""}
              readOnly
              className="w-full rounded-xl border bg-[var(--background)] px-4 py-3"
            />
          </label>

          <label className="space-y-2">
            <span className="text-sm text-[var(--muted)]">Currency</span>
            <input
              value="NGN — Nigerian Naira"
              readOnly
              className="w-full rounded-xl border bg-[var(--background)] px-4 py-3"
            />
          </label>
        </div>

        <p className="mt-4 text-sm text-[var(--muted)]">
          Organization identity and currency are controlled by your organization administrator.
        </p>
      </section>

      <section className="grid gap-4 md:grid-cols-3">
        <Link href="/settings/team" className="rounded-2xl border border-[var(--border)] bg-[var(--surface)] p-5 shadow-sm transition hover:shadow-md">
          <h2 className="font-semibold">Team</h2>
          <p className="mt-1 text-sm text-[var(--muted)]">
            Staff access and store personnel.
          </p>
        </Link>

        <Link href="/settings/roles" className="rounded-2xl border border-[var(--border)] bg-[var(--surface)] p-5 shadow-sm transition hover:shadow-md">
          <h2 className="font-semibold">Roles</h2>
          <p className="mt-1 text-sm text-[var(--muted)]">
            Permissions and custom roles.
          </p>
        </Link>

        <Link href="/settings/security" className="rounded-2xl border border-[var(--border)] bg-[var(--surface)] p-5 shadow-sm transition hover:shadow-md">
          <h2 className="font-semibold">Security</h2>
          <p className="mt-1 text-sm text-[var(--muted)]">
            Security and account controls.
          </p>
        </Link>
      </section>
    </div>
  );
}

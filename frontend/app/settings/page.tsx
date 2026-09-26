"use client";

import { useState } from "react";
import { useOrganization } from "@/components/organization-provider";

export default function SettingsPage() {
  const { organizationId } = useOrganization();
  const [saved, setSaved] = useState(false);

  function save() {
    setSaved(true);
    window.setTimeout(() => setSaved(false), 2500);
  }

  return (
    <div className="space-y-6">
      <header>
        <p className="text-sm font-medium text-[var(--muted)]">Administration</p>
        <h1 className="text-3xl font-semibold tracking-tight">Settings</h1>
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

        <button
          onClick={save}
          className="mt-6 rounded-xl bg-black px-5 py-3 text-white"
        >
          Save settings
        </button>

        {saved && (
          <p className="mt-3 text-sm text-[var(--muted)]">
            Settings saved.
          </p>
        )}
      </section>

      <section className="grid gap-4 md:grid-cols-3">
        <a href="/settings/team" className="rounded-2xl border bg-white p-5">
          <h2 className="font-semibold">Team</h2>
          <p className="mt-1 text-sm text-[var(--muted)]">
            Staff access and store personnel.
          </p>
        </a>

        <a href="/settings/roles" className="rounded-2xl border bg-white p-5">
          <h2 className="font-semibold">Roles</h2>
          <p className="mt-1 text-sm text-[var(--muted)]">
            Permissions and custom roles.
          </p>
        </a>

        <a href="/settings/security" className="rounded-2xl border bg-white p-5">
          <h2 className="font-semibold">Security</h2>
          <p className="mt-1 text-sm text-[var(--muted)]">
            Security and account controls.
          </p>
        </a>
      </section>
    </div>
  );
}

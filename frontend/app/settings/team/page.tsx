"use client";

import { useEffect, useMemo, useState } from "react";
import {
  apiGet,
  apiPost,
  apiGetForOrganization,
} from "@/lib/api";
import { useOrganization } from "@/components/organization-provider";
import { PageHeader } from "@/components/page-header";
import { SectionCard } from "@/components/section-card";

type StoreTreeMember = {
  id: string;
  user_id: string;
  email: string;
  personnel_id: string | null;
  role_name: string;
  account_status: string;
  is_owner: boolean;
  parent_membership_id: string | null;
  created_by_membership_id: string | null;
  is_active: boolean;
};

type StoreTreeResponse = {
  organization_id: string;
  members: StoreTreeMember[];
};

type StoreTreePolicy = {
  organization_id: string;
  managers_can_create_staff: boolean;
};

type InvitationResponse = {
  id: string;
  email: string;
  role_name: string;
  token: string;
  expires_at: string | null;
};

export default function TeamSettingsPage() {
  const organization = useOrganization();

  const [tree, setTree] = useState<StoreTreeResponse | null>(null);
  const [policy, setPolicy] = useState<StoreTreePolicy | null>(null);
  const [loading, setLoading] = useState(true);
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");

  const [inviteEmail, setInviteEmail] = useState("");
  const [inviteRole, setInviteRole] = useState("manager");
  const [inviteLoading, setInviteLoading] = useState(false);
  const [invitation, setInvitation] = useState<InvitationResponse | null>(
    null,
  );

  const organizationId = organization?.organizationId;

  async function loadTeam() {
    if (!organizationId) return;

    setLoading(true);
    setError("");

    try {
      const [treeData, policyData] = await Promise.all([
        apiGet<StoreTreeResponse>(
          `/organizations/${organizationId}/store-tree`,
        ),
        apiGet<StoreTreePolicy>(
          `/organizations/${organizationId}/store-tree/policy`,
        ),
      ]);

      setTree(treeData);
      setPolicy(policyData);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unable to load team.");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    loadTeam();
  }, [organizationId]);

  const owner = useMemo(
    () => tree?.members.find((member) => member.is_owner),
    [tree],
  );

  const managers = useMemo(
    () =>
      tree?.members.filter(
        (member) => !member.is_owner && member.role_name === "manager",
      ) ?? [],
    [tree],
  );

  const staff = useMemo(
    () =>
      tree?.members.filter(
        (member) => !member.is_owner && member.role_name === "staff",
      ) ?? [],
    [tree],
  );

  async function updatePolicy(enabled: boolean) {
    if (!organizationId) return;

    setError("");
    setMessage("");

    try {
      const result = await apiPost<StoreTreePolicy>(
        `/organizations/${organizationId}/store-tree/policy`,
        { managers_can_create_staff: enabled },
      );

      setPolicy(result);
      setMessage(
        enabled
          ? "Managers can now create staff accounts."
          : "Manager staff creation has been disabled.",
      );
    } catch (err) {
      setError(
        err instanceof Error
          ? err.message
          : "Unable to update Store Tree policy.",
      );
    }
  }

  async function invitePersonnel() {
    if (!organizationId || !inviteEmail.trim()) return;

    setInviteLoading(true);
    setError("");
    setMessage("");
    setInvitation(null);

    try {
      const result = await apiPost<InvitationResponse>(
        `/organizations/${organizationId}/store-tree/invitations`,
        {
          email: inviteEmail.trim(),
          role_name: inviteRole,
        },
      );

      setInvitation(result);
      setInviteEmail("");
      setMessage(`${inviteRole} invitation created.`);
      await loadTeam();
    } catch (err) {
      setError(
        err instanceof Error
          ? err.message
          : "Unable to create invitation.",
      );
    } finally {
      setInviteLoading(false);
    }
  }

  function memberStatus(member: StoreTreeMember) {
    if (!member.is_active) return "Suspended";
    if (member.account_status === "invitation_pending") {
      return "Invitation pending";
    }
    return "Active";
  }

  if (!organizationId) {
    return (
      <main className="space-y-6">
        <PageHeader
          eyebrow="Team"
          title="Store Tree"
          description="Manage your store identity hierarchy."
        />
        <SectionCard title="Organization unavailable">
          <p className="text-sm text-[var(--muted)]">
            Select an organization before managing team access.
          </p>
        </SectionCard>
      </main>
    );
  }

  return (
    <main className="space-y-6">
      <PageHeader
        eyebrow="Team & identity"
        title="Store Tree"
        description="The authority structure behind your store workspace."
      />

      {message ? (
        <div className="rounded-xl border border-[var(--border)] bg-white px-4 py-3 text-sm">
          {message}
        </div>
      ) : null}

      {error ? (
        <div className="rounded-xl border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">
          {error}
        </div>
      ) : null}

      <section className="grid gap-4 sm:grid-cols-3">
        <MetricCard
          label="Owner"
          value={owner ? "1" : "0"}
          detail={owner?.personnel_id ?? "Root authority"}
        />
        <MetricCard
          label="Managers"
          value={String(managers.length)}
          detail="Store leadership"
        />
        <MetricCard
          label="Staff"
          value={String(staff.length)}
          detail="Operational personnel"
        />
      </section>

      <SectionCard
        title="Store hierarchy"
        description="Roles, authority and reporting relationships are kept separate."
      >
        {loading ? (
          <p className="text-sm text-[var(--muted)]">Loading Store Tree…</p>
        ) : (
          <div className="space-y-5">
            {owner ? (
              <TreeMember member={owner} level="owner" />
            ) : null}

            <div className="ml-4 border-l border-[var(--border)] pl-5 sm:ml-8">
              <div className="mb-3 text-[11px] font-semibold uppercase tracking-[0.16em] text-[var(--muted)]">
                Managers
              </div>

              <div className="space-y-3">
                {managers.length ? (
                  managers.map((member) => (
                    <TreeMember
                      key={member.id}
                      member={member}
                      level="manager"
                    />
                  ))
                ) : (
                  <p className="text-sm text-[var(--muted)]">
                    No managers have been added yet.
                  </p>
                )}
              </div>

              <div className="mt-6 border-l border-[var(--border)] pl-5 sm:ml-8">
                <div className="mb-3 text-[11px] font-semibold uppercase tracking-[0.16em] text-[var(--muted)]">
                  Staff
                </div>

                <div className="space-y-3">
                  {staff.length ? (
                    staff.map((member) => (
                      <TreeMember
                        key={member.id}
                        member={member}
                        level="staff"
                      />
                    ))
                  ) : (
                    <p className="text-sm text-[var(--muted)]">
                      No staff accounts have been added yet.
                    </p>
                  )}
                </div>
              </div>
            </div>
          </div>
        )}
      </SectionCard>

      <div className="grid gap-6 lg:grid-cols-2">
        <SectionCard
          title="Manager authority"
          description="Owner-controlled policy for the Store Tree."
        >
          <div className="flex items-center justify-between gap-4">
            <div>
              <p className="text-sm font-medium">
                Managers can create staff
              </p>
              <p className="mt-1 text-xs text-[var(--muted)]">
                Managers never create other managers by default.
              </p>
            </div>

            <button
              type="button"
              onClick={() =>
                updatePolicy(!policy?.managers_can_create_staff)
              }
              className={`rounded-full px-4 py-2 text-xs font-semibold ${
                policy?.managers_can_create_staff
                  ? "bg-black text-white"
                  : "border border-[var(--border)] bg-white text-[var(--foreground)]"
              }`}
            >
              {policy?.managers_can_create_staff ? "Enabled" : "Disabled"}
            </button>
          </div>
        </SectionCard>

        <SectionCard
          title="Invite personnel"
          description="Create a real invitation through the Store Tree."
        >
          <div className="space-y-4">
            <label className="block">
              <span className="mb-2 block text-xs font-semibold uppercase tracking-[0.12em] text-[var(--muted)]">
                Email
              </span>
              <input
                value={inviteEmail}
                onChange={(event) => setInviteEmail(event.target.value)}
                type="email"
                placeholder="person@yourstore.ng"
                className="w-full rounded-xl border border-[var(--border)] bg-white px-4 py-3 text-sm outline-none focus:border-black"
              />
            </label>

            <label className="block">
              <span className="mb-2 block text-xs font-semibold uppercase tracking-[0.12em] text-[var(--muted)]">
                Role
              </span>
              <select
                value={inviteRole}
                onChange={(event) => setInviteRole(event.target.value)}
                className="w-full rounded-xl border border-[var(--border)] bg-white px-4 py-3 text-sm outline-none"
              >
                <option value="manager">Manager</option>
                <option value="staff">Staff</option>
              </select>
            </label>

            <button
              type="button"
              disabled={inviteLoading || !inviteEmail.trim()}
              onClick={invitePersonnel}
              className="w-full rounded-xl bg-black px-4 py-3 text-sm font-semibold text-white disabled:cursor-not-allowed disabled:opacity-40"
            >
              {inviteLoading ? "Creating invitation…" : "Create invitation"}
            </button>
          </div>
        </SectionCard>
      </div>

      {invitation ? (
        <SectionCard
          title="Invitation created"
          description="Development view only. The raw token is shown once."
        >
          <div className="space-y-3">
            <div className="rounded-xl border border-[var(--border)] bg-[var(--background)] p-4">
              <p className="text-xs font-semibold uppercase tracking-[0.12em] text-[var(--muted)]">
                Invitation token
              </p>
              <p className="mt-2 break-all font-mono text-xs">
                {invitation.token}
              </p>
            </div>
            <p className="text-xs text-[var(--muted)]">
              In production, this token should be delivered through the
              configured invitation channel rather than displayed in the
              workspace.
            </p>
          </div>
        </SectionCard>
      ) : null}
    </main>
  );
}

function MetricCard({
  label,
  value,
  detail,
}: {
  label: string;
  value: string;
  detail: string;
}) {
  return (
    <div className="rounded-2xl border border-[var(--border)] bg-white p-5">
      <p className="text-xs font-semibold uppercase tracking-[0.14em] text-[var(--muted)]">
        {label}
      </p>
      <p className="mt-3 text-3xl font-semibold tracking-[-0.04em]">
        {value}
      </p>
      <p className="mt-1 text-xs text-[var(--muted)]">{detail}</p>
    </div>
  );
}

function TreeMember({
  member,
  level,
}: {
  member: StoreTreeMember;
  level: "owner" | "manager" | "staff";
}) {
  const roleLabel =
    level === "owner"
      ? "Owner"
      : level === "manager"
        ? "Manager"
        : "Staff";

  return (
    <div className="flex items-center justify-between gap-4 rounded-2xl border border-[var(--border)] bg-white p-4">
      <div className="min-w-0">
        <div className="flex flex-wrap items-center gap-2">
          <span className="text-sm font-semibold">{roleLabel}</span>
          <span className="rounded-full border border-[var(--border)] px-2 py-0.5 text-[10px] font-semibold uppercase tracking-[0.1em]">
            {memberStatusText(member)}
          </span>
        </div>
        <p className="mt-1 truncate text-sm text-[var(--muted)]">
          {member.email}
        </p>
      </div>

      <div className="shrink-0 text-right">
        <p className="font-mono text-xs font-semibold">
          {member.personnel_id ?? "—"}
        </p>
        <p className="mt-1 text-[10px] uppercase tracking-[0.1em] text-[var(--muted)]">
          Personnel ID
        </p>
      </div>
    </div>
  );
}

function memberStatusText(member: StoreTreeMember) {
  if (!member.is_active) return "Suspended";
  if (member.account_status === "invitation_pending") {
    return "Invitation pending";
  }
  return "Active";
}

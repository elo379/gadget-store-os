"use client";

import { FormEvent, useCallback, useEffect, useState } from "react";
import { apiGet, apiPost } from "@/lib/api";
import { useOrganization } from "@/components/organization-provider";

type Member = {
  id?: string;
  membership_id?: string;
  user_id?: string;
  personnel_id?: string | null;
  email?: string;
  role_name?: string;
  parent_membership_id?: string | null;
  created_by_membership_id?: string | null;
  account_status?: string;
  invited_at?: string | null;
  accepted_at?: string | null;
  is_owner?: boolean;
  is_active?: boolean;
};

type Tree = {
  organization_id: string;
  members: Member[];
};

type Policy = {
  managers_can_create_staff: boolean;
  managers_can_create_managers: boolean;
  managers_can_assign_roles: boolean;
  managers_can_modify_permissions: boolean;
};

const roles = ["manager", "staff"];

export default function TeamPage() {
  const { organizationId } = useOrganization();

  const [tree, setTree] = useState<Tree | null>(null);
  const [policy, setPolicy] = useState<Policy | null>(null);

  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [roleName, setRoleName] = useState("staff");

  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [message, setMessage] = useState("");

  const load = useCallback(async () => {
    if (!organizationId) return;

    setLoading(true);
    setMessage("");

    try {
      const [treeData, policyData] = await Promise.all([
        apiGet<Tree>(`/organizations/${organizationId}/store-tree`),
        apiGet<Policy>(`/organizations/${organizationId}/store-tree/policy`),
      ]);

      setTree(treeData);
      setPolicy(policyData);
    } catch (error) {
      setMessage(
        error instanceof Error ? error.message : "Unable to load team.",
      );
    } finally {
      setLoading(false);
    }
  }, [organizationId]);

  useEffect(() => {
    void load();
  }, [load]);

  async function invite(event: FormEvent) {
    event.preventDefault();

    if (!organizationId || !email.trim() || password.length < 8) {
      setMessage("Enter a valid email and a password of at least 8 characters.");
      return;
    }

    setSaving(true);
    setMessage("");

    try {
      await apiPost(
        `/organizations/${organizationId}/store-tree/invitations`,
        {
          email: email.trim(),
          password,
          role_name: roleName,
        },
      );

      setEmail("");
      setPassword("");
      setMessage("Personnel invitation created.");
      await load();
    } catch (error) {
      setMessage(
        error instanceof Error
          ? error.message
          : "Unable to create personnel.",
      );
    } finally {
      setSaving(false);
    }
  }

  async function personnelAction(
    membershipId: string,
    action: "suspend" | "reactivate" | "revoke",
  ) {
    if (!organizationId) return;

    setSaving(true);
    setMessage("");

    try {
      const token = localStorage.getItem("gsos_access_token");

      const response = await fetch(
        `${process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"}/organizations/${organizationId}/store-tree/personnel/${membershipId}/${action}`,
        {
          method: "PATCH",
          headers: {
            Authorization: `Bearer ${token}`,
          },
        },
      );

      if (!response.ok) {
        const body = await response.text();
        throw new Error(body || `Unable to ${action} personnel.`);
      }

      setMessage(`Personnel ${action}d successfully.`);
      await load();
    } catch (error) {
      setMessage(
        error instanceof Error
          ? error.message
          : `Unable to ${action} personnel.`,
      );
    } finally {
      setSaving(false);
    }
  }

  const members = tree?.members ?? [];

  return (
    <main className="space-y-6">
      <section>
        <p className="text-sm font-medium text-zinc-500">Settings</p>
        <h1 className="mt-1 text-2xl font-semibold text-zinc-950">
          Team & Store Tree
        </h1>
        <p className="mt-2 max-w-2xl text-sm text-zinc-500">
          Manage store personnel, roles and account status from the owner
          controlled identity tree.
        </p>
      </section>

      {message ? (
        <div className="rounded-xl border border-zinc-200 bg-zinc-50 px-4 py-3 text-sm text-zinc-700">
          {message}
        </div>
      ) : null}

      <section className="grid gap-6 lg:grid-cols-[minmax(0,1fr)_minmax(0,1.4fr)]">
        <form
          onSubmit={invite}
          className="rounded-2xl border border-zinc-200 bg-white p-5"
        >
          <h2 className="font-semibold text-zinc-950">
            Add personnel
          </h2>

          <p className="mt-1 text-sm text-zinc-500">
            Create a protected account inside this store&apos;s identity tree.
          </p>

          <div className="mt-5 space-y-4">
            <label className="block">
              <span className="text-sm font-medium text-zinc-700">
                Email
              </span>
              <input
                value={email}
                onChange={(event) => setEmail(event.target.value)}
                type="email"
                required
                className="mt-1 w-full rounded-xl border border-zinc-200 px-3 py-2.5 text-sm outline-none focus:border-zinc-500"
                placeholder="staff@example.com"
              />
            </label>

            <label className="block">
              <span className="text-sm font-medium text-zinc-700">
                Temporary password
              </span>
              <input
                value={password}
                onChange={(event) => setPassword(event.target.value)}
                type="password"
                minLength={8}
                required
                className="mt-1 w-full rounded-xl border border-zinc-200 px-3 py-2.5 text-sm outline-none focus:border-zinc-500"
                placeholder="Minimum 8 characters"
              />
            </label>

            <label className="block">
              <span className="text-sm font-medium text-zinc-700">
                Role
              </span>
              <select
                value={roleName}
                onChange={(event) => setRoleName(event.target.value)}
                className="mt-1 w-full rounded-xl border border-zinc-200 bg-white px-3 py-2.5 text-sm outline-none focus:border-zinc-500"
              >
                {roles.map((role) => (
                  <option key={role} value={role}>
                    {role}
                  </option>
                ))}
              </select>
            </label>

            <button
              type="submit"
              disabled={saving}
              className="w-full rounded-xl bg-zinc-950 px-4 py-2.5 text-sm font-medium text-white disabled:opacity-50"
            >
              {saving ? "Saving..." : "Create personnel"}
            </button>
          </div>
        </form>

        <section className="rounded-2xl border border-zinc-200 bg-white p-5">
          <h2 className="font-semibold text-zinc-950">
            Store Tree Policy
          </h2>

          <div className="mt-4 grid gap-3 sm:grid-cols-2">
            {policy ? (
              <>
                <PolicyItem
                  label="Managers can create staff"
                  enabled={policy.managers_can_create_staff}
                />
                <PolicyItem
                  label="Managers can create managers"
                  enabled={policy.managers_can_create_managers}
                />
                <PolicyItem
                  label="Managers can assign roles"
                  enabled={policy.managers_can_assign_roles}
                />
                <PolicyItem
                  label="Managers can modify permissions"
                  enabled={policy.managers_can_modify_permissions}
                />
              </>
            ) : (
              <p className="text-sm text-zinc-500">
                Loading policy...
              </p>
            )}
          </div>
        </section>
      </section>

      <section className="rounded-2xl border border-zinc-200 bg-white p-5">
        <div className="flex items-center justify-between gap-4">
          <div>
            <h2 className="font-semibold text-zinc-950">
              Assigned personnel
            </h2>
            <p className="mt-1 text-sm text-zinc-500">
              Manage active and inactive accounts in the store tree.
            </p>
          </div>

          <span className="rounded-full bg-zinc-100 px-3 py-1 text-xs font-medium text-zinc-600">
            {members.length} member{members.length === 1 ? "" : "s"}
          </span>
        </div>

        <div className="mt-4 divide-y divide-zinc-100">
          {loading ? (
            <p className="py-4 text-sm text-zinc-500">
              Loading...
            </p>
          ) : members.length === 0 ? (
            <p className="py-4 text-sm text-zinc-500">
              No personnel found.
            </p>
          ) : (
            members.map((member, index) => {
              const membershipId =
                member.id ??
                member.membership_id ??
                member.personnel_id ??
                String(index);

              const status =
                member.account_status ??
                (member.is_active === false ? "inactive" : "active");

              const isOwner = Boolean(member.is_owner);

              return (
                <div
                  key={membershipId}
                  className="flex flex-col gap-4 py-4 sm:flex-row sm:items-center sm:justify-between"
                >
                  <div className="min-w-0">
                    <p className="truncate font-medium text-zinc-900">
                      {member.email ??
                        member.personnel_id ??
                        "Personnel"}
                    </p>

                    <p className="mt-1 text-sm capitalize text-zinc-500">
                      {member.role_name ?? "Unassigned"}
                      {member.personnel_id
                        ? ` • ${member.personnel_id}`
                        : ""}
                    </p>
                  </div>

                  <div className="flex flex-wrap items-center gap-2">
                    <span className="rounded-full bg-zinc-100 px-3 py-1 text-xs font-medium capitalize text-zinc-600">
                      {status}
                    </span>

                    {isOwner ? (
                      <span className="rounded-full bg-zinc-950 px-3 py-1 text-xs font-medium text-white">
                        Owner
                      </span>
                    ) : (
                      <>
                        {status === "active" ? (
                          <button
                            type="button"
                            disabled={saving}
                            onClick={() =>
                              void personnelAction(
                                membershipId,
                                "suspend",
                              )
                            }
                            className="rounded-lg border border-zinc-200 px-3 py-1.5 text-xs font-medium text-zinc-700 disabled:opacity-50"
                          >
                            Suspend
                          </button>
                        ) : status === "suspended" ? (
                          <button
                            type="button"
                            disabled={saving}
                            onClick={() =>
                              void personnelAction(
                                membershipId,
                                "reactivate",
                              )
                            }
                            className="rounded-lg border border-zinc-200 px-3 py-1.5 text-xs font-medium text-zinc-700 disabled:opacity-50"
                          >
                            Reactivate
                          </button>
                        ) : null}

                        {status !== "revoked" ? (
                          <button
                            type="button"
                            disabled={saving}
                            onClick={() =>
                              void personnelAction(
                                membershipId,
                                "revoke",
                              )
                            }
                            className="rounded-lg border border-red-200 px-3 py-1.5 text-xs font-medium text-red-600 disabled:opacity-50"
                          >
                            Revoke
                          </button>
                        ) : null}
                      </>
                    )}
                  </div>
                </div>
              );
            })
          )}
        </div>
      </section>
    </main>
  );
}

function PolicyItem({
  label,
  enabled,
}: {
  label: string;
  enabled: boolean;
}) {
  return (
    <div className="rounded-xl border border-zinc-200 px-4 py-3">
      <p className="text-sm font-medium text-zinc-800">
        {label}
      </p>
      <p className="mt-1 text-xs font-medium text-zinc-500">
        {enabled ? "Enabled" : "Owner only"}
      </p>
    </div>
  );
}

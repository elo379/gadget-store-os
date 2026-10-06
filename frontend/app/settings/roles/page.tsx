"use client";

import { useEffect, useMemo, useState } from "react";
import { apiGet, apiPut } from "@/lib/api";
import { useOrganization } from "@/components/organization-provider";

type Member = {
  id?: string;
  membership_id?: string;
  email?: string;
  role_name?: string;
  account_status?: string;
  personnel_id?: string;
};

type StoreTree = {
  members?: Member[];
  personnel?: Member[];
};
type RoleConfiguration = { catalog: Record<string, string>; roles: Record<string, string[]>; can_manage: boolean };

export default function RolesPage() {
  const { organizationId } = useOrganization();
  const [members, setMembers] = useState<Member[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [catalog, setCatalog] = useState<Record<string, string>>({});
  const [rolePermissions, setRolePermissions] = useState<Record<string, string[]>>({ manager: [], staff: [] });
  const [canManage, setCanManage] = useState(false);
  const [selectedRole, setSelectedRole] = useState("manager");
  const [saving, setSaving] = useState(false);
  const [message, setMessage] = useState("");
  const availablePermissions = useMemo(() => Object.entries(catalog), [catalog]);

  useEffect(() => {
    if (!organizationId) return;

    async function load() {
      setLoading(true);
      setError("");

      try {
        const data = await apiGet<StoreTree>(`/organizations/${organizationId}/store-tree`);
        const config = await apiGet<RoleConfiguration>(`/organizations/${organizationId}/role-permissions`).catch(() => null);
        setMembers(data.members ?? data.personnel ?? []);
        setCatalog(config?.catalog ?? {});
        setRolePermissions(config?.roles ?? { manager: [], staff: [] });
        setCanManage(Boolean(config?.can_manage));
      } catch (err) {
        setError(err instanceof Error ? err.message : "Unable to load roles.");
      } finally {
        setLoading(false);
      }
    }

    void load();
  }, [organizationId]);

  const roles = Array.from(
    new Set(members.map((member) => member.role_name).filter(Boolean))
  );

  async function saveRolePermissions() {
    if (!organizationId) return;
    setSaving(true); setMessage(""); setError("");
    try {
      await apiPut(`/organizations/${organizationId}/role-permissions`, { role_name: selectedRole, permission_keys: rolePermissions[selectedRole] ?? [] });
      setMessage(`${selectedRole} permissions saved.`);
    } catch (cause) { setError(cause instanceof Error ? cause.message : "Unable to save role permissions."); }
    finally { setSaving(false); }
  }

  return (
    <main className="space-y-6">
      <div>
        <p className="text-sm text-zinc-500">Settings / Roles</p>
        <h1 className="text-2xl font-semibold text-zinc-950">
          Roles & Access
        </h1>
        <p className="mt-1 text-sm text-zinc-500">
          Review the roles currently assigned within this organization.
        </p>
      </div>

      {error && (
        <div className="rounded-xl border border-red-200 bg-red-50 p-4 text-sm text-red-700">
          {error}
        </div>
      )}
      {message && <p role="status" className="rounded-xl bg-emerald-50 p-3 text-sm text-emerald-900">{message}</p>}

      {canManage && <section className="rounded-2xl border border-zinc-200 bg-white p-5">
        <div className="flex flex-wrap items-center justify-between gap-3"><div><h2 className="font-semibold text-zinc-950">Permission assignments</h2><p className="mt-1 text-sm text-zinc-500">Changes apply to active members assigned to this role.</p></div><select aria-label="Role to configure" value={selectedRole} onChange={(event) => setSelectedRole(event.target.value)} className="h-11 rounded-lg border bg-white px-3"><option value="manager">Manager</option><option value="staff">Staff</option></select></div>
        <div className="mt-4 grid gap-2 sm:grid-cols-2 lg:grid-cols-3">{availablePermissions.map(([key, description]) => <label key={key} className="flex min-h-12 items-start gap-3 rounded-lg border border-zinc-100 p-3 text-sm"><input type="checkbox" checked={(rolePermissions[selectedRole] ?? []).includes(key)} onChange={(event) => setRolePermissions((current) => ({ ...current, [selectedRole]: event.target.checked ? [...(current[selectedRole] ?? []), key] : (current[selectedRole] ?? []).filter((item) => item !== key) }))} className="mt-0.5 h-4 w-4" /><span><span className="block font-medium">{key}</span><span className="text-xs text-zinc-500">{description}</span></span></label>)}</div>
        <button type="button" disabled={saving || loading} onClick={() => void saveRolePermissions()} className="mt-4 min-h-11 rounded-xl bg-zinc-950 px-5 text-sm font-semibold text-white disabled:opacity-50">{saving ? "Saving…" : "Save permissions"}</button>
      </section>}

      <section className="rounded-2xl border border-zinc-200 bg-white p-5">
        <h2 className="font-semibold text-zinc-950">Active roles</h2>

        {loading ? (
          <p className="mt-4 text-sm text-zinc-500">Loading roles...</p>
        ) : roles.length === 0 ? (
          <p className="mt-4 text-sm text-zinc-500">
            No role assignments found.
          </p>
        ) : (
          <div className="mt-4 grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
            {roles.map((role) => {
              const count = members.filter(
                (member) => member.role_name === role
              ).length;

              return (
                <div
                  key={role}
                  className="rounded-xl border border-zinc-200 p-4"
                >
                  <p className="font-medium capitalize text-zinc-950">
                    {role}
                  </p>
                  <p className="mt-1 text-sm text-zinc-500">
                    {count} member{count === 1 ? "" : "s"}
                  </p>
                </div>
              );
            })}
          </div>
        )}
      </section>

      <section className="rounded-2xl border border-zinc-200 bg-white p-5">
        <h2 className="font-semibold text-zinc-950">Assigned personnel</h2>

        <div className="mt-4 divide-y divide-zinc-100">
          {loading ? (
            <p className="py-4 text-sm text-zinc-500">Loading...</p>
          ) : members.length === 0 ? (
            <p className="py-4 text-sm text-zinc-500">
              No personnel found.
            </p>
          ) : (
            members.map((member, index) => (
              <div
                key={
                  member.membership_id ??
                  member.id ??
                  member.personnel_id ??
                  index
                }
                className="flex items-center justify-between gap-4 py-4"
              >
                <div>
                  <p className="font-medium text-zinc-900">
                    {member.email ?? member.personnel_id ?? "Personnel"}
                  </p>
                  <p className="text-sm capitalize text-zinc-500">
                    {member.role_name ?? "Unassigned"}
                  </p>
                </div>

                <span className="rounded-full bg-zinc-100 px-3 py-1 text-xs font-medium capitalize text-zinc-600">
                  {member.account_status ?? "active"}
                </span>
              </div>
            ))
          )}
        </div>
      </section>
    </main>
  );
}

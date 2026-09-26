"use client";

import { useEffect, useState } from "react";
import { apiGet } from "@/lib/api";
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

export default function RolesPage() {
  const { organizationId } = useOrganization();
  const [members, setMembers] = useState<Member[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    if (!organizationId) return;

    async function load() {
      setLoading(true);
      setError("");

      try {
        const data = await apiGet<StoreTree>(
          `/organizations/${organizationId}/store-tree`
        );

        setMembers(data.members ?? data.personnel ?? []);
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

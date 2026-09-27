"use client";

import { useEffect, useState } from "react";
import { apiGet } from "@/lib/api";
import { useOrganization } from "@/components/organization-provider";
import { PageHeader } from "@/components/page-header";

type DashboardData = Record<string, unknown>;

export default function DashboardPage() {
  const { organizationId } = useOrganization();
  const [data, setData] = useState<DashboardData>({});
  const [loading, setLoading] = useState(true);
  const [message, setMessage] = useState("");

  async function loadDashboard() {
    if (!organizationId) return;

    setLoading(true);

    try {
      const result = await apiGet<DashboardData>(
        `/dashboard?organization_id=${organizationId}`,
      );

      setData(result ?? {});
      setMessage("");
    } catch {
      setData({});
      setMessage("Unable to load dashboard data.");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    void loadDashboard();
  }, [organizationId]);

  const entries = Object.entries(data).filter(
    ([, value]) =>
      typeof value === "string" ||
      typeof value === "number" ||
      typeof value === "boolean",
  );

  return (
    <div className="space-y-6">
      <PageHeader
        eyebrow="Overview"
        title="Dashboard"
        description="Live operational overview for your store."
      />

      <div className="flex justify-end">
        <button
          type="button"
          onClick={() => void loadDashboard()}
          disabled={loading}
          className="rounded-xl border border-[var(--border)] bg-[var(--surface)] px-4 py-2 text-sm font-semibold disabled:opacity-50"
        >
          {loading ? "Refreshing…" : "Refresh"}
        </button>
      </div>

      {message && (
        <div className="rounded-xl border border-[var(--border)] bg-[var(--surface)] p-4 text-sm">
          {message}
        </div>
      )}

      {loading ? (
        <div className="rounded-2xl border border-[var(--border)] bg-[var(--surface)] p-6 text-sm">
          Loading dashboard…
        </div>
      ) : entries.length === 0 ? (
        <div className="rounded-2xl border border-[var(--border)] bg-[var(--surface)] p-6 text-sm">
          No dashboard metrics available yet.
        </div>
      ) : (
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
          {entries.map(([key, value]) => (
            <div
              key={key}
              className="rounded-2xl border border-[var(--border)] bg-[var(--surface)] p-5 shadow-sm"
            >
              <p className="text-xs font-semibold uppercase tracking-wide text-[var(--muted)]">
                {key.replaceAll("_", " ")}
              </p>
              <p className="mt-3 text-2xl font-bold">
                {String(value)}
              </p>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

"use client";

import { useEffect, useState } from "react";
import { apiGet } from "@/lib/api";
import { useOrganization } from "@/components/organization-provider";
import { PageHeader } from "@/components/page-header";

type ReportRow = {
  id?: string;
  name?: string;
  value?: number | string;
  total?: number | string;
  status?: string;
};

export default function ReportsPage() {
  const { organizationId } = useOrganization();
  const [rows, setRows] = useState<ReportRow[]>([]);
  const [loading, setLoading] = useState(true);
  const [message, setMessage] = useState("");

  async function loadReports() {
    if (!organizationId) return;

    setLoading(true);

    try {
      const data = await apiGet<ReportRow[]>(
        `/reports?organization_id=${organizationId}`,
      );

      setRows(Array.isArray(data) ? data : []);
      setMessage("");
    } catch {
      setRows([]);
      setMessage("Unable to load reports.");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    void loadReports();
  }, [organizationId]);

  return (
    <div className="space-y-6">
      <PageHeader
        eyebrow="Analytics"
        title="Reports"
        description="Review operational and financial reporting for the organization."
      />

      <div className="flex justify-end">
        <button
          type="button"
          onClick={() => void loadReports()}
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
          Loading reports…
        </div>
      ) : rows.length === 0 ? (
        <div className="rounded-2xl border border-[var(--border)] bg-[var(--surface)] p-6 text-sm">
          No report data available.
        </div>
      ) : (
        <div className="overflow-x-auto rounded-2xl border border-[var(--border)] bg-[var(--surface)]">
          <table className="w-full text-left text-sm">
            <thead>
              <tr className="border-b text-[var(--muted)]">
                <th className="px-4 py-3">Report</th>
                <th className="px-4 py-3">Value</th>
                <th className="px-4 py-3">Status</th>
              </tr>
            </thead>
            <tbody>
              {rows.map((row, index) => (
                <tr key={row.id ?? index} className="border-b last:border-0">
                  <td className="px-4 py-4 font-medium">
                    {row.name ?? "Report"}
                  </td>
                  <td className="px-4 py-4">
                    {row.value ?? row.total ?? "—"}
                  </td>
                  <td className="px-4 py-4">
                    {row.status ?? "Available"}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}

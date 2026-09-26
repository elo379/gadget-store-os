"use client";

import { useEffect, useState } from "react";
import { apiGet } from "@/lib/api";
import { useOrganization } from "@/components/organization-provider";

type ReportRow = Record<string, unknown>;

export default function ReportsPage() {
  const { organizationId } = useOrganization();
  const [rows, setRows] = useState<ReportRow[]>([]);
  const [period, setPeriod] = useState("30");
  const [message, setMessage] = useState("");

  async function load() {
    if (!organizationId) return;

    setMessage("");

    try {
      const data = await apiGet<ReportRow[]>(
        `/reports?organization_id=${organizationId}&days=${period}`,
      );
      setRows(Array.isArray(data) ? data : []);
    } catch (error) {
      setRows([]);
      setMessage(error instanceof Error ? error.message : "Report endpoint unavailable.");
    }
  }

  useEffect(() => {
    void load();
  }, [organizationId, period]);

  return (
    <div className="space-y-6">
      <header className="flex flex-col gap-4 sm:flex-row sm:items-end sm:justify-between">
        <div>
          <p className="text-sm font-medium text-[var(--muted)]">Analytics</p>
          <h1 className="text-3xl font-semibold tracking-tight">Reports</h1>
          <p className="mt-1 text-sm text-[var(--muted)]">
            Review transaction and operational reporting.
          </p>
        </div>

        <select
          value={period}
          onChange={(e) => setPeriod(e.target.value)}
          className="rounded-xl border bg-white px-4 py-3"
        >
          <option value="7">Last 7 days</option>
          <option value="30">Last 30 days</option>
          <option value="90">Last 90 days</option>
          <option value="365">Last 12 months</option>
        </select>
      </header>

      <section className="rounded-2xl border bg-white p-5">
        <div className="flex items-center justify-between">
          <h2 className="font-semibold">Report data</h2>
          <button onClick={() => void load()} className="rounded-xl border px-4 py-2">
            Refresh
          </button>
        </div>

        {message && (
          <p className="mt-4 rounded-xl bg-[var(--background)] p-4 text-sm text-[var(--muted)]">
            {message}
          </p>
        )}

        <div className="mt-4 overflow-x-auto">
          <table className="w-full text-left text-sm">
            <thead>
              <tr className="border-b text-[var(--muted)]">
                <th className="px-3 py-3">Metric</th>
                <th className="px-3 py-3">Value</th>
              </tr>
            </thead>
            <tbody>
              {rows.map((row, index) => {
                const entries = Object.entries(row);
                return (
                  <tr key={index} className="border-b last:border-0">
                    <td className="px-3 py-4 font-medium">
                      {String(entries[0]?.[0] ?? "Record")}
                    </td>
                    <td className="px-3 py-4">
                      {String(entries[0]?.[1] ?? "—")}
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </section>
    </div>
  );
}

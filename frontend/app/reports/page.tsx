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
type Branch = { id: string; name: string };
const reportTypes = ["sales", "products", "staff", "expenses", "inventory", "customers", "suppliers"] as const;

export default function ReportsPage() {
  const { organizationId } = useOrganization();
  const [rows, setRows] = useState<ReportRow[]>([]);
  const [loading, setLoading] = useState(true);
  const [message, setMessage] = useState("");
  const [reportType, setReportType] = useState<(typeof reportTypes)[number]>("sales");
  const [branches, setBranches] = useState<Branch[]>([]);
  const [branchId, setBranchId] = useState("");

  async function loadReports() {
    if (!organizationId) return;

    setLoading(true);

    try {
      const data = await apiGet<Record<string, unknown> | Array<Record<string, unknown>>>(
        reportType === "suppliers"
          ? `/suppliers/performance/summary?organization_id=${organizationId}`
          : `/reports/${organizationId}/${reportType}${reportType === "sales" && branchId ? `?branch_id=${branchId}` : ""}`,
      );
      const reportRows = Array.isArray(data)
        ? data.map((supplier) => ({ name: String(supplier.supplier_name ?? "Supplier"), value: `Measured lead time: ${supplier.average_measured_lead_time_days ?? "insufficient receipts"} days · Defect rate: ${supplier.defect_rate == null ? "no recorded denominator" : `${(Number(supplier.defect_rate) * 100).toFixed(1)}%`}` }))
        : Object.entries(data).map(([name, value]) => ({ name: name.replaceAll("_", " "), value: typeof value === "object" ? JSON.stringify(value) : String(value ?? "—") }));
      setRows(reportRows);
      setMessage("");
    } catch {
      setRows([]);
      setMessage("Unable to load reports.");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    const timer = window.setTimeout(() => void loadReports(), 0);
    return () => window.clearTimeout(timer);
  }, [organizationId, reportType, branchId]);

  useEffect(() => {
    if (!organizationId) return;
    let active = true;
    void apiGet<Branch[]>(`/reports/${organizationId}/branches`).then((rows) => {
      if (active) setBranches(rows);
    }).catch(() => { if (active) setBranches([]); });
    return () => { active = false; };
  }, [organizationId]);

  return (
    <div className="space-y-6">
      <PageHeader
        eyebrow="Analytics"
        title="Reports"
        description="Analyze live sales, product, staff, expense, inventory, customer and supplier performance records."
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

      <nav aria-label="Report type" className="flex gap-2 overflow-x-auto rounded-xl border border-[var(--border)] bg-white p-2">
        {reportTypes.map((type) => <button key={type} type="button" aria-pressed={reportType === type} onClick={() => setReportType(type)} className={`min-h-10 shrink-0 rounded-lg px-4 text-sm font-medium capitalize ${reportType === type ? "bg-neutral-950 text-white" : "hover:bg-neutral-100"}`}>{type}</button>)}
      </nav>
      {reportType === "sales" && branches.length > 0 ? <label className="flex max-w-sm flex-col gap-1 text-sm">Branch sales <select value={branchId} onChange={(event) => setBranchId(event.target.value)} className="min-h-11 rounded-lg border bg-white px-3"><option value="">All accessible branches</option>{branches.map((branch) => <option key={branch.id} value={branch.id}>{branch.name}</option>)}</select></label> : null}

      {loading ? (
        <div role="status" aria-busy="true" className="rounded-2xl border border-[var(--border)] bg-[var(--surface)] p-6 text-sm">
          Loading reports…
        </div>
      ) : message ? (
        <div role="alert" className="rounded-2xl border border-amber-200 bg-amber-50 p-6 text-sm text-amber-950">
          <p>{message}</p><button type="button" onClick={() => void loadReports()} className="mt-3 min-h-10 rounded-lg border border-amber-300 px-3 font-semibold">Retry report</button>
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

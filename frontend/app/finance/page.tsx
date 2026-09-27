"use client";

import { useEffect, useState } from "react";
import { apiGet } from "@/lib/api";
import { useOrganization } from "@/components/organization-provider";

type Summary = {
  revenue?: number | string;
  cogs?: number | string;
  gross_profit?: number | string;
  expenses?: number | string;
  net_operating_profit?: number | string;
};

function money(value: number | string | undefined) {
  return `₦${Number(value ?? 0).toLocaleString()}`;
}

export default function FinancePage() {
  const { organizationId } = useOrganization();
  const [summary, setSummary] = useState<Summary>({});
  const [loading, setLoading] = useState(true);

  async function load() {
    if (!organizationId) return;
    setLoading(true);
    try {
      const data = await apiGet<Summary>(
        `/finance/${organizationId}/summary`,
      );
      setSummary(data);
    } catch {
      setSummary({});
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    void load();
  }, [organizationId]);

  const cards = [
    ["Revenue", summary.revenue],
    ["COGS", summary.cogs],
    ["Gross profit", summary.gross_profit],
    ["Expenses", summary.expenses],
    ["Net operating profit", summary.net_operating_profit],
  ];

  return (
    <div className="space-y-6">
      <header>
        <p className="text-sm font-medium text-[var(--muted)]">Finance</p>
        <h1 className="text-3xl font-semibold tracking-tight">Financial overview</h1>
        <p className="mt-1 text-sm text-[var(--muted)]">
          Transaction-derived financial performance for the store.
        </p>
      </header>

      <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-5">
        {cards.map(([label, value]) => (
          <div key={label} className="rounded-2xl border border-[var(--border)] bg-[var(--surface)] shadow-sm p-5">
            <p className="text-sm text-[var(--muted)]">{label}</p>
            <p className="mt-2 text-2xl font-semibold">
              {loading ? "Loading..." : money(value)}
            </p>
          </div>
        ))}
      </div>

      <section className="rounded-2xl border border-[var(--border)] bg-[var(--surface)] shadow-sm p-6">
        <div className="flex items-center justify-between">
          <div>
            <h2 className="font-semibold">Financial controls</h2>
            <p className="text-sm text-[var(--muted)]">
              Refresh the live summary from the backend.
            </p>
          </div>
          <button
            onClick={() => void load()}
            className="rounded-xl border px-4 py-3"
          >
            Refresh
          </button>
        </div>
      </section>
    </div>
  );
}

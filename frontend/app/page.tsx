"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { apiGet } from "@/lib/api";
import { useOrganization } from "@/components/organization-provider";

type Summary = {
  sales?: number | string;
  revenue?: number | string;
  gross_profit?: number | string;
  inventory_units?: number | string;
  open_orders?: number | string;
  [key: string]: unknown;
};

type Operational = {
  low_stock_count?: number;
  pending_orders?: number;
  staff_count?: number;
  [key: string]: unknown;
};

function money(value: number | string | undefined) {
  return `₦${Number(value ?? 0).toLocaleString()}`;
}

export default function DashboardPage() {
  const { organizationId } = useOrganization();
  const [summary, setSummary] = useState<Summary>({});
  const [operations, setOperations] = useState<Operational>({});
  const [loading, setLoading] = useState(true);

  async function load() {
    if (!organizationId) return;

    setLoading(true);

    const [summaryResult, operationsResult] = await Promise.allSettled([
      apiGet<Summary>(`/dashboard/${organizationId}/summary`),
      apiGet<Operational>(`/dashboard/${organizationId}/operational`),
    ]);

    if (summaryResult.status === "fulfilled") setSummary(summaryResult.value);
    if (operationsResult.status === "fulfilled") setOperations(operationsResult.value);

    setLoading(false);
  }

  useEffect(() => {
    void load();
  }, [organizationId]);

  const cards = [
    ["Today's sales", money(summary.sales ?? summary.revenue)],
    ["Gross profit", money(summary.gross_profit)],
    ["Inventory units", String(summary.inventory_units ?? 0)],
    ["Open orders", String(summary.open_orders ?? operations.pending_orders ?? 0)],
  ];

  return (
    <div className="space-y-6">
      <header className="flex items-end justify-between">
        <div>
          <p className="text-sm font-medium text-[var(--muted)]">Store overview</p>
          <h1 className="text-3xl font-semibold tracking-tight">Dashboard</h1>
        </div>
        <button onClick={() => void load()} className="rounded-xl border px-4 py-3">
          Refresh
        </button>
      </header>

      <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
        {cards.map(([label, value]) => (
          <div key={label} className="rounded-2xl border bg-white p-5">
            <p className="text-sm text-[var(--muted)]">{label}</p>
            <p className="mt-2 text-2xl font-semibold">
              {loading ? "Loading..." : value}
            </p>
          </div>
        ))}
      </div>

      <section className="rounded-2xl border bg-white p-6">
        <h2 className="font-semibold">Operational signals</h2>
        <div className="mt-5 grid gap-4 sm:grid-cols-3">
          <div className="rounded-xl bg-[var(--background)] p-4">
            <p className="text-sm text-[var(--muted)]">Low stock</p>
            <p className="mt-1 text-2xl font-semibold">
              {operations.low_stock_count ?? 0}
            </p>
          </div>
          <div className="rounded-xl bg-[var(--background)] p-4">
            <p className="text-sm text-[var(--muted)]">Pending orders</p>
            <p className="mt-1 text-2xl font-semibold">
              {operations.pending_orders ?? 0}
            </p>
          </div>
          <div className="rounded-xl bg-[var(--background)] p-4">
            <p className="text-sm text-[var(--muted)]">Staff</p>
            <p className="mt-1 text-2xl font-semibold">
              {operations.staff_count ?? 0}
            </p>
          </div>
        </div>
      </section>

      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        {[
          ["/sales/pos", "Open POS"],
          ["/inventory", "Inventory"],
          ["/devices", "Device lookup"],
          ["/reports", "Reports"],
        ].map(([href, label]) => (
          <Link
            key={href}
            href={href}
            className="rounded-2xl border bg-white p-5 font-semibold transition hover:-translate-y-0.5"
          >
            {label}
          </Link>
        ))}
      </div>
    </div>
  );
}

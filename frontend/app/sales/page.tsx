"use client";

import { useCallback, useEffect, useState } from "react";
import Link from "next/link";
import { AppShell } from "@/components/app-shell";
import { PageHeader } from "@/components/page-header";
import { useOrganization } from "@/components/organization-provider";
import { apiGet } from "@/lib/api";

type SalesSummary = {
  sales_count: number;
  revenue: number | string;
  gross_profit: number | string;
};

function money(value: number | string | undefined) {
  return `₦${Number(value ?? 0).toLocaleString()}`;
}

export default function SalesPage() {
  const { organizationId } = useOrganization();
  const [summary, setSummary] = useState<SalesSummary | null>(null);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(true);

  const load = useCallback(async () => {
    if (!organizationId) return;
    setLoading(true);
    setError("");
    try {
      setSummary(await apiGet<SalesSummary>(`/sales/summary?organization_id=${organizationId}`));
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : "Unable to load sales summary.");
    } finally {
      setLoading(false);
    }
  }, [organizationId]);

  useEffect(() => { void load(); }, [load]);

  return (
    <AppShell>
      <PageHeader
        eyebrow="Point of sale"
        title="Sales"
        description="Review completed sales and start a checkout."
      />

      <div className="grid gap-5 lg:grid-cols-[1.4fr_0.8fr]">
        <section className="rounded-2xl border border-[var(--border)] bg-white p-6" aria-busy={loading}>
          <p className="text-xs font-semibold text-[var(--muted)]">Sales summary</p>
          {error ? (
            <div role="alert" className="mt-5 rounded-xl bg-red-50 p-4 text-sm text-red-800">
              <p>{error}</p>
              <button type="button" onClick={() => void load()} className="mt-2 font-semibold underline">Retry</button>
            </div>
          ) : (
            <div className="mt-6 grid gap-6 sm:grid-cols-3">
              <Metric label="Transactions" value={loading ? "—" : (summary?.sales_count ?? 0).toLocaleString()} />
              <Metric label="Revenue" value={loading ? "—" : money(summary?.revenue)} />
              <Metric label="Gross profit" value={loading ? "—" : money(summary?.gross_profit)} />
            </div>
          )}
        </section>

        <Link
          href="/sales/pos"
          className="rounded-2xl bg-neutral-900 p-6 text-white transition hover:bg-neutral-800"
        >
          <p className="text-[10px] font-semibold uppercase tracking-[0.16em] text-neutral-400">Point of sale</p>
          <p className="mt-4 text-2xl font-semibold tracking-[-0.03em]">Open POS</p>
          <p className="mt-2 text-sm text-neutral-400">Scan products and build a customer order.</p>
          <p className="mt-8 text-sm font-semibold">Start checkout →</p>
        </Link>
      </div>
    </AppShell>
  );
}

function Metric({ label, value }: { label: string; value: string }) {
  return (
    <div>
      <p className="text-xs text-[var(--muted)]">{label}</p>
      <p className="mt-2 text-2xl font-semibold">{value}</p>
    </div>
  );
}

"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { apiGet } from "@/lib/api";
import { useOrganization } from "@/components/organization-provider";
import { PageHeader } from "@/components/page-header";

type DashboardData = { revenue?: number | string; gross_profit?: number | string; operating_result?: number | string; today_revenue?: number | string; today_gross_profit?: number | string; outstanding?: number | string; today_sales_count?: number; product_count?: number; customer_count?: number; inventory_quantity?: number | string; device_count?: number };
type OperationalData = { sales_count?: number; active_inventory_items?: number; out_of_stock_items?: number; active_devices?: number; active_staff?: number; active_customers?: number };
type LiveRecord = Record<string, unknown>;
type DashboardLive = { lowStock: LiveRecord[]; purchaseOrders: LiveRecord[]; warranties: LiveRecord[]; repairs: LiveRecord[]; inventory: LiveRecord[]; products: LiveRecord[]; sales: LiveRecord[]; events: LiveRecord[] };

export default function DashboardPage() {
  const { organizationId } = useOrganization();
  const [data, setData] = useState<DashboardData>({});
  const [loading, setLoading] = useState(true);
  const [message, setMessage] = useState("");
  const [operations, setOperations] = useState<OperationalData>({});
  const [live, setLive] = useState<DashboardLive>({ lowStock: [], purchaseOrders: [], warranties: [], repairs: [], inventory: [], products: [], sales: [], events: [] });

  async function loadDashboard() {
    if (!organizationId) return;

    setLoading(true);

    try {
      const [result, operational] = await Promise.all([
        apiGet<DashboardData>(`/dashboard/${organizationId}/summary`),
        apiGet<OperationalData>(`/dashboard/${organizationId}/operational`),
      ]);
      setData(result ?? {});
      setOperations(operational ?? {});
      const requests = await Promise.allSettled([
        apiGet<LiveRecord[]>(`/dashboard/${organizationId}/low-stock`),
        apiGet<LiveRecord[]>(`/purchasing/orders?organization_id=${organizationId}`),
        apiGet<LiveRecord[]>(`/aftersales/warranties?organization_id=${organizationId}`),
        apiGet<LiveRecord[]>(`/aftersales/repairs?organization_id=${organizationId}`),
        apiGet<LiveRecord[]>(`/inventory?organization_id=${organizationId}`),
        apiGet<LiveRecord[]>(`/products?organization_id=${organizationId}`),
        apiGet<LiveRecord[]>(`/sales?organization_id=${organizationId}`),
        apiGet<LiveRecord[]>(`/organizations/${organizationId}/events?limit=10`),
      ]);
      const valueAt = (index: number) => requests[index].status === "fulfilled" && Array.isArray(requests[index].value) ? requests[index].value : [];
      setLive({ lowStock: valueAt(0), purchaseOrders: valueAt(1), warranties: valueAt(2), repairs: valueAt(3), inventory: valueAt(4), products: valueAt(5), sales: valueAt(6), events: valueAt(7) });
      setMessage("");
    } catch {
      setData({});
      setMessage("Unable to load dashboard data.");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    const timer = window.setTimeout(() => void loadDashboard(), 0);
    return () => window.clearTimeout(timer);
  }, [organizationId]);

  const money = (value?: number | string) => value == null ? "—" : new Intl.NumberFormat(undefined, { maximumFractionDigits: 2 }).format(Number(value));
  const metrics = [
    { label: "Today revenue", value: money(data.today_revenue), note: "Completed sales today", href: "/sales" },
    { label: "Sales today", value: data.today_sales_count?.toLocaleString() ?? "—", note: "Completed transactions", href: "/sales" },
    { label: "Gross profit", value: money(data.gross_profit), note: "All completed sales less recorded COGS", href: "/operations/profit" },
    { label: "Outstanding", value: money(data.outstanding), note: "Unpaid customer balances", href: "/sales" },
  ];

  return (
    <div className="space-y-7">
      <PageHeader
        eyebrow="Command center"
        title="Dashboard"
        description="A live view of store performance and the work that needs attention. Figures reflect the data currently available to your workspace."
        action={{ label: "New sale", onClick: () => { window.location.href = "/sales/pos" } }}
      />

      {message && (
        <div className="rounded-xl border border-[var(--border)] bg-[var(--surface)] p-4 text-sm">
          {message}
        </div>
      )}

      <section aria-label="Business summary" className="grid gap-px overflow-hidden rounded-2xl border border-[var(--border)] bg-[var(--border)] sm:grid-cols-2 xl:grid-cols-4">
        {metrics.map((item, index) => <Link href={item.href} key={item.label} className="bg-white p-5 transition hover:bg-neutral-50 sm:p-6">
          <p className="text-xs font-semibold uppercase tracking-[.12em] text-[var(--muted)]">{item.label}</p>
          <p className={`mt-3 text-2xl font-semibold tracking-tight ${index === 0 ? "text-[var(--accent)]" : ""}`}>{loading ? "···" : item.value}</p>
          <p className="mt-1 text-xs text-[var(--muted)]">{item.note}</p>
        </Link>)}
      </section>

      <div className="grid gap-5 xl:grid-cols-[1.4fr_.9fr]">
        <section className="rounded-2xl border border-[var(--border)] bg-white p-5 sm:p-6">
          <div className="flex items-start justify-between gap-4"><div><p className="text-xs font-semibold uppercase tracking-[.12em] text-[var(--muted)]">Sales activity</p><h2 className="mt-1 text-lg font-semibold">Store performance</h2></div><button onClick={() => void loadDashboard()} disabled={loading} className="min-h-10 rounded-xl border border-[var(--border)] px-3 text-sm font-semibold hover:bg-neutral-50 disabled:opacity-50">{loading ? "Refreshing…" : "Refresh"}</button></div>
          <div className="mt-6 grid grid-cols-2 gap-3 sm:grid-cols-3"><Metric label="Inventory units" value={data.inventory_quantity == null ? "—" : Number(data.inventory_quantity).toLocaleString()} /><Metric label="Active products" value={data.product_count?.toLocaleString() ?? "—"} /><Metric label="Active devices" value={operations.active_devices?.toLocaleString() ?? "—"} /></div>
          <p className="mt-5 rounded-xl bg-neutral-50 p-3 text-xs leading-5 text-[var(--muted)]">All figures are calculated from completed sales and current inventory records for this organization.</p>
        </section>
        <section className="rounded-2xl border border-[var(--border)] bg-white p-5 sm:p-6">
          <p className="text-xs font-semibold uppercase tracking-[.12em] text-[var(--muted)]">Inventory health</p><h2 className="mt-1 text-lg font-semibold">Stock at a glance</h2>
          <HealthRow label="In-stock items" value={operations.active_inventory_items} href="/inventory" />
          <HealthRow label="Out of stock" value={operations.out_of_stock_items} href="/inventory" danger />
          <HealthRow label="Serialized devices" value={operations.active_devices} href="/devices" />
          <HealthRow label="Low stock alerts" value={live.lowStock.filter((item) => item.stock_status === "low_stock").length} href="/operations/low-stock" />
        </section>
      </div>

      <section className="grid gap-5 xl:grid-cols-2">
        <LivePanel title="Operational feed" note="Latest durable business events" rows={live.events.slice(0, 5)} empty="No business events are recorded yet." />
        <LivePanel title="Needs attention" note="Live procurement and after-sales records" rows={[...live.purchaseOrders.slice(0, 2), ...live.warranties.slice(0, 2), ...live.repairs.slice(0, 2)]} empty="No purchase orders, warranty alerts, or repair cases are currently available." />
      </section>

      <section className="grid gap-5 xl:grid-cols-2">
        <LivePanel title="Recent sales" note="Latest transactions available to your workspace" rows={live.sales.slice(0, 5)} empty="No sales have been recorded yet." />
        <LivePanel title="Device activity" note="Recent serialized stock and after-sales records" rows={[...live.warranties.slice(0, 2), ...live.repairs.slice(0, 3)]} empty="No warranty or repair activity is available." />
      </section>

      <section className="grid gap-5 xl:grid-cols-2">
        <LivePanel title="Low stock" note={`${live.lowStock.length} products at or below reorder level`} rows={live.lowStock.slice(0, 5)} empty="No low stock alerts." />
        <LivePanel title="High-value stock" note="Estimated at recorded product cost, ranked by on-hand inventory value" rows={live.inventory.map((item) => { const product = live.products.find((entry) => entry.id === item.product_id); const cost = Number(product?.unit_cost ?? 0); return { ...item, name: product?.name ?? item.product_id, estimated_value: Number(item.quantity ?? 0) * cost, unit_cost: cost }; }).sort((a, b) => Number(b.estimated_value) - Number(a.estimated_value)).slice(0, 5)} empty="No inventory records are available." />
      </section>

      <section className="rounded-2xl border border-[var(--border)] bg-white p-5 sm:p-6">
        <div className="flex flex-wrap items-end justify-between gap-3"><div><p className="text-xs font-semibold uppercase tracking-[.12em] text-[var(--muted)]">Your workspace</p><h2 className="mt-1 text-lg font-semibold">Get work moving</h2><p className="mt-1 text-sm text-[var(--muted)]">Shortcuts to the workflows your team uses every day.</p></div></div>
        <div className="mt-5 grid gap-3 sm:grid-cols-2 lg:grid-cols-3">{[["New sale","/sales/pos","Start a checkout"],["Add product","/products","Build your catalogue"],["Receive stock","/purchasing","Record incoming goods"],["Transfer stock","/inventory","Manage stock movement"],["Add customer","/customers","Create a customer profile"],["Purchase orders","/purchasing","Review supplier orders"]].map(([label, href, note]) => <Link key={label} href={href} className="group flex min-h-20 items-center justify-between rounded-xl border border-[var(--border)] p-4 hover:border-neutral-400 hover:bg-neutral-50"><span><span className="block text-sm font-semibold">{label}</span><span className="mt-1 block text-xs text-[var(--muted)]">{note}</span></span><span aria-hidden="true" className="text-lg text-neutral-400 group-hover:text-[var(--accent)]">↗</span></Link>)}</div>
      </section>
    </div>
  );
}

function Metric({ label, value }: { label: string; value: string }) { return <div className="rounded-xl bg-neutral-50 p-4"><p className="text-xs text-[var(--muted)]">{label}</p><p className="mt-2 text-xl font-semibold">{value}</p></div>; }
function HealthRow({ label, value, href, danger = false }: { label: string; value?: number; href: string; danger?: boolean }) { return <Link href={href} className="mt-3 flex min-h-14 items-center justify-between border-b border-[var(--border)] py-2 last:border-0"><span className="text-sm font-medium">{label}</span><span className={`rounded-full px-3 py-1 text-sm font-semibold ${danger && value ? "bg-red-50 text-red-700" : "bg-emerald-50 text-emerald-800"}`}>{value?.toLocaleString() ?? "—"}<span className="ml-2 text-xs">↗</span></span></Link>; }
function LivePanel({ title, note, rows, empty }: { title: string; note: string; rows: LiveRecord[]; empty: string }) { return <section className="rounded-2xl border border-[var(--border)] bg-white p-5 sm:p-6"><h2 className="text-lg font-semibold">{title}</h2><p className="mt-1 text-xs text-[var(--muted)]">{note}</p>{rows.length ? <ul className="mt-4 divide-y divide-[var(--border)]">{rows.map((row, index) => <li key={String(row.id ?? row.inventory_item_id ?? index)} className="flex min-h-14 items-center justify-between gap-4 py-3"><span className="min-w-0 truncate text-sm font-medium">{String(row.name ?? row.product_name ?? row.reference_number ?? row.id ?? row.stock_status ?? "Record")}</span><span className="shrink-0 text-xs text-neutral-500">{row.estimated_value != null ? `₦${Number(row.estimated_value).toLocaleString()}` : row.total != null ? `₦${Number(row.total).toLocaleString()}` : String(row.status ?? row.stock_status ?? row.created_at ?? row.quantity ?? "Recorded")}</span></li>)}</ul> : <p className="py-8 text-center text-sm text-neutral-500">{empty}</p>}</section>; }

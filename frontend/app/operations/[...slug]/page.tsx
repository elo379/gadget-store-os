"use client";

import { useCallback, useEffect, useMemo, useState, type FormEvent } from "react";
import { useParams } from "next/navigation";
import { apiGet, apiPost } from "@/lib/api";
import { useOrganization } from "@/components/organization-provider";
import { PageHeader } from "@/components/page-header";
import { CameraScanner } from "@/components/camera-scanner";
import type { ScanResult } from "@/lib/scanner";

type Config = { title: string; eyebrow: string; description: string; path: (org: string) => string; action?: string };
const configs: Record<string, Config> = {
  receiving: { title: "Receiving", eyebrow: "Stock", description: "Review purchase orders and incoming stock receipts.", path: (o) => `/purchasing/orders?organization_id=${o}` },
  transfers: { title: "Transfers", eyebrow: "Stock", description: "Review stock movement history and transfer activity.", path: (o) => `/inventory?organization_id=${o}` },
  counts: { title: "Stock Counts", eyebrow: "Stock", description: "Review stock counts and reconcile recorded quantities.", path: (o) => `/stocktakes/${o}` },
  adjustments: { title: "Adjustments", eyebrow: "Stock", description: "Inspect current stock and movement history before recording a controlled adjustment.", path: (o) => `/inventory?organization_id=${o}` },
  "low-stock": { title: "Low Stock", eyebrow: "Stock", description: "Products at or below their configured reorder threshold.", path: (o) => `/dashboard/${o}/low-stock` },
  suppliers: { title: "Suppliers", eyebrow: "Procurement", description: "Supplier records for this organization.", path: (o) => `/suppliers?organization_id=${o}` },
  warranty: { title: "Warranty", eyebrow: "After-sales", description: "Warranty registrations and customer coverage.", path: (o) => `/aftersales/warranties?organization_id=${o}` },
  repairs: { title: "Repairs", eyebrow: "After-sales", description: "Repair cases and their current service status.", path: (o) => `/aftersales/repairs?organization_id=${o}` },
  attendance: { title: "Attendance", eyebrow: "People", description: "Staff attendance records for your workspace.", path: (o) => `/staff/${o}/attendance` },
  "finance-sales": { title: "Sales", eyebrow: "Finance", description: "Recorded sales and transaction totals.", path: () => "/sales" },
  payments: { title: "Payments", eyebrow: "Finance", description: "Payment reconciliation and outstanding balances.", path: (o) => `/finance/${o}/reconciliation` },
  expenses: { title: "Expenses", eyebrow: "Finance", description: "Recorded expenses and approval state.", path: (o) => `/expenses/${o}` },
  profit: { title: "Profit", eyebrow: "Finance", description: "Revenue, cost, expenses and operating result from recorded business activity.", path: (o) => `/finance/${o}/summary` },
  "report-sales": { title: "Sales Report", eyebrow: "Reports", description: "Sales performance calculated from completed transactions.", path: (o) => `/reports/${o}/sales` },
  "report-inventory": { title: "Inventory Report", eyebrow: "Reports", description: "Current inventory position from recorded stock.", path: (o) => `/reports/${o}/inventory` },
  "report-customers": { title: "Customer Report", eyebrow: "Reports", description: "Customer activity calculated from workspace records.", path: (o) => `/reports/${o}/customers` },
  "report-staff": { title: "Staff Report", eyebrow: "Reports", description: "Staff sales and operational reporting.", path: (o) => `/reports/${o}/staff` },
  "report-financial": { title: "Financial Report", eyebrow: "Reports", description: "Expense reporting and financial totals.", path: (o) => `/reports/${o}/expenses` },
};

export default function OperationalPage() {
  const params = useParams<{ slug: string[] }>();
  const section = params.slug?.at(-1) ?? "";
  const config = configs[section];
  const { organizationId } = useOrganization();
  const [data, setData] = useState<unknown>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [query, setQuery] = useState("");
  useEffect(() => {
    if (!organizationId || !config) return;
    let alive = true;
    queueMicrotask(() => { if (alive) { setLoading(true); setError(""); } });
    const request = () => apiGet<unknown>(config.path(organizationId)).then((value) => { if (alive) setData(value); }).catch((reason: unknown) => { if (alive) setError(reason instanceof Error ? reason.message : "Unable to load this view."); }).finally(() => { if (alive) setLoading(false); });
    queueMicrotask(request);
    return () => { alive = false; };
  }, [organizationId, section]);
  const rows = useMemo(() => {
    const raw = Array.isArray(data) ? data : data && typeof data === "object" ? Object.entries(data as Record<string, unknown>).map(([key, value]) => ({ metric: key, value })) : [];
    return raw.filter((row) => JSON.stringify(row).toLowerCase().includes(query.toLowerCase()));
  }, [data, query]);
  if (!config) return <div className="rounded-2xl border bg-white p-6">This operations view is unavailable.</div>;
  if (section === "transfers") return <TransferWorkspace organizationId={organizationId} />;
  return <div className="space-y-6">
    <PageHeader eyebrow={config.eyebrow} title={config.title} description={config.description} />
    <section className="rounded-2xl border border-[var(--border)] bg-white p-4 sm:p-5">
      <label className="block max-w-xl text-xs font-semibold">Search records<input value={query} onChange={(event) => setQuery(event.target.value)} className="mt-2 h-11 w-full rounded-xl border border-[var(--border)] px-3 text-sm font-normal" placeholder="Filter visible records" /></label>
      {loading ? <div role="status" className="py-14 text-center text-sm text-neutral-500">Loading {config.title.toLowerCase()}…</div> : error ? <div role="alert" className="mt-5 rounded-xl bg-red-50 p-4 text-sm text-red-800">{error}<button type="button" onClick={() => window.location.reload()} className="ml-3 font-semibold underline">Retry</button></div> : rows.length ? <div className="mt-5 overflow-x-auto"><table className="w-full min-w-[640px] text-left text-sm"><thead><tr className="border-b text-xs uppercase tracking-wide text-neutral-500"><th className="px-3 py-3">Record</th><th className="px-3 py-3">Details</th><th className="px-3 py-3">Status</th></tr></thead><tbody>{rows.map((row, index) => <tr key={index} className="border-b last:border-0"><td className="px-3 py-4 font-semibold">{label(row, "name", "product_name", "supplier_name", "id", "metric")}</td><td className="max-w-[520px] px-3 py-4 text-xs text-neutral-600">{formatDetails(row)}</td><td className="px-3 py-4">{label(row, "status", "stock_status", "state")}</td></tr>)}</tbody></table></div> : <div className="py-14 text-center"><p className="font-semibold">No {config.title.toLowerCase()} records</p><p className="mt-1 text-sm text-neutral-500">Records will appear here when they exist in this workspace.</p></div>}
      {!loading && !error && Boolean(data) && <p className="mt-4 text-xs text-neutral-500">Showing {rows.length} of {Array.isArray(data) ? data.length : Object.keys(data as object).length} live records.</p>}
    </section>
  </div>;
}

type TransferItem = { id: string; product_id: string; location_id: string | null; quantity: number | string; reserved_quantity: number | string; status: string };
type TransferProduct = { id: string; name: string; sku: string | null; barcode?: string | null };
type TransferLocation = { id: string; name: string };

function TransferWorkspace({ organizationId }: { organizationId: string | null }) {
  const [items, setItems] = useState<TransferItem[]>([]);
  const [products, setProducts] = useState<TransferProduct[]>([]);
  const [locations, setLocations] = useState<TransferLocation[]>([]);
  const [productId, setProductId] = useState("");
  const [sourceId, setSourceId] = useState("");
  const [destinationId, setDestinationId] = useState("");
  const [quantity, setQuantity] = useState("1");
  const [reason, setReason] = useState("");
  const [loading, setLoading] = useState(true);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [message, setMessage] = useState("");

  const load = useCallback(async () => {
    if (!organizationId) return;
    setLoading(true);
    setError("");
    try {
      const [stock, catalog, locationRows] = await Promise.all([
        apiGet<TransferItem[]>(`/inventory?organization_id=${organizationId}`),
        apiGet<TransferProduct[]>(`/products?organization_id=${organizationId}`),
        apiGet<TransferLocation[]>(`/inventory/locations?organization_id=${organizationId}`),
      ]);
      setItems(stock);
      setProducts(catalog);
      setLocations(locationRows);
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : "Transfer data could not be loaded.");
    } finally {
      setLoading(false);
    }
  }, [organizationId]);

  useEffect(() => { queueMicrotask(() => void load()); }, [load]);

  const sourceChoices = items.filter((item) => item.product_id === productId && item.status === "active");
  const source = items.find((item) => item.id === sourceId);
  const product = products.find((item) => item.id === productId);
  const locationName = (id: string | null) => locations.find((location) => location.id === id)?.name ?? "Unassigned";

  function locateProduct(result: ScanResult) {
    const match = products.find((item) => [item.sku, item.barcode].some((value) => value?.trim().toUpperCase() === result.normalizedValue));
    if (!match) {
      setError("No quantity product matches this scan. Serialized device transfers are not supported by this workflow.");
      return;
    }
    setError("");
    setMessage("");
    setProductId(match.id);
    setSourceId("");
    const available = items.filter((item) => item.product_id === match.id && item.status === "active");
    if (available.length === 1) setSourceId(available[0].id);
    else if (available.length > 1) setMessage("Choose the source location for this product.");
    else setError("This product has no active inventory record to transfer.");
  }

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!organizationId || !source) return;
    setBusy(true); setError(""); setMessage("");
    try {
      await apiPost(`/inventory/transfer?organization_id=${organizationId}`, {
        inventory_item_id: source.id,
        destination_location_id: destinationId,
        quantity,
        reason: reason.trim(),
      });
      setMessage("Transfer recorded in the inventory ledger.");
      setQuantity("1"); setReason(""); setDestinationId("");
      await load();
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : "Stock transfer failed.");
    } finally { setBusy(false); }
  }

  return <div className="space-y-6">
    <PageHeader eyebrow="Stock" title="Transfers" description="Move quantity inventory between store locations with paired ledger entries." action={{ label: "Refresh", onClick: () => void load() }} />
    {error && <div role="alert" className="rounded-xl bg-red-50 p-4 text-sm text-red-800">{error}</div>}
    {message && <div role="status" className="rounded-xl bg-emerald-50 p-4 text-sm text-emerald-900">{message}</div>}
    {loading ? <p role="status" className="rounded-2xl border bg-white p-8 text-sm text-neutral-500">Loading inventory and locations…</p> : <div className="grid gap-5 lg:grid-cols-[minmax(0,1fr)_minmax(280px,380px)]">
      <section className="rounded-2xl border bg-white p-5"><h2 className="font-semibold">Find a product to transfer</h2><CameraScanner expectation="barcode" onDetected={locateProduct} /><div className="mt-4 max-h-[50vh] overflow-auto"><table className="w-full text-left text-sm"><thead><tr className="border-b text-xs text-neutral-500"><th className="p-3">Product</th><th className="p-3">Location</th><th className="p-3">Available</th></tr></thead><tbody>{items.map((item) => <tr key={item.id} className={`cursor-pointer border-b last:border-0 ${sourceId === item.id ? "bg-neutral-50" : ""}`} onClick={() => { setProductId(item.product_id); setSourceId(item.id); }}><td className="p-3">{products.find((candidate) => candidate.id === item.product_id)?.name ?? "Product"}</td><td className="p-3">{locationName(item.location_id)}</td><td className="p-3">{Number(item.quantity) - Number(item.reserved_quantity)}</td></tr>)}</tbody></table></div></section>
      <form onSubmit={submit} className="space-y-4 rounded-2xl border bg-white p-5"><h2 className="font-semibold">Transfer stock</h2><label className="block text-sm">Product<select required value={productId} onChange={(event) => { setProductId(event.target.value); setSourceId(""); }} className="mt-1 h-11 w-full rounded-lg border bg-white px-3"><option value="">Select product</option>{products.filter((candidate) => items.some((item) => item.product_id === candidate.id)).map((item) => <option key={item.id} value={item.id}>{item.name}{item.sku ? ` · ${item.sku}` : ""}</option>)}</select></label><label className="block text-sm">Source location<select required value={sourceId} onChange={(event) => setSourceId(event.target.value)} className="mt-1 h-11 w-full rounded-lg border bg-white px-3"><option value="">Select source</option>{sourceChoices.map((item) => <option key={item.id} value={item.id}>{locationName(item.location_id)} · {Number(item.quantity) - Number(item.reserved_quantity)} available</option>)}</select></label><label className="block text-sm">Destination<select required value={destinationId} onChange={(event) => setDestinationId(event.target.value)} className="mt-1 h-11 w-full rounded-lg border bg-white px-3"><option value="">Select destination</option>{locations.filter((location) => location.id !== source?.location_id).map((location) => <option key={location.id} value={location.id}>{location.name}</option>)}</select></label><label className="block text-sm">Quantity<input required type="number" min="0.001" max={source ? Number(source.quantity) - Number(source.reserved_quantity) : undefined} step="0.001" value={quantity} onChange={(event) => setQuantity(event.target.value)} className="mt-1 h-11 w-full rounded-lg border px-3" /></label><label className="block text-sm">Reason<input value={reason} onChange={(event) => setReason(event.target.value)} className="mt-1 h-11 w-full rounded-lg border px-3" /></label><button disabled={busy || !source || !destinationId || Number(quantity) > Number(source?.quantity ?? 0) - Number(source?.reserved_quantity ?? 0)} className="min-h-11 w-full rounded-lg bg-neutral-950 px-4 font-semibold text-white disabled:opacity-50">{busy ? "Transferring…" : "Record transfer"}</button>{product && <p className="text-xs text-neutral-500">Scanned/selected {product.name}. Device registry records are not transferred through quantity inventory.</p>}</form>
    </div>}
  </div>;
}

function label(row: unknown, ...keys: string[]) { if (!row || typeof row !== "object") return String(row ?? "—"); const obj = row as Record<string, unknown>; for (const key of keys) if (obj[key] != null) return String(obj[key]); return "—"; }
function formatDetails(row: unknown) { if (!row || typeof row !== "object") return String(row); return Object.entries(row as Record<string, unknown>).filter(([key]) => !["name", "product_name", "supplier_name", "id", "metric", "status", "stock_status", "state"].includes(key)).map(([key, value]) => `${key.replaceAll("_", " ")}: ${typeof value === "object" && value ? JSON.stringify(value) : String(value ?? "—")}`).join(" · ") || "—"; }

"use client";

import { useCallback, useEffect, useMemo, useState } from "react";
import { useParams } from "next/navigation";
import { AppShell } from "@/components/app-shell";
import { PageHeader } from "@/components/page-header";
import { CameraScanner } from "@/components/camera-scanner";
import { apiGet, apiPatch, apiPost, ApiError } from "@/lib/api";
import type { ScanResult } from "@/lib/scanner";

type Stocktake = { id: string; organization_id: string; location_id: string | null; reference_number: string; status: string; notes: string; created_at?: string; submitted_by_user_id?: string | null; completed_by_user_id?: string | null; submitted_at?: string | null; completed_at?: string | null };
type StocktakeLine = { id: string; stocktake_id: string; inventory_item_id: string; expected_quantity: number | string; counted_quantity: number | string | null; variance: number | string; notes: string; counted_by_user_id?: string | null };
type InventoryItem = { id: string; product_id: string; location_id: string | null; quantity: number | string; status: string };
type Product = { id: string; name: string; sku: string | null; barcode?: string; is_serialized?: boolean };
type Location = { id: string; name: string };

export default function StocktakesPage() {
  const params = useParams<{ organizationId: string }>();
  const organizationId = params.organizationId;
  const [stocktakes, setStocktakes] = useState<Stocktake[]>([]);
  const [items, setItems] = useState<InventoryItem[]>([]);
  const [products, setProducts] = useState<Product[]>([]);
  const [locations, setLocations] = useState<Location[]>([]);
  const [selected, setSelected] = useState<Stocktake | null>(null);
  const [lines, setLines] = useState<StocktakeLine[]>([]);
  const [loading, setLoading] = useState(true);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [reference, setReference] = useState("");
  const [locationId, setLocationId] = useState("");
  const [scannerLine, setScannerLine] = useState<StocktakeLine | null>(null);

  const load = useCallback(async () => {
    if (!organizationId) return;
    setLoading(true);
    setError("");
    try {
      const [stocktakeRows, inventoryRows, productRows, locationRows] = await Promise.all([
        apiGet<Stocktake[]>(`/stocktakes/${organizationId}`),
        apiGet<InventoryItem[]>(`/inventory?organization_id=${organizationId}`),
        apiGet<Product[]>(`/products?organization_id=${organizationId}`),
        apiGet<Location[]>(`/inventory/locations?organization_id=${organizationId}`),
      ]);
      setStocktakes(stocktakeRows);
      setItems(inventoryRows);
      setProducts(productRows);
      setLocations(locationRows);
    } catch (cause) {
      setError(cause instanceof ApiError ? cause.message : "Unable to load stocktakes.");
    } finally {
      setLoading(false);
    }
  }, [organizationId]);

  const loadLines = useCallback(async (stocktake: Stocktake) => {
    setSelected(stocktake);
    setError("");
    try {
      setLines(await apiGet<StocktakeLine[]>(`/stocktakes/${organizationId}/${stocktake.id}/lines`));
    } catch (cause) {
      setError(cause instanceof ApiError ? cause.message : "Unable to load count lines.");
    }
  }, [organizationId]);

  useEffect(() => { queueMicrotask(() => void load()); }, [load]);

  const productById = useMemo(() => new Map(products.map((product) => [product.id, product])), [products]);
  const itemById = useMemo(() => new Map(items.map((item) => [item.id, item])), [items]);
  const productName = (line: StocktakeLine) => productById.get(itemById.get(line.inventory_item_id)?.product_id ?? "")?.name ?? "Inventory item";

  async function create(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!reference.trim()) return;
    setBusy(true); setError("");
    try {
      const created = await apiPost<Stocktake>("/stocktakes", { organization_id: organizationId, location_id: locationId || null, reference_number: reference.trim(), notes: "" });
      setReference("");
      await load();
      await loadLines(created);
    } catch (cause) {
      setError(cause instanceof ApiError ? cause.message : "Unable to start stocktake.");
    } finally { setBusy(false); }
  }

  async function saveCount(line: StocktakeLine, count: string) {
    if (!selected || count === "") return;
    setBusy(true); setError("");
    try {
      await apiPatch(`/stocktakes/${organizationId}/${selected.id}/lines/${line.id}`, { counted_quantity: count });
      await loadLines(selected);
    } catch (cause) {
      setError(cause instanceof ApiError ? cause.message : "Unable to save this count.");
    } finally { setBusy(false); }
  }

  async function transition(action: "submit" | "complete") {
    if (!selected) return;
    setBusy(true); setError("");
    try {
      const updated = await apiPost<Stocktake>(`/stocktakes/${organizationId}/${selected.id}/${action}`, {});
      setSelected(updated);
      await Promise.all([load(), loadLines(updated)]);
    } catch (cause) {
      setError(cause instanceof ApiError ? cause.message : `Unable to ${action} stocktake.`);
    } finally { setBusy(false); }
  }

  async function handleScan(result: ScanResult) {
    if (!scannerLine || !selected) return;
    const item = itemById.get(scannerLine.inventory_item_id);
    const product = item ? productById.get(item.product_id) : undefined;
    if (result.type === "imei") {
      setError("IMEI detected. This stocktake contains quantity inventory lines only; serialized device reconciliation is not enabled yet.");
      setScannerLine(null);
      return;
    }
    if (!product || ![product.sku, product.barcode].some((value) => value && value.toUpperCase() === result.normalizedValue)) {
      setError(`Scanned code ${result.normalizedValue} does not match ${product?.name ?? "this product"}.`);
      return;
    }
    const nextCount = Number(scannerLine.counted_quantity ?? 0) + 1;
    await saveCount(scannerLine, String(nextCount));
    setScannerLine(null);
  }

  return <AppShell>
    <PageHeader eyebrow="Stock control" title="Stocktake" description="Snapshot recorded quantities, count stock, review variances, then approve reconciliation." />
    <ol aria-label="Stocktake progress" className="mb-5 grid grid-cols-3 gap-2 rounded-2xl border border-[var(--border)] bg-white p-3 shadow-sm">
      {["Snapshot & count", "Review variance", "Approve & adjust"].map((step, index) => {
        const state = selected?.status === "completed" || (selected?.status === "review" && index < 2) || (selected?.status === "draft" && index === 0);
        return <li key={step} className={`flex min-h-11 items-center gap-2 rounded-xl px-2 text-xs font-semibold sm:px-3 ${state ? "bg-[var(--accent-soft)] text-[var(--accent-strong)]" : "bg-[var(--background)] text-[var(--muted)]"}`}><span className="grid h-6 w-6 shrink-0 place-items-center rounded-full bg-white text-[10px] shadow-sm">{state ? "✓" : String(index + 1).padStart(2, "0")}</span><span>{step}</span></li>;
      })}
    </ol>
    {error && <div role="alert" className="mb-4 rounded-xl border border-red-200 bg-red-50 p-3 text-sm text-red-800">{error}</div>}
    <div className="grid gap-5 xl:grid-cols-[minmax(260px,360px)_1fr]">
      <aside className="space-y-4">
        <form onSubmit={create} className="space-y-3 rounded-2xl border bg-white p-4">
          <h2 className="font-semibold">Start a count</h2>
          <label className="block text-sm">Reference<input required maxLength={100} value={reference} onChange={(event) => setReference(event.target.value)} placeholder="e.g. OCT-STORE-A" className="mt-1 h-11 w-full rounded-lg border px-3" /></label>
          <label className="block text-sm">Store location<select value={locationId} onChange={(event) => setLocationId(event.target.value)} className="mt-1 h-11 w-full rounded-lg border bg-white px-3"><option value="">All locations</option>{locations.map((location) => <option key={location.id} value={location.id}>{location.name}</option>)}</select></label>
          <button disabled={busy} className="min-h-11 w-full rounded-lg bg-neutral-900 px-4 font-semibold text-white disabled:opacity-50">{busy ? "Starting…" : "Start stocktake"}</button>
          <p className="text-xs text-neutral-500">The count starts from a snapshot. Reconciliation is posted only after approval.</p>
        </form>
        <section className="rounded-2xl border bg-white p-4">
          <h2 className="font-semibold">Previous counts</h2>
          {loading ? <p role="status" className="py-5 text-sm text-neutral-500">Loading stocktakes…</p> : stocktakes.length === 0 ? <p className="py-5 text-sm text-neutral-500">No stocktakes yet.</p> : <ul className="mt-3 space-y-2">{stocktakes.map((stocktake) => <li key={stocktake.id}><button onClick={() => void loadLines(stocktake)} className={`w-full rounded-xl border p-3 text-left ${selected?.id === stocktake.id ? "border-neutral-900 bg-neutral-50" : "border-neutral-200"}`}><span className="block font-medium">{stocktake.reference_number}</span><span className="mt-1 block text-xs capitalize text-neutral-500">{stocktake.status} · {stocktake.created_at ? new Date(stocktake.created_at).toLocaleString() : "date unavailable"}</span></button></li>)}</ul>}
        </section>
      </aside>
      <section className="min-w-0 rounded-2xl border bg-white">
        {!selected ? <div className="p-8 text-center text-sm text-neutral-500">Start a count or select a previous stocktake.</div> : <>
          <header className="flex flex-wrap items-center justify-between gap-3 border-b p-4"><div><h2 className="font-semibold">{selected.reference_number}</h2><p className="text-sm capitalize text-neutral-500">{selected.status} · {lines.filter((line) => line.counted_quantity !== null).length}/{lines.length} counted · {lines.filter((line) => line.counted_quantity !== null && Number(line.variance) !== 0).length} variances</p></div><div className="flex gap-2">{selected.status === "draft" && <button disabled={busy || lines.some((line) => line.counted_quantity === null)} onClick={() => void transition("submit")} className="min-h-11 rounded-lg bg-[var(--accent-strong)] px-4 text-sm font-semibold text-white disabled:opacity-50">Submit for review</button>}{selected.status === "review" && <button disabled={busy} onClick={() => void transition("complete")} className="min-h-11 rounded-lg bg-emerald-700 px-4 text-sm font-semibold text-white disabled:opacity-50">Approve & reconcile</button>}</div></header>
          {lines.length === 0 ? <p className="p-6 text-sm text-neutral-500">This snapshot contains no active inventory items.</p> : <div className="divide-y">{lines.map((line) => { const product = productById.get(itemById.get(line.inventory_item_id)?.product_id ?? ""); const counted = line.counted_quantity !== null; const variance = Number(line.variance); return <div key={line.id} className="grid gap-3 p-4 sm:grid-cols-[minmax(0,1fr)_auto] sm:items-center"><div><p className="font-medium">{productName(line)}</p><p className="mt-1 text-xs text-neutral-500">Expected {line.expected_quantity} · {counted ? variance === 0 ? "Matched" : `Variance ${variance > 0 ? "+" : ""}${variance}` : "Not counted"}</p></div>{selected.status === "draft" ? <div className="flex flex-wrap gap-2"><input aria-label={`Count ${product?.name ?? "item"}`} type="number" min="0" step="0.001" defaultValue={line.counted_quantity ?? ""} onBlur={(event) => { if (event.target.value !== String(line.counted_quantity ?? "")) void saveCount(line, event.target.value); }} className="h-11 w-28 rounded-lg border px-3" /><button type="button" onClick={() => setScannerLine(line)} className="min-h-11 rounded-lg border px-3 text-sm">Scan item</button></div> : <p className={`font-semibold ${counted && variance !== 0 ? "text-amber-700" : "text-[var(--foreground)]"}`}>Counted {line.counted_quantity ?? "—"}</p>}</div>; })}</div>}
          {selected.status === "review" && <div className="border-t bg-amber-50 p-4 text-sm text-amber-900">Review variance and approve from a different manager account. The owner may approve their own submission.</div>}
          {selected.status === "completed" && <div className="border-t bg-emerald-50 p-4 text-sm text-emerald-900">Approved by {selected.completed_by_user_id ?? "recorded reviewer"} · {selected.completed_at ? new Date(selected.completed_at).toLocaleString() : "timestamp unavailable"}</div>}
        </>}
      </section>
    </div>
    {scannerLine && <div role="dialog" aria-modal="true" aria-label="Scan stocktake item" className="fixed inset-0 z-50 flex items-end justify-center bg-black/50 p-0 sm:items-center sm:p-4"><div className="max-h-[95vh] w-full max-w-xl overflow-auto rounded-t-2xl bg-white p-4 sm:rounded-2xl"><div className="flex items-center justify-between"><h2 className="font-semibold">Scan {productName(scannerLine)}</h2><button className="min-h-11 min-w-11 rounded-lg border" onClick={() => setScannerLine(null)}>Close</button></div><CameraScanner expectation="barcode" onDetected={handleScan} /><p className="mt-2 text-xs text-neutral-500">A matching barcode increments this line by one. Use the count field for other quantities. Serialized IMEI reconciliation is not yet supported in this screen.</p></div></div>}
  </AppShell>;
}

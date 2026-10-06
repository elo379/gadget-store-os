"use client";

import { FormEvent, useEffect, useState } from "react";
import { apiGet, apiPost } from "@/lib/api";
import { PageHeader } from "@/components/page-header";
import { useOrganization } from "@/components/organization-provider";
import { CameraScanner } from "@/components/camera-scanner";
import type { ScanResult } from "@/lib/scanner";

type SaleLine = { id: string; product_id: string; quantity: number | string; unit_price: number | string; device_id: string | null };
type Sale = { id: string; reference_number: string; customer_id: string | null; total: number | string; lines: SaleLine[] };

export default function ReturnsPage() {
  const { organizationId } = useOrganization();
  const [sales, setSales] = useState<Sale[]>([]);
  const [saleId, setSaleId] = useState("");
  const [selected, setSelected] = useState<Record<string, string>>({});
  const [reference, setReference] = useState("");
  const [reason, setReason] = useState("");
  const [loading, setLoading] = useState(true);
  const [busy, setBusy] = useState(false);
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");
  async function load() {
    if (!organizationId) return;
    setLoading(true); setError("");
    try { const rows = await apiGet<Sale[]>(`/sales?organization_id=${organizationId}`); setSales(rows); }
    catch (e) { setError(e instanceof Error ? e.message : "Sales could not be loaded."); }
    finally { setLoading(false); }
  }
  useEffect(() => { queueMicrotask(() => void load()); }, [organizationId]);
  const sale = sales.find((row) => row.id === saleId);
  async function locateReturnedDevice(result: ScanResult) {
    if (!organizationId || !sale) {
      setError("Choose the sale before scanning a serialized device.");
      return;
    }
    const lookup = result.type === "imei" ? "imei" : result.type === "barcode" || result.type === "qr" ? "barcode" : "serial";
    try {
      const device = await apiGet<{ id: string }>(`/devices/lookup/${lookup}/${encodeURIComponent(result.normalizedValue)}?organization_id=${organizationId}`);
      const line = sale.lines.find((candidate) => candidate.device_id === device.id);
      if (!line) {
        setError("This device is not part of the selected sale and cannot be returned here.");
        return;
      }
      setError("");
      setSelected((current) => ({ ...current, [line.id]: "" }));
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : "The scanned device could not be matched to the selected sale.");
    }
  }
  async function submit(event: FormEvent) {
    event.preventDefault();
    if (!organizationId || !sale || !Object.keys(selected).length || Object.values(selected).some((disposition) => !disposition)) return;
    setBusy(true); setMessage(""); setError("");
    try {
      await apiPost("/customers/returns", { organization_id: organizationId, sale_id: sale.id, reference_number: reference.trim(), reason: reason.trim(), lines: Object.entries(selected).map(([sale_line_id, disposition]) => ({ sale_line_id, quantity: sale.lines.find((line) => line.id === sale_line_id)?.quantity, condition: disposition === "RESTOCK" ? "good" : "damaged", disposition })) });
      setMessage("Return recorded. Inventory, device status, finance and audit records have been updated."); setSaleId(""); setSelected({}); setReference(""); setReason(""); await load();
    } catch (e) { setError(e instanceof Error ? e.message : "Return could not be processed."); }
    finally { setBusy(false); }
  }
  return <div className="space-y-6">
    <PageHeader eyebrow="Sell" title="Returns" description="Record sale returns with a disposition for every returned item." action={{ label: "Refresh", onClick: () => void load() }} />
    {error && <div role="alert" className="rounded-xl bg-red-50 p-4 text-sm text-red-800">{error}</div>}{message && <div role="status" className="rounded-xl bg-emerald-50 p-4 text-sm text-emerald-900">{message}</div>}
    <form onSubmit={submit} className="max-w-3xl space-y-5 rounded-2xl border border-[var(--border)] bg-white p-5 sm:p-6">
      <label className="block text-sm font-medium">Completed sale<select required value={saleId} onChange={(e) => { setSaleId(e.target.value); setSelected({}); }} className="mt-1 h-11 w-full rounded-xl border bg-white px-3"><option value="">{loading ? "Loading sales…" : "Choose a sale"}</option>{sales.map((row) => <option key={row.id} value={row.id}>{row.reference_number} · {Number(row.total).toLocaleString()}</option>)}</select></label>
      {sale && <div><p className="mb-2 text-sm font-semibold">Find a serialized item from this sale</p><CameraScanner expectation="device" onDetected={locateReturnedDevice} /></div>}
      {sale && <fieldset className="space-y-2"><legend className="mb-2 text-sm font-semibold">Items returned</legend>{sale.lines.map((line) => <div key={line.id} className="grid gap-2 rounded-xl border p-3 sm:grid-cols-[1fr_180px]"><label className="flex min-h-10 items-center gap-3 text-sm"><input type="checkbox" checked={line.id in selected} onChange={(e) => setSelected((current) => { const next = { ...current }; if (e.target.checked) next[line.id] = "RESTOCK"; else delete next[line.id]; return next; })} />Product {line.product_id.slice(0, 8)} · sold {line.quantity}</label>{line.id in selected && <select required aria-label="Returned item disposition" value={selected[line.id]} onChange={(e) => setSelected((current) => ({ ...current, [line.id]: e.target.value }))} className="h-10 rounded-lg border bg-white px-2 text-sm"><option value="">Choose disposition</option><option value="RESTOCK">Restock</option><option value="DAMAGED">Damaged</option><option value="DEFECTIVE">Defective</option></select>}</div>)}</fieldset>}
      <div className="grid gap-3 sm:grid-cols-2"><label className="text-sm font-medium">Return reference<input required value={reference} onChange={(e) => setReference(e.target.value)} className="mt-1 h-11 w-full rounded-xl border px-3" /></label><label className="text-sm font-medium">Reason<input value={reason} onChange={(e) => setReason(e.target.value)} className="mt-1 h-11 w-full rounded-xl border px-3" /></label></div>
      <button disabled={busy || !sale || !Object.keys(selected).length || Object.values(selected).some((disposition) => !disposition)} className="min-h-11 rounded-xl bg-neutral-950 px-5 text-sm font-semibold text-white disabled:opacity-50">{busy ? "Recording return…" : "Record return"}</button>
    </form>
  </div>;
}

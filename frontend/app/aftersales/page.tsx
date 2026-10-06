"use client";

import { useCallback, useEffect, useState } from "react";
import { apiGet, apiPatch } from "@/lib/api";
import { PageHeader } from "@/components/page-header";
import { useOrganization } from "@/components/organization-provider";
import { CameraScanner } from "@/components/camera-scanner";
import type { ScanResult } from "@/lib/scanner";

type Repair = { id: string; reference_number: string; device_id: string; customer_id: string; status: string; diagnosis: string; created_at: string };
type Warranty = { id: string; device_id: string; customer_id: string | null; sale_id: string; starts_at: string; ends_at: string; status: string; coverage: string };
const repairStages = ["intake", "diagnosis", "assigned", "waiting_parts", "repairing", "completed", "collected"];

export default function AftersalesPage() {
  const { organizationId } = useOrganization();
  const [repairs, setRepairs] = useState<Repair[]>([]);
  const [warranties, setWarranties] = useState<Warranty[]>([]);
  const [loading, setLoading] = useState(true);
  const [busyId, setBusyId] = useState("");
  const [deviceFilter, setDeviceFilter] = useState("");
  const [error, setError] = useState("");
  const load = useCallback(async () => {
    if (!organizationId) return;
    setLoading(true); setError("");
    const [repairResult, warrantyResult] = await Promise.allSettled([
      apiGet<Repair[]>(`/aftersales/repairs?organization_id=${organizationId}`),
      apiGet<Warranty[]>(`/aftersales/warranties?organization_id=${organizationId}`),
    ]);
    if (repairResult.status === "fulfilled") setRepairs(repairResult.value);
    else setError(repairResult.reason instanceof Error ? repairResult.reason.message : "Repair cases could not be loaded.");
    if (warrantyResult.status === "fulfilled") setWarranties(warrantyResult.value);
    else setError((current) => current || (warrantyResult.reason instanceof Error ? warrantyResult.reason.message : "Warranties could not be loaded."));
    setLoading(false);
  }, [organizationId]);
  useEffect(() => { queueMicrotask(() => void load()); }, [load]);
  async function focusScannedDevice(result: ScanResult) {
    if (!organizationId) return;
    try {
      const rows = await apiGet<Array<{ id: string; imei?: string | null; imei_2?: string | null; serial_number?: string | null; barcode?: string | null }>>(`/devices/search?organization_id=${organizationId}&q=${encodeURIComponent(result.normalizedValue)}`);
      const match = rows.find((device) => [device.imei, device.imei_2, device.serial_number, device.barcode].some((value) => value?.trim().toUpperCase() === result.normalizedValue));
      if (!match) {
        setError("No registered device matches this identifier.");
        return;
      }
      setError("");
      setDeviceFilter(match.id);
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : "The scanned device could not be resolved.");
    }
  }
  async function advance(caseItem: Repair) {
    if (!organizationId) return;
    const next = repairStages[repairStages.indexOf(caseItem.status) + 1];
    if (!next) return;
    setBusyId(caseItem.id); setError("");
    try { await apiPatch(`/aftersales/repairs/${caseItem.id}?organization_id=${organizationId}`, { status: next }); await load(); }
    catch (e) { setError(e instanceof Error ? e.message : "Repair status could not be updated."); }
    finally { setBusyId(""); }
  }
  return <div className="space-y-6">
    <PageHeader eyebrow="Customers" title="Warranty & repairs" description="Track warranty coverage and move service cases through their recorded lifecycle." action={{ label: "Refresh", onClick: () => void load() }} />
    <section className="rounded-2xl border border-[var(--border)] bg-white p-5"><div className="flex items-center justify-between gap-3"><div><h2 className="font-semibold">Find device service history</h2><p className="mt-1 text-xs text-neutral-500">Scan an IMEI, serial number or barcode to filter warranty and repair records.</p></div>{deviceFilter && <button type="button" onClick={() => setDeviceFilter("")} className="min-h-10 rounded-lg border px-3 text-sm">Clear filter</button>}</div><CameraScanner expectation="device" onDetected={focusScannedDevice} /></section>
    {error && <div role="alert" className="rounded-xl bg-red-50 p-4 text-sm text-red-800">{error} <button onClick={() => void load()} className="ml-2 underline">Retry</button></div>}
    <section className="rounded-2xl border border-[var(--border)] bg-white p-5"><h2 className="font-semibold">Repair cases <span className="ml-2 text-sm font-normal text-neutral-500">{repairs.filter((item) => !deviceFilter || item.device_id === deviceFilter).length}</span></h2>{loading ? <p className="py-6 text-sm text-neutral-500">Loading cases…</p> : repairs.filter((item) => !deviceFilter || item.device_id === deviceFilter).length === 0 ? <p className="py-6 text-sm text-neutral-500">No matching repair cases recorded.</p> : <div className="mt-3 overflow-x-auto"><table className="w-full min-w-[720px] text-left text-sm"><thead className="text-xs text-neutral-500"><tr><th className="p-3">Reference</th><th className="p-3">Customer</th><th className="p-3">Device</th><th className="p-3">Status</th><th className="p-3">Opened</th><th className="p-3">Action</th></tr></thead><tbody>{repairs.filter((item) => !deviceFilter || item.device_id === deviceFilter).map((item) => <tr key={item.id} className="border-t"><td className="p-3 font-semibold">{item.reference_number}</td><td className="p-3 font-mono text-xs">{item.customer_id.slice(0, 8)}</td><td className="p-3 font-mono text-xs">{item.device_id.slice(0, 8)}</td><td className="p-3 capitalize">{item.status.replaceAll("_", " ")}</td><td className="p-3">{new Date(item.created_at).toLocaleDateString()}</td><td className="p-3">{item.status !== "collected" && <button disabled={busyId === item.id} onClick={() => void advance(item)} className="min-h-9 rounded-lg border px-3 text-xs font-semibold disabled:opacity-50">{busyId === item.id ? "Saving…" : `Advance to ${repairStages[repairStages.indexOf(item.status) + 1]?.replaceAll("_", " ")}`}</button>}</td></tr>)}</tbody></table></div>}</section>
    <section className="rounded-2xl border border-[var(--border)] bg-white p-5"><h2 className="font-semibold">Warranty register <span className="ml-2 text-sm font-normal text-neutral-500">{warranties.filter((item) => !deviceFilter || item.device_id === deviceFilter).length}</span></h2>{loading ? <p className="py-6 text-sm text-neutral-500">Loading warranties…</p> : warranties.filter((item) => !deviceFilter || item.device_id === deviceFilter).length === 0 ? <p className="py-6 text-sm text-neutral-500">No matching warranties recorded.</p> : <div className="mt-3 overflow-x-auto"><table className="w-full min-w-[650px] text-left text-sm"><thead className="text-xs text-neutral-500"><tr><th className="p-3">Device</th><th className="p-3">Customer</th><th className="p-3">Coverage</th><th className="p-3">Period</th><th className="p-3">Status</th></tr></thead><tbody>{warranties.filter((item) => !deviceFilter || item.device_id === deviceFilter).map((item) => <tr key={item.id} className="border-t"><td className="p-3 font-mono text-xs">{item.device_id.slice(0, 8)}</td><td className="p-3 font-mono text-xs">{item.customer_id?.slice(0, 8) || "—"}</td><td className="p-3">{item.coverage}</td><td className="p-3">{item.starts_at} – {item.ends_at}</td><td className="p-3 capitalize">{item.status}</td></tr>)}</tbody></table></div>}</section>
  </div>;
}

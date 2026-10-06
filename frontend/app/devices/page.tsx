"use client";

import { FormEvent, useState } from "react";
import { AppShell } from "@/components/app-shell";
import { PageHeader } from "@/components/page-header";
import { apiGet, ApiError } from "@/lib/api";
import { useOrganization } from "@/components/organization-provider";
import { CameraScanner } from "@/components/camera-scanner";

type Device = {
  id: string;
  organization_id: string;
  product_id?: string | null;
  imei?: string | null;
  imei_2?: string | null;
  serial_number?: string | null;
  barcode?: string | null;
  brand?: string | null;
  model?: string | null;
  variant?: string | null;
  storage?: string | null;
  color?: string | null;
  source_type?: string | null;
  source_name?: string | null;
  condition?: string | null;
  status?: string | null;
  grade?: string | null;
  ram?: string | null;
  network_sim?: string | null;
  acquisition_cost?: number | string | null;
  selling_price?: number | string | null;
  warranty?: string | null;
  location_id?: string | null;
  notes?: string | null;
  created_at?: string;
};
type DeviceEvent = { occurred_at: string; event: string; status?: string | null; reference?: string | null; supplier?: string | null; location_id?: string | null; actor?: string | null; customer?: string | null };
type WarrantyLookup = { current_status: string; sales: { reference_number: string; purchase_date: string; seller?: string | null; customer?: string | null; warranty: { starts_at: string; ends_at: string; status: string }[] }[]; warranties: { starts_at: string; ends_at: string; status: string }[]; repairs: { reference_number: string; status: string }[]; returns: { reference_number: string; status: string }[] };

export default function DevicesPage() {
  const { organizationId } = useOrganization();

  const [query, setQuery] = useState("");
  const [identifierType, setIdentifierType] = useState<"imei" | "serial" | "barcode" | "model">("imei");
  const [device, setDevice] = useState<Device | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [history, setHistory] = useState<DeviceEvent[]>([]);
  const [historyError, setHistoryError] = useState("");
  const [lifecycle, setLifecycle] = useState<WarrantyLookup | null>(null);
  const [lifecycleError, setLifecycleError] = useState("");

  async function lookupValue(rawValue: string) {
    if (!organizationId || !rawValue.trim()) return;

    setLoading(true);
    setError("");
    setDevice(null);
    setHistory([]); setHistoryError("");
    setLifecycle(null); setLifecycleError("");

    const raw = rawValue.trim();
    const value = encodeURIComponent(raw);

    try {
      let result: Device;

      if (identifierType === "imei") {
        result = await apiGet<Device>(
          `/devices/lookup/imei/${value}?organization_id=${organizationId}`
        );
      } else if (identifierType === "model") {
        const matches = await apiGet<Device[]>(`/devices/search?organization_id=${organizationId}&q=${value}`);
        if (!matches.length) throw new ApiError("No devices match that model or identifier.", 404);
        result = matches[0];
      } else {
        result = await apiGet<Device>(
          `/devices/lookup/${identifierType}/${value}?organization_id=${organizationId}`
        );
      }

      setDevice(result);
      try { setHistory(await apiGet<DeviceEvent[]>(`/devices/${result.id}/history?organization_id=${organizationId}`)); }
      catch (cause) { setHistoryError(cause instanceof Error ? cause.message : "Device lifecycle could not be loaded."); }
      const lifecycleIdentifier = encodeURIComponent(result.imei || result.serial_number || result.barcode || raw);
      try { setLifecycle(await apiGet<WarrantyLookup>(`/aftersales/warranty-lookup?organization_id=${organizationId}&identifier=${lifecycleIdentifier}`)); }
      catch (cause) { setLifecycleError(cause instanceof Error ? cause.message : "Warranty details could not be loaded."); }
    } catch (err) {
      setError(
        err instanceof ApiError
          ? err.message
          : "Device could not be found."
      );
    } finally {
      setLoading(false);
    }
  }

  function lookup(event: FormEvent) {
    event.preventDefault();
    void lookupValue(query);
  }

  return (
    <AppShell>
      <PageHeader
        eyebrow="Catalogue · Registry"
        title="Device Registry"
        description="Identifier-level visibility for serialized devices from intake through sale."
      />

      <div className="grid gap-5 xl:grid-cols-[1fr_380px]">
        <section className="rounded-2xl border border-[var(--border)] bg-[var(--surface)] shadow-sm p-5">
          <form onSubmit={lookup} className="flex gap-2">
            <label className="sr-only" htmlFor="identifier-type">Identifier type</label>
            <select id="identifier-type" value={identifierType} onChange={(event) => setIdentifierType(event.target.value as typeof identifierType)} className="h-12 rounded-xl border border-[var(--border)] bg-white px-3 text-sm">
              <option value="imei">IMEI</option><option value="serial">Serial</option><option value="barcode">Barcode</option><option value="model">Model</option>
            </select>
            <input
              value={query}
              onChange={(event) => setQuery(event.target.value)}
                placeholder={`Enter ${identifierType === "imei" ? "IMEI" : identifierType === "model" ? "model or identifier" : identifierType}`}
              className="h-12 min-w-0 flex-1 rounded-xl border border-[var(--border)] px-4 text-sm outline-none focus:border-neutral-900"
            />

            <button
              type="submit"
              disabled={loading || !query.trim()}
              className="rounded-xl bg-neutral-900 px-5 text-sm font-semibold text-white disabled:opacity-50"
            >
              {loading ? "Searching…" : "Lookup"}
            </button>
          </form>

          <CameraScanner
            expectation={identifierType === "imei" || identifierType === "serial" || identifierType === "barcode" ? identifierType : "auto"}
            onDetected={(result) => { setQuery(result.normalizedValue); return lookupValue(result.normalizedValue); }}
          />

          {error && (
            <div className="mt-5 rounded-xl border border-red-200 bg-red-50 p-4 text-sm text-red-700">
              {error}
            </div>
          )}

          {!device && !error && (
            <div className="py-20 text-center">
              <p className="text-sm font-semibold">
                Search the device registry
              </p>
              <p className="mt-1 text-xs text-[var(--muted)]">
                Choose an identifier type, enter its value or scan a device barcode.
              </p>
            </div>
          )}

          {device && (
            <div className="mt-6">
              <div className="rounded-2xl bg-neutral-50 p-5">
                <div className="flex items-start justify-between gap-4">
                  <div>
                    <p className="text-xs text-[var(--muted)]">Device</p>
                    <h2 className="mt-1 text-lg font-semibold">
                      {device.brand || "Unknown"}{" "}
                      {device.model || "Device"}
                    </h2>
                  </div>

                  <span className="rounded-full bg-white px-3 py-1 text-xs font-semibold">
                    {device.status || "Unknown"}
                  </span>
                </div>

                <div className="mt-6 grid gap-4 sm:grid-cols-2">
                  <Detail label="IMEI" value={device.imei} />
                  <Detail label="IMEI 2" value={device.imei_2} />
                  <Detail label="Serial" value={device.serial_number} />
                  <Detail label="Barcode" value={device.barcode} />
                  <Detail label="Variant" value={device.variant} />
                  <Detail label="Storage" value={device.storage} />
                  <Detail label="Color" value={device.color} />
                  <Detail label="Condition" value={device.condition} />
                  <Detail label="Grade" value={device.grade} />
                  <Detail label="RAM" value={device.ram} />
                  <Detail label="Network / SIM" value={device.network_sim} />
                  <Detail label="Source" value={device.source_name || device.source_type} />
                  <Detail label="Received cost" value={device.acquisition_cost == null ? null : String(device.acquisition_cost)} />
                  <Detail label="Selling price" value={device.selling_price == null ? null : String(device.selling_price)} />
                  <Detail label="Warranty" value={device.warranty} />
                  <Detail label="Store / location" value={device.location_id} />
                  <Detail label="Notes" value={device.notes} />
                  <Detail label="Received date" value={device.created_at} />
                </div>
              </div>
              <section className="mt-4 rounded-2xl border border-[var(--border)] p-5"><h3 className="font-semibold">Lifecycle history</h3>{historyError ? <p role="alert" className="mt-3 text-sm text-red-700">{historyError}</p> : history.length ? <ol className="mt-3 space-y-3">{history.map((event, index) => <li key={`${event.event}-${event.occurred_at}-${index}`} className="border-l-2 border-neutral-200 pl-4"><p className="text-sm font-semibold capitalize">{event.event}{event.status ? ` · ${event.status}` : ""}</p><p className="text-xs text-neutral-500">{new Date(event.occurred_at).toLocaleString()} {[event.reference, event.supplier && `Supplier: ${event.supplier}`, event.customer && `Customer: ${event.customer}`, event.actor && `Actor: ${event.actor}`, event.location_id && `Location: ${event.location_id}`].filter(Boolean).join(" · ")}</p></li>)}</ol> : <p className="mt-3 text-sm text-neutral-500">No lifecycle events have been recorded.</p>}</section>
              <section className="mt-4 rounded-2xl border border-[var(--border)] p-5"><h3 className="font-semibold">Warranty and customer lifecycle</h3>{lifecycleError ? <p role="alert" className="mt-3 text-sm text-red-700">{lifecycleError}</p> : lifecycle ? <div className="mt-3 space-y-3 text-sm"><p>Current device status: <strong>{lifecycle.current_status}</strong></p>{lifecycle.sales.map((sale) => <div key={sale.reference_number} className="rounded-xl bg-neutral-50 p-3"><p className="font-semibold">Sale {sale.reference_number} · {new Date(sale.purchase_date).toLocaleDateString()}</p><p className="mt-1 text-xs text-neutral-600">{sale.seller ? `Seller: ${sale.seller} · ` : ""}{sale.customer ? `Customer: ${sale.customer}` : "Customer details require customer permission"}</p></div>)}<p>Warranties: {lifecycle.warranties.length ? lifecycle.warranties.map((warranty) => `${warranty.status}, ${warranty.starts_at} to ${warranty.ends_at}`).join(" · ") : "none recorded"}</p><p>Repairs: {lifecycle.repairs.length ? lifecycle.repairs.map((repair) => `${repair.reference_number} (${repair.status})`).join(" · ") : "none"}</p><p>Returns: {lifecycle.returns.length ? lifecycle.returns.map((record) => `${record.reference_number} (${record.status})`).join(" · ") : "none"}</p></div> : <p className="mt-3 text-sm text-neutral-500">Searching warranty records…</p>}</section>
            </div>
          )}
        </section>

        <aside className="rounded-2xl border border-[var(--border)] bg-[var(--surface)] shadow-sm p-5">
          <p className="text-sm font-semibold">Registry controls</p>

          <div className="mt-5 space-y-3">
            <div className="rounded-xl border border-[var(--border)] p-4">
              <p className="text-xs font-semibold">IMEI lookup</p>
              <p className="mt-1 text-xs text-[var(--muted)]">
                Find a serialized device using its primary IMEI.
              </p>
            </div>

            <div className="rounded-xl border border-[var(--border)] p-4">
              <p className="text-xs font-semibold">Serial lookup</p>
              <p className="mt-1 text-xs text-[var(--muted)]">
                Resolve devices using manufacturer serial numbers.
              </p>
            </div>

            <div className="rounded-xl border border-[var(--border)] p-4">
              <p className="text-xs font-semibold">Barcode lookup</p>
              <p className="mt-1 text-xs text-[var(--muted)]">
                Works with store barcodes and scanner input.
              </p>
            </div>
          </div>
        </aside>
      </div>
    </AppShell>
  );
}

function Detail({
  label,
  value,
}: {
  label: string;
  value?: string | null;
}) {
  return (
    <div>
      <p className="text-[11px] font-medium text-[var(--muted)]">{label}</p>
      <p className="mt-1 text-sm font-medium">{value || "—"}</p>
    </div>
  );
}

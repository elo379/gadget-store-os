"use client";

import { FormEvent, useState } from "react";
import { AppShell } from "@/components/app-shell";
import { PageHeader } from "@/components/page-header";
import { apiGet, ApiError } from "@/lib/api";
import { useOrganization } from "@/components/organization-provider";

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
};

export default function DevicesPage() {
  const { organizationId } = useOrganization();

  const [query, setQuery] = useState("");
  const [device, setDevice] = useState<Device | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  async function lookup(event: FormEvent) {
    event.preventDefault();

    if (!organizationId || !query.trim()) return;

    setLoading(true);
    setError("");
    setDevice(null);

    const value = encodeURIComponent(query.trim());

    try {
      let result: Device;

      if (/^\d{14,16}$/.test(query.trim())) {
        result = await apiGet<Device>(
          `/devices/lookup/imei/${value}?organization_id=${organizationId}`
        );
      } else if (query.includes("-") || query.length >= 8) {
        try {
          result = await apiGet<Device>(
            `/devices/lookup/serial/${value}?organization_id=${organizationId}`
          );
        } catch {
          result = await apiGet<Device>(
            `/devices/lookup/barcode/${value}?organization_id=${organizationId}`
          );
        }
      } else {
        result = await apiGet<Device>(
          `/devices/lookup/barcode/${value}?organization_id=${organizationId}`
        );
      }

      setDevice(result);
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

  return (
    <AppShell>
      <PageHeader
        eyebrow="Device registry"
        title="Devices & IMEI"
        description="Identifier-level visibility for serialized devices from intake through sale."
      />

      <div className="grid gap-5 xl:grid-cols-[1fr_380px]">
        <section className="rounded-2xl border border-[var(--border)] bg-[var(--surface)] shadow-sm p-5">
          <form onSubmit={lookup} className="flex gap-2">
            <input
              value={query}
              onChange={(event) => setQuery(event.target.value)}
              placeholder="IMEI, serial number or barcode"
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
                Enter an IMEI, serial number or barcode.
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
                  <Detail label="Source" value={device.source_name || device.source_type} />
                </div>
              </div>
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

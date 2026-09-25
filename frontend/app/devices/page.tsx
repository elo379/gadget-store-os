import { AppShell } from "@/components/app-shell";
import { DataTable } from "@/components/data-table";
import { PageHeader } from "@/components/page-header";

export default function DevicesPage() {
  return (
    <AppShell>
      <PageHeader eyebrow="Device registry" title="Devices & IMEI"
        description="Track serialized devices from intake through sale with identifier-level visibility."
        action={{ label: "Scan IMEI", icon: "scan" }} />

      <div className="mb-5 flex h-11 items-center gap-3 rounded-xl border border-[var(--border)] bg-white px-3 text-sm text-neutral-400">
        <span>⌕</span>
        Search IMEI, serial number or barcode...
      </div>

      <DataTable
        columns={[
          { label: "IMEI", key: "imei" },
          { label: "Product", key: "product" },
          { label: "Serial", key: "serial" },
          { label: "Source", key: "source" },
          { label: "Status", key: "status" },
        ]}
        rows={[
          { imei: "356789102345671", product: "iPhone 15 Pro", serial: "F2L9X8A01", source: "Supplier", status: "Available" },
          { imei: "356789102345689", product: "iPhone 15 Pro", serial: "F2L9X8A14", source: "Supplier", status: "Sold" },
          { imei: "356789102345697", product: "Samsung Galaxy S24", serial: "R5CT91ABC", source: "Supplier", status: "Available" },
        ]}
      />
    </AppShell>
  );
}

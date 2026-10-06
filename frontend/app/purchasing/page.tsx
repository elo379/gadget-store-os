"use client";

import { useEffect, useState, type FormEvent } from "react";
import { apiGet, apiPost } from "@/lib/api";
import { useOrganization } from "@/components/organization-provider";
import { CameraScanner } from "@/components/camera-scanner";
import type { ScanExpectation, ScanResult } from "@/lib/scanner";

type Supplier = {
  id: string;
  name: string;
  phone?: string;
  email?: string;
  address?: string;
  lead_time_days?: number | null;
};

type Purchase = {
  id: string;
  supplier_id?: string;
  status?: string;
  total?: number | string;
  notes?: string;
  created_at?: string;
  reference_number?: string;
  lines?: { id: string; product_id: string; quantity: number | string; received_quantity: number | string; unit_cost: number | string }[];
};
type Product = { id: string; name: string; sku: string | null; is_serialized: boolean; brand: string; model: string };
type Location = { id: string; name: string };

export default function PurchasingPage() {
  const { organizationId } = useOrganization();
  const [suppliers, setSuppliers] = useState<Supplier[]>([]);
  const [orders, setOrders] = useState<Purchase[]>([]);
  const [supplierName, setSupplierName] = useState("");
  const [supplierPhone, setSupplierPhone] = useState("");
  const [supplierLeadTime, setSupplierLeadTime] = useState("");
  const [busy, setBusy] = useState(false);
  const [message, setMessage] = useState("");
  const [loadError, setLoadError] = useState("");
  const [products, setProducts] = useState<Product[]>([]);
  const [locations, setLocations] = useState<Location[]>([]);
  const [supplierId, setSupplierId] = useState("");
  const [productId, setProductId] = useState("");
  const [quantity, setQuantity] = useState("1");
  const [unitCost, setUnitCost] = useState("");
  const [orderReference, setOrderReference] = useState("");
  const [receiving, setReceiving] = useState<Purchase | null>(null);
  const [receiveLocation, setReceiveLocation] = useState("");
  const [deviceIdentity, setDeviceIdentity] = useState({ imei: "", imei_2: "", serial_number: "", barcode: "", storage: "", ram: "", color: "", network_sim: "", grade: "", warranty: "", selling_price: "", condition: "new", notes: "" });
  const [deviceScanExpectation, setDeviceScanExpectation] = useState<ScanExpectation>("device");

  async function load() {
    if (!organizationId) return;
    setLoadError("");

    const [supplierResult, orderResult, productResult, locationResult] = await Promise.allSettled([
      apiGet<Supplier[]>(
        `/suppliers?organization_id=${organizationId}`,
      ),
      apiGet<Purchase[]>(
        `/purchasing/orders?organization_id=${organizationId}`,
      ),
      apiGet<Product[]>(`/products?organization_id=${organizationId}`),
      apiGet<Location[]>(`/inventory/locations?organization_id=${organizationId}`),
    ]);

    if (supplierResult.status === "fulfilled") {
      setSuppliers(Array.isArray(supplierResult.value) ? supplierResult.value : []);
    }

    if (orderResult.status === "fulfilled") {
      setOrders(Array.isArray(orderResult.value) ? orderResult.value : []);
    }
    if (productResult.status === "fulfilled") setProducts(productResult.value);
    if (locationResult.status === "fulfilled") setLocations(locationResult.value);
    const failures = [supplierResult, orderResult, productResult, locationResult].filter((result) => result.status === "rejected");
    if (failures.length) setLoadError("Some purchasing data could not be loaded. " + failures.map((result) => result.status === "rejected" && result.reason instanceof Error ? result.reason.message : "Request failed").join(" · "));
  }

  async function createOrder(event: FormEvent) {
    event.preventDefault();
    if (!organizationId || !supplierId || !productId) return;
    setBusy(true); setMessage("");
    try {
      const created = await apiPost<Purchase>("/purchasing/orders", { organization_id: organizationId, supplier_id: supplierId, reference_number: orderReference.trim(), lines: [{ product_id: productId, quantity, unit_cost: unitCost }] });
      setOrderReference(""); setMessage(`Purchase order ${created.reference_number ?? created.id} created.`); await load();
    } catch (error) { setMessage(error instanceof Error ? error.message : "Purchase order could not be created."); }
    finally { setBusy(false); }
  }

  async function receiveOrder(event: FormEvent) {
    event.preventDefault();
    if (!organizationId || !receiving?.lines?.length) return;
    const line = receiving.lines.find((item) => Number(item.received_quantity) < Number(item.quantity));
    if (!line) { setMessage("This order has no outstanding quantities."); return; }
    const product = products.find((item) => item.id === line.product_id);
    const serialized = Boolean(product?.is_serialized);
    const remaining = Number(line.quantity) - Number(line.received_quantity);
    if (serialized && !deviceIdentity.imei && !deviceIdentity.serial_number && !deviceIdentity.barcode) { setMessage("Enter an IMEI, serial number or barcode for this device."); return; }
    setBusy(true); setMessage("");
    try {
      await apiPost("/purchasing/receive", { organization_id: organizationId, lines: [{ purchase_line_id: line.id, quantity: serialized ? 1 : remaining, location_id: receiveLocation || null, ...(serialized ? deviceIdentity : {}) }] });
      setReceiving(null); setDeviceIdentity({ imei: "", imei_2: "", serial_number: "", barcode: "", storage: "", ram: "", color: "", network_sim: "", grade: "", warranty: "", selling_price: "", condition: "new", notes: "" }); setDeviceScanExpectation("device");
      setMessage("Receipt recorded. Stock, device identity and supplier balance were updated."); await load();
    } catch (error) { setMessage(error instanceof Error ? error.message : "Stock could not be received."); }
    finally { setBusy(false); }
  }

  function applyReceivedDeviceScan(result: ScanResult) {
    const value = result.normalizedValue;
    setDeviceIdentity((current) => {
      if (result.type === "imei") {
        if (!current.imei) return { ...current, imei: value };
        if (!current.imei_2) return { ...current, imei_2: value };
        return current;
      }
      if (result.type === "barcode" || result.type === "qr") return { ...current, barcode: value };
      return { ...current, serial_number: value };
    });
  }

  useEffect(() => {
    queueMicrotask(() => void load());
  }, [organizationId]);

  async function createSupplier() {
    if (!organizationId || !supplierName.trim()) return;

    setBusy(true);
    setMessage("");

    try {
      await apiPost("/suppliers", {
        organization_id: organizationId,
        name: supplierName.trim(),
        phone: supplierPhone.trim(),
        lead_time_days: supplierLeadTime.trim() ? Number(supplierLeadTime) : null,
      });

      setSupplierName("");
      setSupplierPhone("");
      setSupplierLeadTime("");
      setMessage("Supplier created.");
      await load();
    } catch (error) {
      setMessage(error instanceof Error ? error.message : "Unable to create supplier.");
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="space-y-6">
      <header className="flex flex-col gap-4 sm:flex-row sm:items-end sm:justify-between">
        <div>
          <p className="text-sm font-medium text-[var(--muted)]">Procurement</p>
          <h1 className="text-3xl font-semibold tracking-tight">Purchasing</h1>
          <p className="mt-1 text-sm text-[var(--muted)]">
            Suppliers, purchase orders and receiving workflows.
          </p>
        </div>
        <button onClick={() => void load()} className="rounded-xl border px-4 py-3">
          Refresh
        </button>
      </header>

      <div className="grid gap-4 md:grid-cols-3">
        <div className="rounded-2xl border border-[var(--border)] bg-[var(--surface)] shadow-sm p-5">
          <p className="text-sm text-[var(--muted)]">Suppliers</p>
          <p className="mt-2 text-3xl font-semibold">{suppliers.length}</p>
        </div>
        <div className="rounded-2xl border border-[var(--border)] bg-[var(--surface)] shadow-sm p-5">
          <p className="text-sm text-[var(--muted)]">Purchase orders</p>
          <p className="mt-2 text-3xl font-semibold">{orders.length}</p>
        </div>
        <div className="rounded-2xl border border-[var(--border)] bg-[var(--surface)] shadow-sm p-5">
          <p className="text-sm text-[var(--muted)]">Open orders</p>
          <p className="mt-2 text-3xl font-semibold">
            {orders.filter((order) => order.status !== "completed").length}
          </p>
        </div>
      </div>
      {loadError && <p role="alert" className="rounded-xl bg-red-50 p-3 text-sm text-red-800">{loadError}<button type="button" onClick={() => void load()} className="ml-3 underline">Retry</button></p>}

      <section className="rounded-2xl border border-[var(--border)] bg-[var(--surface)] shadow-sm p-5">
        <h2 className="font-semibold">Add supplier</h2>
        <div className="mt-4 grid gap-3 sm:grid-cols-2 xl:grid-cols-[1fr_1fr_180px_auto]">
          <input
            value={supplierName}
            onChange={(e) => setSupplierName(e.target.value)}
            placeholder="Supplier name"
            className="rounded-xl border px-4 py-3"
          />
          <input
            value={supplierPhone}
            onChange={(e) => setSupplierPhone(e.target.value)}
            placeholder="Phone"
            className="rounded-xl border px-4 py-3"
          />
          <label className="text-xs font-semibold">Supplier lead time in days<input type="number" min="0" max="365" step="1" value={supplierLeadTime} onChange={(event) => setSupplierLeadTime(event.target.value)} placeholder="Optional" className="mt-1 w-full rounded-xl border px-4 py-3 text-sm font-normal" /></label>
          <button
            onClick={() => void createSupplier()}
            disabled={busy}
            className="rounded-xl bg-black px-5 py-3 text-white disabled:opacity-50"
          >
            {busy ? "Saving..." : "Add supplier"}
          </button>
        </div>
        {message && <p className="mt-3 text-sm text-[var(--muted)]">{message}</p>}
      </section>

      <form onSubmit={createOrder} className="space-y-4 rounded-2xl border border-[var(--border)] bg-[var(--surface)] p-5"><div><h2 className="font-semibold">Create purchase order</h2><p className="mt-1 text-sm text-[var(--muted)]">Purchase costs and quantities are captured per order line.</p></div><div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-5"><label className="text-xs font-semibold">Supplier<select required value={supplierId} onChange={(e) => setSupplierId(e.target.value)} className="mt-1 h-11 w-full rounded-lg border bg-white px-3 text-sm font-normal"><option value="">Select supplier</option>{suppliers.map((item) => <option key={item.id} value={item.id}>{item.name}</option>)}</select></label><label className="text-xs font-semibold">Product<select required value={productId} onChange={(e) => setProductId(e.target.value)} className="mt-1 h-11 w-full rounded-lg border bg-white px-3 text-sm font-normal"><option value="">Select product</option>{products.map((item) => <option key={item.id} value={item.id}>{item.name}{item.is_serialized ? " · serialized" : item.sku ? ` · ${item.sku}` : ""}</option>)}</select></label><label className="text-xs font-semibold">Quantity<input required min="0.001" step="0.001" type="number" value={quantity} onChange={(e) => setQuantity(e.target.value)} className="mt-1 h-11 w-full rounded-lg border px-3 text-sm font-normal" /></label><label className="text-xs font-semibold">Unit cost<input required min="0.01" step="0.01" type="number" value={unitCost} onChange={(e) => setUnitCost(e.target.value)} className="mt-1 h-11 w-full rounded-lg border px-3 text-sm font-normal" /></label><label className="text-xs font-semibold">PO reference<input required value={orderReference} onChange={(e) => setOrderReference(e.target.value)} className="mt-1 h-11 w-full rounded-lg border px-3 text-sm font-normal" /></label></div><button disabled={busy || !suppliers.length || !products.length} className="min-h-11 rounded-xl bg-neutral-950 px-5 text-sm font-semibold text-white disabled:opacity-50">{busy ? "Saving…" : "Create purchase order"}</button></form>

      <section className="rounded-2xl border border-[var(--border)] bg-[var(--surface)] shadow-sm p-5">
        <h2 className="font-semibold">Purchase orders</h2>
        <div className="mt-4 overflow-x-auto">
          <table className="w-full text-left text-sm">
            <thead>
              <tr className="border-b text-[var(--muted)]">
                <th className="px-3 py-3">Order</th>
                <th className="px-3 py-3">Supplier</th>
                <th className="px-3 py-3">Status</th>
                <th className="px-3 py-3">Total</th>
                <th className="px-3 py-3">Receipt</th>
              </tr>
            </thead>
            <tbody>
              {orders.map((order) => {
                const supplier = suppliers.find((item) => item.id === order.supplier_id);
                return (
                  <tr key={order.id} className="border-b last:border-0">
                    <td className="px-3 py-4 font-medium">{order.id.slice(0, 8)}</td>
                    <td className="px-3 py-4">{supplier?.name || "—"}{supplier?.lead_time_days != null ? <span className="block text-xs text-neutral-500">{supplier.lead_time_days} day lead time</span> : null}</td>
                    <td className="px-3 py-4">{order.status || "Draft"}</td>
                    <td className="px-3 py-4">
                      ₦{Number(order.total ?? 0).toLocaleString()}
                    </td>
                    <td className="px-3 py-4">{order.status !== "received" && <button type="button" disabled={busy} onClick={() => { setReceiving(order); setReceiveLocation(""); }} className="rounded-lg border px-3 py-2 text-xs font-semibold">Receive stock</button>}</td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </section>
      {receiving && <div role="presentation" className="fixed inset-0 z-50 flex items-end justify-center bg-black/40 sm:items-center sm:p-4" onMouseDown={(event) => { if (event.target === event.currentTarget) setReceiving(null); }}><form onSubmit={receiveOrder} className="max-h-[92vh] w-full max-w-2xl space-y-3 overflow-y-auto rounded-t-2xl bg-white p-5 sm:rounded-2xl"><div className="flex justify-between"><div><h2 className="text-lg font-semibold">Receive {receiving.reference_number}</h2><p className="text-sm text-neutral-500">Serialized units are received one at a time with their own identifiers.</p></div><button type="button" onClick={() => setReceiving(null)} className="h-10 w-10 rounded-lg border">×</button></div><label className="block text-sm font-medium">Store / location<select value={receiveLocation} onChange={(e) => setReceiveLocation(e.target.value)} className="mt-1 h-11 w-full rounded-lg border bg-white px-3"><option value="">Unassigned location</option>{locations.map((location) => <option key={location.id} value={location.id}>{location.name}</option>)}</select></label>{products.find((item) => item.id === receiving.lines?.find((line) => Number(line.received_quantity) < Number(line.quantity))?.product_id)?.is_serialized && <><p className="text-sm font-semibold">Device identity and configuration</p><label className="block text-sm">Identifier type<select value={deviceScanExpectation} onChange={(event) => setDeviceScanExpectation(event.target.value as ScanExpectation)} className="mt-1 h-11 w-full rounded-lg border bg-white px-3"><option value="device">IMEI / device identifier</option><option value="serial">Serial number</option><option value="barcode">Barcode / QR</option></select></label><CameraScanner expectation={deviceScanExpectation} onDetected={applyReceivedDeviceScan} /><div className="grid gap-3 sm:grid-cols-2">{([["IMEI", "imei"], ["IMEI 2", "imei_2"], ["Serial number", "serial_number"], ["Barcode", "barcode"], ["Storage", "storage"], ["RAM", "ram"], ["Color", "color"], ["Network / SIM", "network_sim"], ["Grade", "grade"], ["Warranty", "warranty"], ["Selling price", "selling_price"], ["Condition", "condition"]] as const).map(([label, key]) => <label key={key} className="text-sm font-medium">{label}<input required={key === "imei" || key === "serial_number" || key === "barcode" ? !deviceIdentity.imei && !deviceIdentity.serial_number && !deviceIdentity.barcode : false} type={key === "selling_price" ? "number" : "text"} min={key === "selling_price" ? "0" : undefined} step={key === "selling_price" ? "0.01" : undefined} value={deviceIdentity[key]} onChange={(e) => setDeviceIdentity((value) => ({ ...value, [key]: e.target.value }))} className="mt-1 h-11 w-full rounded-lg border px-3 font-normal" /></label>)}</div></>}<label className="block text-sm font-medium">Notes<textarea value={deviceIdentity.notes} onChange={(e) => setDeviceIdentity((value) => ({ ...value, notes: e.target.value }))} className="mt-1 w-full rounded-lg border p-3 font-normal" /></label><div className="flex justify-end gap-2"><button type="button" onClick={() => setReceiving(null)} className="min-h-11 rounded-lg border px-4">Cancel</button><button disabled={busy} className="min-h-11 rounded-lg bg-neutral-950 px-4 text-white disabled:opacity-50">{busy ? "Receiving…" : "Record receipt"}</button></div></form></div>}
    </div>
  );
}

"use client";

import { useEffect, useState } from "react";
import { apiGet, apiPost } from "@/lib/api";
import { useOrganization } from "@/components/organization-provider";

type Supplier = {
  id: string;
  name: string;
  phone?: string;
  email?: string;
  address?: string;
};

type Purchase = {
  id: string;
  supplier_id?: string;
  status?: string;
  total?: number | string;
  notes?: string;
  created_at?: string;
};

export default function PurchasingPage() {
  const { organizationId } = useOrganization();
  const [suppliers, setSuppliers] = useState<Supplier[]>([]);
  const [orders, setOrders] = useState<Purchase[]>([]);
  const [supplierName, setSupplierName] = useState("");
  const [supplierPhone, setSupplierPhone] = useState("");
  const [busy, setBusy] = useState(false);
  const [message, setMessage] = useState("");

  async function load() {
    if (!organizationId) return;

    const [supplierResult, orderResult] = await Promise.allSettled([
      apiGet<Supplier[]>(
        `/suppliers?organization_id=${organizationId}`,
      ),
      apiGet<Purchase[]>(
        `/purchasing/orders?organization_id=${organizationId}`,
      ),
    ]);

    if (supplierResult.status === "fulfilled") {
      setSuppliers(Array.isArray(supplierResult.value) ? supplierResult.value : []);
    }

    if (orderResult.status === "fulfilled") {
      setOrders(Array.isArray(orderResult.value) ? orderResult.value : []);
    }
  }

  useEffect(() => {
    void load();
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
      });

      setSupplierName("");
      setSupplierPhone("");
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

      <section className="rounded-2xl border border-[var(--border)] bg-[var(--surface)] shadow-sm p-5">
        <h2 className="font-semibold">Add supplier</h2>
        <div className="mt-4 grid gap-3 md:grid-cols-[1fr_1fr_auto]">
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
              </tr>
            </thead>
            <tbody>
              {orders.map((order) => {
                const supplier = suppliers.find((item) => item.id === order.supplier_id);
                return (
                  <tr key={order.id} className="border-b last:border-0">
                    <td className="px-3 py-4 font-medium">{order.id.slice(0, 8)}</td>
                    <td className="px-3 py-4">{supplier?.name || "—"}</td>
                    <td className="px-3 py-4">{order.status || "Draft"}</td>
                    <td className="px-3 py-4">
                      ₦{Number(order.total ?? 0).toLocaleString()}
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </section>
    </div>
  );
}

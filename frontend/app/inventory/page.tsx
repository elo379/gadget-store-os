"use client";

import { FormEvent, useEffect, useState } from "react";
import { AppShell } from "@/components/app-shell";
import { PageHeader } from "@/components/page-header";
import { apiGet, apiPost, ApiError } from "@/lib/api";
import { useOrganization } from "@/components/organization-provider";

type InventoryItem = {
  id: string;
  organization_id: string;
  product_id: string;
  location_id: string | null;
  quantity: number | string;
  reserved_quantity: number | string;
  average_unit_cost: number | string;
  status: string;
};

type InventoryMovement = {
  id: string;
  movement_type: string;
  quantity: number | string;
  quantity_before?: number | string;
  quantity_after?: number | string;
  reason?: string;
  created_at?: string;
};

type Product = {
  id: string;
  name: string;
  sku: string;
};

type Location = {
  id: string;
  name: string;
};

export default function InventoryPage() {
  const { organizationId } = useOrganization();

  const [items, setItems] = useState<InventoryItem[]>([]);
  const [products, setProducts] = useState<Product[]>([]);
  const [locations, setLocations] = useState<Location[]>([]);
  const [selectedItem, setSelectedItem] = useState<InventoryItem | null>(null);
  const [movements, setMovements] = useState<InventoryMovement[]>([]);

  const [loading, setLoading] = useState(true);
  const [movementLoading, setMovementLoading] = useState(false);
  const [error, setError] = useState("");
  const [movementError, setMovementError] = useState("");

  const [movementType, setMovementType] = useState("adjustment");
  const [movementQuantity, setMovementQuantity] = useState("");
  const [movementReason, setMovementReason] = useState("");

  async function loadInventory() {
    if (!organizationId) return;

    setLoading(true);
    setError("");

    try {
      const [inventory, productList, locationList] = await Promise.all([
        apiGet<InventoryItem[]>(
          `/inventory?organization_id=${organizationId}`
        ),
        apiGet<Product[]>(
          `/products?organization_id=${organizationId}`
        ),
        apiGet<Location[]>(
          `/inventory/locations?organization_id=${organizationId}`
        ),
      ]);

      setItems(inventory);
      setProducts(productList);
      setLocations(locationList);
    } catch (err) {
      setError(
        err instanceof ApiError ? err.message : "Unable to load inventory."
      );
    } finally {
      setLoading(false);
    }
  }

  async function loadMovements(item: InventoryItem) {
    if (!organizationId) return;

    setSelectedItem(item);
    setMovementError("");

    try {
      const result = await apiGet<InventoryMovement[]>(
        `/inventory/${item.id}/movements?organization_id=${organizationId}`
      );
      setMovements(result);
    } catch (err) {
      setMovementError(
        err instanceof ApiError
          ? err.message
          : "Unable to load movement history."
      );
      setMovements([]);
    }
  }

  async function addProductToInventory(productId: string) {
    if (!organizationId || !productId) return;

    setMovementLoading(true);
    setMovementError("");

    try {
      await apiPost(
        `/inventory/items?organization_id=${organizationId}`,
        {
          product_id: productId,
          quantity: 0,
          notes: "Added from inventory workflow",
        },
      );

      await loadInventory();
    } catch (err) {
      setMovementError(
        err instanceof ApiError
          ? err.message
          : "Unable to add product to inventory.",
      );
    } finally {
      setMovementLoading(false);
    }
  }

async function submitMovement(event: FormEvent) {
    event.preventDefault();

    if (!organizationId || !selectedItem || !movementQuantity) return;

    setMovementLoading(true);
    setMovementError("");

    try {
      await apiPost(
        `/inventory/${selectedItem.id}/movements?organization_id=${organizationId}&movement_type=${encodeURIComponent(movementType)}&quantity=${encodeURIComponent(movementQuantity)}&reason=${encodeURIComponent(movementReason)}`,
        {},
      );

      setMovementQuantity("");
      setMovementReason("");
      await loadInventory();

      const refreshed = await apiGet<InventoryItem>(
        `/inventory/${selectedItem.id}?organization_id=${organizationId}`
      );

      await loadMovements(refreshed);
    } catch (err) {
      setMovementError(
        err instanceof ApiError ? err.message : "Stock movement failed."
      );
    } finally {
      setMovementLoading(false);
    }
  }

  useEffect(() => {
    void loadInventory();
  }, [organizationId]);

  const productName = (productId: string) =>
    products.find((product) => product.id === productId)?.name ?? productId;

  const locationName = (locationId: string | null) =>
    locations.find((location) => location.id === locationId)?.name ??
    "Unassigned";

  const totalUnits = items.reduce(
    (sum, item) => sum + Number(item.quantity),
    0
  );

  const reservedUnits = items.reduce(
    (sum, item) => sum + Number(item.reserved_quantity),
    0
  );

  return (
    <AppShell>
      <PageHeader
        eyebrow="Stock control"
        title="Inventory"
        description="Monitor quantities, locations, reservations and stock health."
      />

      <div className="mb-6 grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
        {[
          ["Inventory records", String(items.length)],
          ["Units on hand", String(totalUnits)],
          ["Reserved units", String(reservedUnits)],
          ["Low / inactive", String(items.filter((item) => item.status !== "active").length)],
        ].map(([label, value]) => (
          <div
            key={label}
            className="rounded-2xl border border-[var(--border)] bg-white p-5"
          >
            <p className="text-xs font-semibold text-[var(--muted)]">{label}</p>
            <p className="mt-2 text-2xl font-semibold tracking-[-0.03em]">
              {value}
            </p>
          </div>
        ))}
      </div>

      {error && (
        <div className="mb-5 rounded-xl border border-red-200 bg-red-50 p-4 text-sm text-red-700">
          {error}
        </div>
      )}

      <div className="grid gap-5 xl:grid-cols-[1fr_380px]">
        <section className="overflow-hidden rounded-2xl border border-[var(--border)] bg-white">
          <div className="border-b border-[var(--border)] px-5 py-4">
            <p className="text-sm font-semibold">Stock records</p>
            <p className="mt-1 text-xs text-[var(--muted)]">
              Select a record to inspect its movement history.
            </p>
          </div>

          {loading ? (
            <div className="p-8 text-sm text-[var(--muted)]">
              Loading inventory…
            </div>
          ) : items.length === 0 ? (
            <div className="p-8 text-center">
              <p className="text-sm font-semibold">No inventory records</p>
              <p className="mt-1 text-xs text-[var(--muted)]">
                Inventory will appear here after stock is received.
              </p>
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-left text-sm">
                <thead className="border-b border-[var(--border)] text-xs text-[var(--muted)]">
                  <tr>
                    <th className="px-5 py-3 font-medium">Product</th>
                    <th className="px-5 py-3 font-medium">Location</th>
                    <th className="px-5 py-3 font-medium">Quantity</th>
                    <th className="px-5 py-3 font-medium">Reserved</th>
                    <th className="px-5 py-3 font-medium">Status</th>
                  </tr>
                </thead>
                <tbody>
                  {items.map((item) => (
                    <tr
                      key={item.id}
                      onClick={() => void loadMovements(item)}
                      className="cursor-pointer border-b border-[var(--border)] last:border-0 hover:bg-neutral-50"
                    >
                      <td className="px-5 py-4 font-medium">
                        {productName(item.product_id)}
                      </td>
                      <td className="px-5 py-4 text-[var(--muted)]">
                        {locationName(item.location_id)}
                      </td>
                      <td className="px-5 py-4">{item.quantity}</td>
                      <td className="px-5 py-4">{item.reserved_quantity}</td>
                      <td className="px-5 py-4">
                        <span className="rounded-full bg-neutral-100 px-2.5 py-1 text-xs font-medium">
                          {item.status}
                        </span>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </section>

        <aside className="space-y-5">
          <section className="rounded-2xl border border-[var(--border)] bg-white p-5">
            <p className="text-sm font-semibold">Stock movement</p>

            {!selectedItem ? (
              <p className="mt-3 text-xs text-[var(--muted)]">
                Select an inventory record first.
              </p>
            ) : (
              <form onSubmit={submitMovement} className="mt-5 space-y-4">
                <div>
                  <p className="text-xs text-[var(--muted)]">Selected item</p>
                  <p className="mt-1 text-sm font-semibold">
                    {productName(selectedItem.product_id)}
                  </p>
                </div>

                <select
                  value={movementType}
                  onChange={(event) => setMovementType(event.target.value)}
                  className="h-11 w-full rounded-xl border border-[var(--border)] bg-white px-3 text-sm"
                >
                  <option value="adjustment">Adjustment</option>
                  <option value="receive">Receive</option>
                  <option value="sale">Sale</option>
                  <option value="damage">Damage</option>
                  <option value="loss">Loss</option>
                  <option value="return">Return</option>
                  <option value="transfer">Transfer</option>
                </select>

                <input
                  type="number"
                  min="0.001"
                  step="0.001"
                  value={movementQuantity}
                  onChange={(event) => setMovementQuantity(event.target.value)}
                  placeholder="Quantity"
                  className="h-11 w-full rounded-xl border border-[var(--border)] px-3 text-sm"
                  required
                />

                <textarea
                  value={movementReason}
                  onChange={(event) => setMovementReason(event.target.value)}
                  placeholder="Reason"
                  className="min-h-24 w-full rounded-xl border border-[var(--border)] px-3 py-3 text-sm"
                />

                {movementError && (
                  <p className="text-xs text-red-600">{movementError}</p>
                )}

                <button
                  type="submit"
                  disabled={movementLoading}
                  className="h-11 w-full rounded-xl bg-neutral-900 text-sm font-semibold text-white disabled:opacity-50"
                >
                  {movementLoading ? "Saving…" : "Record movement"}
                </button>
              </form>
            )}
          </section>

          {selectedItem && (
            <section className="rounded-2xl border border-[var(--border)] bg-white p-5">
              <p className="text-sm font-semibold">Movement history</p>

              <div className="mt-4 space-y-3">
                {movements.length === 0 ? (
                  <p className="text-xs text-[var(--muted)]">
                    No movement history.
                  </p>
                ) : (
                  movements.map((movement) => (
                    <div
                      key={movement.id}
                      className="rounded-xl bg-neutral-50 p-3"
                    >
                      <div className="flex justify-between gap-3">
                        <span className="text-xs font-semibold">
                          {movement.movement_type}
                        </span>
                        <span className="text-xs">
                          {movement.quantity}
                        </span>
                      </div>
                      {movement.reason && (
                        <p className="mt-1 text-xs text-[var(--muted)]">
                          {movement.reason}
                        </p>
                      )}
                    </div>
                  ))
                )}
              </div>
            </section>
          )}
        </aside>
      </div>
    </AppShell>
  );
}

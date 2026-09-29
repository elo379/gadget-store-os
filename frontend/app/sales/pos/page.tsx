"use client";

import { FormEvent, useEffect, useMemo, useState } from "react";
import { AppShell } from "@/components/app-shell";
import { apiGet, apiPost, ApiError } from "@/lib/api";
import { useOrganization } from "@/components/organization-provider";

type Product = {
  id: string;
  name: string;
  sku: string;
  brand?: string | null;
  model?: string | null;
  is_serialized: boolean;
  selling_price?: number | string;
  barcode?: string;
};
type Customer = { id: string; name: string; phone: string };
type Device = { id: string; product_id: string | null; status: string; imei: string | null; serial_number: string | null };

type CartLine = {
  product: Product;
  quantity: number;
  unitPrice: number;
  deviceId?: string;
};

type SaleResponse = {
  id: string;
  reference_number?: string;
  total: number | string;
  subtotal: number | string;
  discount: number | string;
  status: string;
};
type Receipt = { reference_number: string; total: number | string; amount_paid: number | string; amount_due: number | string; payment_status: string };

export default function POSPage() {
  const { organizationId } = useOrganization();

  const [products, setProducts] = useState<Product[]>([]);
  const [search, setSearch] = useState("");
  const [cart, setCart] = useState<CartLine[]>([]);
  const [discount, setDiscount] = useState("");
  const [tax, setTax] = useState("");
  const [fees, setFees] = useState("");
  const [paymentMethod, setPaymentMethod] = useState("cash");
  const [paymentAmount, setPaymentAmount] = useState("");
  const [customers, setCustomers] = useState<Customer[]>([]);
  const [customerId, setCustomerId] = useState("");
  const [deviceScan, setDeviceScan] = useState("");

  const [loading, setLoading] = useState(true);
  const [checkoutLoading, setCheckoutLoading] = useState(false);
  const [error, setError] = useState("");
  const [success, setSuccess] = useState<SaleResponse | null>(null);
  const [receipt, setReceipt] = useState<Receipt | null>(null);

  useEffect(() => {
    async function loadProducts() {
      if (!organizationId) return;

      setLoading(true);

      try {
        const result = await apiGet<Product[]>(
          `/products?organization_id=${organizationId}`
        );
        setProducts(result);
        setCustomers(await apiGet<Customer[]>(`/customers?organization_id=${organizationId}`));
      } catch (err) {
        setError(
          err instanceof ApiError
            ? err.message
            : "Unable to load products."
        );
      } finally {
        setLoading(false);
      }
    }

    void loadProducts();
  }, [organizationId]);

  const filteredProducts = useMemo(() => {
    const value = search.trim().toLowerCase();

    if (!value) return products.slice(0, 8);

    return products
      .filter(
        (product) =>
          product.name.toLowerCase().includes(value) ||
          product.sku.toLowerCase().includes(value) ||
          product.brand?.toLowerCase().includes(value) ||
          product.model?.toLowerCase().includes(value)
          || product.barcode?.toLowerCase().includes(value)
      )
      .slice(0, 8);
  }, [products, search]);

  const subtotal = cart.reduce(
    (sum, line) => sum + line.quantity * line.unitPrice,
    0
  );

  const discountValue = Math.max(0, Number(discount) || 0);
  const taxValue = Math.max(0, Number(tax) || 0);
  const feeValue = Math.max(0, Number(fees) || 0);
  const total = Math.max(0, subtotal - discountValue + taxValue + feeValue);

  function addProduct(product: Product) {
    setSuccess(null);

    const existing = cart.find((line) => line.product.id === product.id);

    if (existing) {
      setCart(
        cart.map((line) =>
          line.product.id === product.id
            ? { ...line, quantity: line.quantity + 1 }
            : line
        )
      );
      return;
    }

    setCart([
      ...cart,
      {
        product,
        quantity: 1,
        unitPrice: Number(product.selling_price ?? 0),
      },
    ]);

    setSearch("");
  }

  function updateQuantity(productId: string, quantity: number) {
    if (quantity <= 0) {
      setCart(cart.filter((line) => line.product.id !== productId));
      return;
    }

    setCart(
      cart.map((line) =>
        line.product.id === productId ? { ...line, quantity } : line
      )
    );
  }

  function updatePrice(productId: string, unitPrice: number) {
    setCart(
      cart.map((line) =>
        line.product.id === productId ? { ...line, unitPrice } : line
      )
    );
  }

  async function attachScannedDevice() {
    if (!organizationId || !deviceScan.trim()) return;
    try {
      const value = encodeURIComponent(deviceScan.trim());
      let device: Device;
      try {
        device = await apiGet<Device>(`/devices/lookup/imei/${value}?organization_id=${organizationId}`);
      } catch {
        device = await apiGet<Device>(`/devices/lookup/serial/${value}?organization_id=${organizationId}`);
      }
      const line = cart.find((item) => item.product.id === device.product_id);
      if (!line) throw new Error("Add the scanned device product to the cart first.");
      if (!line.product.is_serialized) throw new Error("The scanned device is not a serialized cart product.");
      setCart(cart.map((item) => item.product.id === line.product.id ? { ...item, quantity: 1, deviceId: device.id } : item));
      setDeviceScan("");
      setError("");
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : "Unable to find this device.");
    }
  }

  async function checkout(event: FormEvent) {
    event.preventDefault();

    if (!organizationId || cart.length === 0) return;

    if (cart.some((line) => line.unitPrice <= 0)) {
      setError("Enter a selling price for every cart item.");
      return;
    }

    if (Number(paymentAmount || 0) > total) {
      setError("Payment cannot exceed the sale total.");
      return;
    }

    setCheckoutLoading(true);
    setError("");

    try {
      const saleReference = `SALE-${Date.now()}-${crypto.randomUUID().slice(0, 8)}`;

      const sale = await apiPost<SaleResponse>("/sales", {
        organization_id: organizationId,
        reference_number: saleReference,
        customer_id: customerId || null,
        discount: discountValue,
        tax: taxValue,
        fees: feeValue,
        payment_method: Number(paymentAmount) > 0 ? paymentMethod : null,
        amount_paid: Number(paymentAmount || 0),
        lines: cart.map((line) => ({
          product_id: line.product.id,
          quantity: line.quantity,
          unit_price: line.unitPrice,
          device_id: line.deviceId || null,
        })),
        notes: "",
      });

      setSuccess(sale);
      void apiGet<Receipt>(`/sales/${sale.id}/receipt?organization_id=${organizationId}`).then(setReceipt).catch(() => setReceipt(null));
      setCart([]);
      setDiscount("");
      setTax("");
      setFees("");
      setPaymentAmount("");
    } catch (err) {
      setError(
        err instanceof ApiError
          ? err.message
          : "Checkout failed."
      );
    } finally {
      setCheckoutLoading(false);
    }
  }

  return (
    <AppShell>
      <div className="mb-6">
        <p className="text-[11px] font-semibold uppercase tracking-[0.16em] text-[var(--accent)]">
          Point of sale
        </p>
        <h1 className="mt-2 text-2xl font-semibold tracking-[-0.03em]">
          New sale
        </h1>
        <p className="mt-1 text-sm text-[var(--muted)]">
          Build a cart and complete a real store transaction.
        </p>
      </div>

      {error && (
        <div className="mb-5 rounded-xl border border-red-200 bg-red-50 p-4 text-sm text-red-700">
          {error}
        </div>
      )}

      {success && (
        <div className="mb-5 rounded-xl border border-green-200 bg-green-50 p-4 text-sm text-green-800">
          <div className="flex flex-wrap items-start justify-between gap-4">
            <div><p className="font-semibold">Sale completed · {receipt?.reference_number ?? success.reference_number ?? success.id}</p>
            <p className="mt-1">Receipt {receipt ? `total ₦${Number(receipt.total).toLocaleString()} · paid ₦${Number(receipt.amount_paid).toLocaleString()} · due ₦${Number(receipt.amount_due).toLocaleString()} · ${receipt.payment_status}` : "is loading"}</p></div>
            {receipt && <button type="button" onClick={() => window.print()} className="rounded-lg border border-green-300 px-3 py-2 font-semibold">Print receipt</button>}
          </div>
        </div>
      )}

      <div className="grid gap-5 xl:grid-cols-[1fr_390px]">
        <section className="rounded-2xl border border-[var(--border)] bg-white p-5">
          <div className="relative">
            <input
              value={search}
              onChange={(event) => setSearch(event.target.value)}
              placeholder="Search product or scan barcode…"
              className="h-12 w-full rounded-xl border border-[var(--border)] px-4 text-sm outline-none focus:border-neutral-900"
            />

            {search && filteredProducts.length > 0 && (
              <div className="absolute left-0 right-0 top-14 z-20 overflow-hidden rounded-xl border border-[var(--border)] bg-white shadow-lg">
                {filteredProducts.map((product) => (
                  <button
                    key={product.id}
                    type="button"
                    onClick={() => addProduct(product)}
                    className="flex w-full items-center justify-between border-b border-[var(--border)] px-4 py-3 text-left last:border-0 hover:bg-neutral-50"
                  >
                    <div>
                      <p className="text-sm font-semibold">{product.name}</p>
                      <p className="mt-1 text-xs text-[var(--muted)]">
                        {product.sku}
                      </p>
                    </div>
                    <span className="text-xs text-[var(--muted)]">
                      {product.is_serialized ? "Serialized" : "Stock"}
                    </span>
                  </button>
                ))}
              </div>
            )}
          </div>
          <label className="mt-4 block text-xs text-[var(--muted)]">IMEI / serial scan for serialized items
            <div className="mt-1 flex gap-2"><input value={deviceScan} onChange={(event) => setDeviceScan(event.target.value)} placeholder="Scan IMEI or serial number" className="h-11 min-w-0 flex-1 rounded-xl border border-[var(--border)] px-4 text-sm text-neutral-900" /><button type="button" onClick={() => void attachScannedDevice()} className="rounded-xl border px-3 text-sm font-semibold">Attach</button></div>
          </label>

          <div className="mt-6">
            {loading ? (
              <p className="py-16 text-center text-sm text-[var(--muted)]">
                Loading products…
              </p>
            ) : cart.length === 0 ? (
              <div className="rounded-xl border border-dashed border-neutral-300 px-6 py-20 text-center">
                <p className="text-sm font-semibold">Cart is empty</p>
                <p className="mt-1 text-xs text-[var(--muted)]">
                  Search for a product to begin.
                </p>
              </div>
            ) : (
              <div className="space-y-3">
                {cart.map((line) => (
                  <div
                    key={line.product.id}
                    className="rounded-xl border border-[var(--border)] p-4"
                  >
                    <div className="flex items-start justify-between gap-4">
                      <div>
                        <p className="text-sm font-semibold">
                          {line.product.name}
                        </p>
                        <p className="mt-1 text-xs text-[var(--muted)]">
                          {line.product.sku}
                        </p>
                        {line.product.is_serialized && <p className="mt-1 text-xs text-[var(--muted)]">{line.deviceId ? "IMEI / serial attached" : "Scan a device to complete this line"}</p>}
                      </div>

                      <button
                        type="button"
                        onClick={() =>
                          updateQuantity(line.product.id, 0)
                        }
                        className="text-xs font-semibold text-red-600"
                      >
                        Remove
                      </button>
                    </div>

                    <div className="mt-4 grid gap-3 sm:grid-cols-2">
                      <label className="text-xs">
                        Quantity
                        <input
                          type="number"
                          min="1"
                          value={line.quantity}
                          onChange={(event) =>
                            updateQuantity(
                              line.product.id,
                              Number(event.target.value)
                            )
                          }
                          className="mt-1 h-10 w-full rounded-lg border border-[var(--border)] px-3 text-sm"
                        />
                      </label>

                      <label className="text-xs">
                        Unit price
                        <input
                          type="number"
                          min="0"
                          value={line.unitPrice || ""}
                          onChange={(event) =>
                            updatePrice(
                              line.product.id,
                              Number(event.target.value)
                            )
                          }
                          placeholder="₦"
                          className="mt-1 h-10 w-full rounded-lg border border-[var(--border)] px-3 text-sm"
                        />
                      </label>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        </section>

        <aside className="rounded-2xl border border-[var(--border)] bg-white p-5">
          <p className="text-sm font-semibold">Order summary</p>

          <div className="mt-6 space-y-3 border-b border-[var(--border)] pb-5 text-sm">
            <div className="flex justify-between">
              <span className="text-[var(--muted)]">Subtotal</span>
              <span>₦{subtotal.toLocaleString()}</span>
            </div>

            <label className="block">
              <span className="text-xs text-[var(--muted)]">Discount</span>
              <input
                type="number"
                min="0"
                value={discount}
                onChange={(event) => setDiscount(event.target.value)}
                className="mt-1 h-10 w-full rounded-lg border border-[var(--border)] px-3 text-sm"
                placeholder="₦0"
              />
            </label>
            <label className="block">
              <span className="text-xs text-[var(--muted)]">Configured tax</span>
              <input type="number" min="0" value={tax} onChange={(event) => setTax(event.target.value)} className="mt-1 h-10 w-full rounded-lg border border-[var(--border)] px-3 text-sm" placeholder="₦0" />
            </label>
            <label className="block">
              <span className="text-xs text-[var(--muted)]">Fees</span>
              <input type="number" min="0" value={fees} onChange={(event) => setFees(event.target.value)} className="mt-1 h-10 w-full rounded-lg border border-[var(--border)] px-3 text-sm" placeholder="₦0" />
            </label>
          </div>

          <div className="flex justify-between py-5 text-lg font-semibold">
            <span>Total</span>
            <span>₦{total.toLocaleString()}</span>
          </div>

          <form onSubmit={checkout} className="space-y-3">
            <select value={customerId} onChange={(event) => setCustomerId(event.target.value)} className="h-11 w-full rounded-xl border border-[var(--border)] bg-white px-3 text-sm">
              <option value="">Walk-in customer</option>
              {customers.map((customer) => <option key={customer.id} value={customer.id}>{customer.name}{customer.phone ? ` · ${customer.phone}` : ""}</option>)}
            </select>
            <select
              value={paymentMethod}
              onChange={(event) => setPaymentMethod(event.target.value)}
              className="h-11 w-full rounded-xl border border-[var(--border)] bg-white px-3 text-sm"
            >
              <option value="cash">Cash</option>
              <option value="transfer">Bank transfer</option>
              <option value="pos">POS</option>
              <option value="card">Card</option>
            </select>

            <input
              type="number"
              min="0"
              value={paymentAmount}
              onChange={(event) => setPaymentAmount(event.target.value)}
              placeholder="Amount received (0 for pay later)"
              className="h-11 w-full rounded-xl border border-[var(--border)] px-3 text-sm"
            />

            <button
              type="submit"
              disabled={checkoutLoading || cart.length === 0}
              className="h-12 w-full rounded-xl bg-[var(--accent)] text-sm font-semibold text-white disabled:opacity-50"
            >
              {checkoutLoading
                ? "Processing…"
                : `Charge ₦${total.toLocaleString()}`}
            </button>
          </form>
        </aside>
      </div>
    </AppShell>
  );
}

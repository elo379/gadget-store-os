"use client";

import { FormEvent, useEffect, useMemo, useState } from "react";
import { AppShell } from "@/components/app-shell";
import { apiGet, apiPost, ApiError } from "@/lib/api";
import { useOrganization } from "@/components/organization-provider";
import { CameraScanner } from "@/components/camera-scanner";
import { deleteEncryptedDraft, listEncryptedDrafts, saveEncryptedDraft } from "@/lib/offline-drafts";

type Product = {
  id: string;
  name: string;
  sku: string | null;
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
type OfflineCart = { cart: CartLine[]; discount: string; tax: string; fees: string };

type SaleResponse = {
  id: string;
  reference_number?: string;
  total: number | string;
  subtotal: number | string;
  discount: number | string;
  status: string;
};
type Receipt = { reference_number: string; subtotal: number | string; discount: number | string; tax: number | string; fees: number | string; total: number | string; amount_paid: number | string; amount_due: number | string; payment_status: string; lines: { product_id: string; quantity: number | string; unit_price: number | string; line_total: number | string }[] };

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
  const [scannerTarget, setScannerTarget] = useState<"product" | "device">("product");

  const [loading, setLoading] = useState(true);
  const [checkoutLoading, setCheckoutLoading] = useState(false);
  const [error, setError] = useState("");
  const [success, setSuccess] = useState<SaleResponse | null>(null);
  const [receipt, setReceipt] = useState<Receipt | null>(null);
  const [savedDrafts, setSavedDrafts] = useState<{ id: string; createdAt: string }[]>([]);
  const [isOnline, setIsOnline] = useState(true);
  const [offlineMessage, setOfflineMessage] = useState("");

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

    queueMicrotask(() => void loadProducts());
  }, [organizationId]);

  useEffect(() => {
    const updateConnection = () => setIsOnline(navigator.onLine);
    queueMicrotask(updateConnection);
    window.addEventListener("online", updateConnection);
    window.addEventListener("offline", updateConnection);
    return () => { window.removeEventListener("online", updateConnection); window.removeEventListener("offline", updateConnection); };
  }, []);

  useEffect(() => {
    if (!organizationId) return;
    let active = true;
    queueMicrotask(() => { void listEncryptedDrafts(organizationId).then((rows) => { if (active) setSavedDrafts(rows.map(({ id, createdAt }) => ({ id, createdAt }))); }).catch(() => { if (active) setSavedDrafts([]); }); });
    return () => { active = false; };
  }, [organizationId]);

  async function saveCartDraft() {
    if (!organizationId || !cart.length) return;
    try {
      await saveEncryptedDraft(organizationId, { cart, discount, tax, fees } satisfies OfflineCart);
      const rows = await listEncryptedDrafts(organizationId);
      setSavedDrafts(rows.map(({ id, createdAt }) => ({ id, createdAt })));
      setOfflineMessage("Cart saved encrypted on this device. It has not been submitted and still needs fresh stock validation and cashier confirmation when connected.");
    } catch (cause) { setOfflineMessage(cause instanceof Error ? cause.message : "Unable to save an offline cart draft."); }
  }

  async function restoreCartDraft() {
    if (!organizationId || !savedDrafts.length) return;
    try {
      const drafts = await listEncryptedDrafts(organizationId);
      const draft = drafts[0];
      const saved = draft?.payload as OfflineCart | undefined;
      if (!saved || !Array.isArray(saved.cart)) throw new Error("Saved cart data is invalid.");
      const currentProducts = await apiGet<Product[]>(`/products?organization_id=${organizationId}`);
      const refreshed = saved.cart.map((line) => {
        const product = currentProducts.find((item) => item.id === line.product.id);
        if (!product) throw new Error(`Product ${line.product.name} is no longer available. Review the cart before checkout.`);
        return { ...line, product, deviceId: undefined };
      });
      setProducts(currentProducts);
      setCart(refreshed);
      setDiscount(saved.discount);
      setTax(saved.tax);
      setFees(saved.fees);
      setCustomerId(""); setPaymentAmount("");
      setOfflineMessage("Cart restored and product records refreshed from GSOS. Serialized device selection, customer and tender were cleared; verify stock and rescan devices before checkout.");
      await deleteEncryptedDraft(organizationId, draft.id);
      setSavedDrafts((rows) => rows.filter((row) => row.id !== draft.id));
    } catch (cause) { setOfflineMessage(cause instanceof Error ? cause.message : "Unable to restore this cart."); }
  }

  const filteredProducts = useMemo(() => {
    const value = search.trim().toLowerCase();

    if (!value) return products.slice(0, 8);

    return products
      .filter(
        (product) =>
          product.name.toLowerCase().includes(value) ||
          product.sku?.toLowerCase().includes(value) ||
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

  async function attachScannedDevice(rawValue = deviceScan) {
    if (!organizationId || !rawValue.trim()) return;
    try {
      const value = encodeURIComponent(rawValue.trim());
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
      <div className="mb-5 border-b border-[var(--border)] pb-5">
        <p className="text-[11px] font-semibold uppercase tracking-[0.16em] text-[var(--accent)]">
          Sell · Point of sale
        </p>
        <h1 className="gsos-page-title mt-2 text-3xl font-semibold">
          New sale
        </h1>
        <p className="mt-1 text-sm text-[var(--muted)]">
          Search or scan products, build the order, then take payment.
        </p>
      </div>

      <ol aria-label="Checkout flow" className="mb-5 grid grid-cols-3 gap-2 rounded-2xl border border-[var(--border)] bg-white p-3 shadow-sm sm:grid-cols-6">
        {["Search / scan", "Cart", "Customer", "Discount", "Payment", "Receipt"].map((step, index) => {
          const complete = index === 0 ? cart.length > 0 : index === 1 ? cart.length > 0 : index === 2 ? Boolean(customerId) : index === 3 ? discountValue > 0 : index === 4 ? Boolean(paymentAmount) || success !== null : success !== null;
          return <li key={step} className={`flex min-h-11 items-center gap-2 rounded-xl px-2 text-xs font-semibold sm:px-3 ${complete ? "bg-[var(--accent-soft)] text-[var(--accent-strong)]" : "bg-[var(--background)] text-[var(--muted)]"}`}><span className="grid h-6 w-6 shrink-0 place-items-center rounded-full bg-white text-[10px] shadow-sm">{complete ? "✓" : String(index + 1).padStart(2, "0")}</span><span>{step}</span></li>;
        })}
      </ol>

      {error && (
        <div role="alert" className="mb-5 rounded-xl border border-red-200 bg-red-50 p-4 text-sm text-red-700">
          {error}
        </div>
      )}
      <div className="mb-4 flex flex-wrap items-center justify-between gap-3 rounded-xl border border-[var(--border)] bg-white p-3 text-sm">
        <p role="status" className={isOnline ? "text-emerald-800" : "text-amber-800"}>{isOnline ? "Connected · checkout is validated by GSOS" : "Offline · checkout is unavailable; cart drafts can be saved on this device"}</p>
        <div className="flex gap-2"><button type="button" disabled={!cart.length} onClick={() => void saveCartDraft()} className="min-h-10 rounded-lg border px-3 text-xs font-semibold disabled:opacity-50">Save encrypted draft</button><button type="button" disabled={!isOnline || !savedDrafts.length || checkoutLoading} onClick={() => void restoreCartDraft()} className="min-h-10 rounded-lg border px-3 text-xs font-semibold disabled:opacity-50">Restore saved cart{savedDrafts.length ? ` (${savedDrafts.length})` : ""}</button></div>
      </div>
      {offlineMessage && <p role="status" className="mb-4 rounded-xl bg-blue-50 p-3 text-sm text-blue-900">{offlineMessage}</p>}

      {success && (
        <div className="mb-5 rounded-xl border border-green-200 bg-green-50 p-4 text-sm text-green-800">
          <div id="print-receipt" className="flex flex-wrap items-start justify-between gap-4">
            <div><p className="font-semibold">Sale completed · {receipt?.reference_number ?? success.reference_number ?? success.id}</p>
            {receipt ? <><div className="mt-2 space-y-1 text-sm">{receipt.lines.map((line, index) => <p key={`${line.product_id}-${index}`}>{products.find((product) => product.id === line.product_id)?.name ?? "Product"} · {line.quantity} × ₦{Number(line.unit_price).toLocaleString()} = ₦{Number(line.line_total).toLocaleString()}</p>)}</div><p className="mt-2 text-sm">Subtotal ₦{Number(receipt.subtotal).toLocaleString()} · Discount ₦{Number(receipt.discount).toLocaleString()} · Tax ₦{Number(receipt.tax).toLocaleString()} · Fees ₦{Number(receipt.fees).toLocaleString()}</p><p className="mt-1">Total ₦{Number(receipt.total).toLocaleString()} · Paid ₦{Number(receipt.amount_paid).toLocaleString()} · Due ₦{Number(receipt.amount_due).toLocaleString()} · {receipt.payment_status}</p></> : <p className="mt-1">Receipt is loading…</p>}</div>
            {receipt && <button type="button" onClick={() => window.print()} className="print:hidden rounded-lg border border-green-300 px-3 py-2 font-semibold">Print receipt</button>}
          </div>
        </div>
      )}

      <div className="grid min-w-0 gap-5 xl:grid-cols-[minmax(0,1fr)_390px]">
        <section className="rounded-2xl border border-[var(--border)] bg-white p-5">
          <p className="mb-3 text-xs font-bold uppercase tracking-[.13em] text-[var(--muted)]">1 · Search or scan</p>
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
                        {product.sku || "Serialized device template"}
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
          <label className="mt-4 block text-xs font-medium text-[var(--muted)]">Device identity · IMEI or serial
            <div className="mt-1 flex gap-2"><input value={deviceScan} onChange={(event) => setDeviceScan(event.target.value)} placeholder="Scan IMEI or serial number" className="h-11 min-w-0 flex-1 rounded-xl border border-[var(--border)] px-4 text-sm text-neutral-900" /><button type="button" onClick={() => void attachScannedDevice()} className="rounded-xl border px-3 text-sm font-semibold">Attach</button></div>
          </label>
          <label className="mt-4 block text-xs font-semibold">Camera scan target<select value={scannerTarget} onChange={(event) => setScannerTarget(event.target.value as typeof scannerTarget)} className="mt-1 h-11 w-full rounded-lg border bg-white px-3 text-sm font-normal"><option value="product">Product barcode / QR</option><option value="device">Device IMEI / serial</option></select></label>
          <CameraScanner
            expectation={scannerTarget === "device" ? "device" : "barcode"}
            onDetected={(result) => {
              if (scannerTarget === "device") {
                setDeviceScan(result.normalizedValue);
                return attachScannedDevice(result.normalizedValue);
              }
              setSearch(result.normalizedValue);
            }}
          />

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
          <p className="text-xs font-bold uppercase tracking-[.13em] text-[var(--accent)]">Order summary</p>
          <p className="mt-1 text-lg font-semibold">Customer · discount · payment</p>

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
              disabled={!isOnline || checkoutLoading || cart.length === 0}
              className="h-12 w-full rounded-xl bg-[var(--accent)] text-sm font-semibold text-white disabled:opacity-50"
            >
              {checkoutLoading
                ? "Processing…"
                : !isOnline ? "Connect to complete checkout" : `Charge ₦${total.toLocaleString()}`}
            </button>
          </form>
        </aside>
      </div>
    </AppShell>
  );
}

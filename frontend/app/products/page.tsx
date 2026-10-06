"use client";

import { FormEvent, useEffect, useMemo, useState } from "react";
import { apiGet, apiPost } from "@/lib/api";
import { useOrganization } from "@/components/organization-provider";
import { PageHeader } from "@/components/page-header";

type Product = { id: string; name: string; sku: string | null; category_id?: string | null; brand: string; model: string; description: string; is_serialized: boolean; is_active: boolean };
type Category = { id: string; name: string; is_active: boolean };
const productTypes = ["Smartphone", "Laptop", "Tablet", "Accessory", "Screen Protector", "Charger / Cable", "Wearable", "Audio", "Other"];

export default function ProductsPage() {
  const { organizationId } = useOrganization();
  const [products, setProducts] = useState<Product[]>([]);
  const [categories, setCategories] = useState<Category[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [query, setQuery] = useState("");
  const [category, setCategory] = useState("all");
  const [dialog, setDialog] = useState(false);
  const [saving, setSaving] = useState(false);
  const [message, setMessage] = useState("");
  const [type, setType] = useState(productTypes[0]);
  const [name, setName] = useState("");
  const [sku, setSku] = useState("");
  const [brand, setBrand] = useState("");
  const [model, setModel] = useState("");
  const [description, setDescription] = useState("");
  const [categoryId, setCategoryId] = useState("");
  const [barcode, setBarcode] = useState("");
  const [unitCost, setUnitCost] = useState("");
  const [sellingPrice, setSellingPrice] = useState("");
  const [reorderThreshold, setReorderThreshold] = useState("0");
  const productTypeKey: Record<string, string> = { "Smartphone": "smartphone", "Laptop": "laptop", "Tablet": "tablet", "Accessory": "accessory", "Screen Protector": "screen_protector", "Charger / Cable": "charger_cable", "Wearable": "wearable", "Audio": "audio", "Other": "other" };
  const serializedType = ["Smartphone", "Laptop", "Tablet", "Wearable"].includes(type);

  async function load() {
    if (!organizationId) return;
    setLoading(true); setError("");
    try {
      const [items, groups] = await Promise.all([
        apiGet<Product[]>(`/products?organization_id=${organizationId}`),
        apiGet<Category[]>(`/products/categories?organization_id=${organizationId}`),
      ]);
      setProducts(Array.isArray(items) ? items : []); setCategories(Array.isArray(groups) ? groups : []);
    } catch (cause) { setError(cause instanceof Error ? cause.message : "Catalogue could not be loaded."); }
    finally { setLoading(false); }
  }
  useEffect(() => { queueMicrotask(() => void load()); }, [organizationId]);

  const filtered = useMemo(() => products.filter((product) => {
    const matchesQuery = `${product.name} ${product.sku} ${product.brand} ${product.model}`.toLowerCase().includes(query.toLowerCase());
    return matchesQuery && (category === "all" || product.category_id === category);
  }), [products, query, category]);

  async function createProduct(event: FormEvent) {
    event.preventDefault(); if (!organizationId) return;
    setSaving(true); setMessage("");
    try {
      await apiPost(`/products?organization_id=${organizationId}`, {
        name: name.trim(), sku: serializedType ? null : sku.trim(), brand: brand.trim(), model: model.trim(), description: description.trim(),
        category_id: categoryId || null, is_serialized: serializedType,
        product_type: productTypeKey[type], barcode: barcode.trim(), unit_cost: unitCost || "0", selling_price: sellingPrice || "0", reorder_threshold: reorderThreshold || "0",
      });
      setMessage("Product template created. Receive stock separately to record physical inventory.");
      setDialog(false); setName(""); setSku(""); setBrand(""); setModel(""); setDescription(""); setCategoryId(""); setBarcode(""); setUnitCost(""); setSellingPrice(""); setReorderThreshold("0"); await load();
    } catch (err) { setMessage(err instanceof Error ? err.message : "Product could not be created."); }
    finally { setSaving(false); }
  }

  return <div className="space-y-6">
    <PageHeader eyebrow="Catalogue" title="Products" description="Maintain product templates and distinguish tracked devices from quantity-based goods." />
    <section className="flex flex-wrap items-center justify-between gap-3 rounded-2xl border border-[var(--border)] bg-white p-4 sm:p-5">
      <div><p className="text-sm font-semibold">{products.length} catalogue products</p><p className="mt-1 text-xs text-[var(--muted)]">Product templates define what you sell. Receiving records the physical stock.</p></div>
      <button onClick={() => setDialog(true)} className="min-h-11 rounded-xl bg-neutral-950 px-5 text-sm font-semibold text-white">Add product</button>
    </section>
    {message && <p role="status" className="rounded-xl border border-emerald-200 bg-emerald-50 p-3 text-sm text-emerald-900">{message}</p>}
    <section className="space-y-4 rounded-2xl border border-[var(--border)] bg-white p-4 sm:p-5">
      <div className="grid gap-3 sm:grid-cols-[1fr_220px]">
        <label className="text-xs font-semibold">Search catalogue<input value={query} onChange={(event) => setQuery(event.target.value)} placeholder="Name, SKU, brand or model" className="mt-1 block h-11 w-full rounded-xl border border-[var(--border)] px-3 text-sm font-normal" /></label>
        <label className="text-xs font-semibold">Category<select value={category} onChange={(event) => setCategory(event.target.value)} className="mt-1 block h-11 w-full rounded-xl border border-[var(--border)] bg-white px-3 text-sm font-normal"><option value="all">All categories</option>{categories.map((item) => <option key={item.id} value={item.id}>{item.name}</option>)}</select></label>
      </div>
      {error && <div className="rounded-xl bg-red-50 p-4 text-sm text-red-800">{error}<button onClick={() => void load()} className="ml-3 font-semibold underline">Retry</button></div>}
      {loading ? <div className="py-12 text-center text-sm text-neutral-500">Loading catalogue…</div> : filtered.length === 0 ? <div className="py-12 text-center"><p className="font-semibold">{products.length ? "No matching products" : "No products yet"}</p><p className="mt-1 text-sm text-[var(--muted)]">{products.length ? "Adjust your search or category filter." : "Add a product template to begin building the catalogue."}</p></div> : <div className="overflow-x-auto"><table className="w-full min-w-[680px] text-left text-sm"><thead><tr className="border-b text-xs text-[var(--muted)]"><th className="px-3 py-3">Product</th><th className="px-3 py-3">SKU</th><th className="px-3 py-3">Category</th><th className="px-3 py-3">Tracking</th><th className="px-3 py-3">Status</th></tr></thead><tbody>{filtered.map((item) => <tr key={item.id} className="border-b last:border-0"><td className="px-3 py-4"><p className="font-semibold">{item.name}</p><p className="text-xs text-neutral-500">{[item.brand, item.model].filter(Boolean).join(" · ") || "—"}</p></td><td className="px-3 py-4 font-mono text-xs">{item.sku}</td><td className="px-3 py-4">{categories.find((entry) => entry.id === item.category_id)?.name || "Uncategorised"}</td><td className="px-3 py-4">{item.is_serialized ? "Individual devices" : "Quantity based"}</td><td className="px-3 py-4"><span className="rounded-full bg-neutral-100 px-2.5 py-1 text-xs">{item.is_active ? "Active" : "Inactive"}</span></td></tr>)}</tbody></table></div>}
    </section>
    {dialog && <div role="presentation" className="fixed inset-0 z-[60] flex items-end justify-center bg-black/40 sm:items-center sm:p-4" onMouseDown={(event) => { if (event.target === event.currentTarget) setDialog(false); }}><form onSubmit={createProduct} className="max-h-[92vh] w-full max-w-2xl space-y-4 overflow-y-auto rounded-t-2xl bg-white p-5 sm:rounded-2xl sm:p-6"><div className="flex justify-between gap-3"><div><h2 className="text-xl font-semibold">Add product</h2><p className="mt-1 text-sm text-neutral-500">Choose a gadget category, then define its catalogue identity.</p></div><button type="button" aria-label="Close" onClick={() => setDialog(false)} className="h-10 w-10 rounded-lg border">×</button></div>
      <label className="block text-sm font-medium">Product type<select value={type} onChange={(event) => setType(event.target.value)} className="mt-1 block h-11 w-full rounded-xl border px-3">{productTypes.map((item) => <option key={item}>{item}</option>)}</select></label>
      <div className="grid gap-3 sm:grid-cols-2"><label className="text-sm font-medium">Product name<input required value={name} onChange={(event) => setName(event.target.value)} className="mt-1 block h-11 w-full rounded-xl border px-3 font-normal" /></label>{!serializedType && <label className="text-sm font-medium">SKU<input required value={sku} onChange={(event) => setSku(event.target.value)} className="mt-1 block h-11 w-full rounded-xl border px-3 font-normal" /></label>}<label className="text-sm font-medium">Brand<input value={brand} onChange={(event) => setBrand(event.target.value)} className="mt-1 block h-11 w-full rounded-xl border px-3 font-normal" /></label><label className="text-sm font-medium">Model / variant<input value={model} onChange={(event) => setModel(event.target.value)} className="mt-1 block h-11 w-full rounded-xl border px-3 font-normal" /></label></div>
      <label className="block text-sm font-medium">Category<select value={categoryId} onChange={(event) => setCategoryId(event.target.value)} className="mt-1 block h-11 w-full rounded-xl border bg-white px-3"><option value="">No category</option>{categories.map((item) => <option key={item.id} value={item.id}>{item.name}</option>)}</select></label>
      <div className="grid gap-3 sm:grid-cols-2">{[["Barcode", barcode, setBarcode, "text"], ["Unit cost", unitCost, setUnitCost, "number"], ["Selling price", sellingPrice, setSellingPrice, "number"], ["Reorder threshold", reorderThreshold, setReorderThreshold, "number"]].map(([label, value, setter, inputType]) => <label key={label as string} className="text-sm font-medium">{label as string}<input type={inputType as string} min={inputType === "number" ? "0" : undefined} step={inputType === "number" ? "0.01" : undefined} value={value as string} onChange={(event) => (setter as (value: string) => void)(event.target.value)} className="mt-1 block h-11 w-full rounded-xl border px-3 font-normal" /></label>)}</div>
      <label className="block text-sm font-medium">Description<textarea value={description} onChange={(event) => setDescription(event.target.value)} rows={3} className="mt-1 block w-full rounded-xl border p-3 font-normal" /></label>
      <div className="rounded-xl bg-neutral-50 p-3 text-sm text-neutral-600">{serializedType ? "This is a product template. Physical units will be recorded separately with IMEI or serial number during receiving; this template does not need a SKU." : "This product uses quantity-based stock and requires its own SKU. Barcode, prices and reorder threshold apply to the stock item."}</div>
      <div className="flex flex-col-reverse gap-2 sm:flex-row sm:justify-end"><button type="button" onClick={() => setDialog(false)} className="min-h-11 rounded-xl border px-5">Cancel</button><button disabled={saving} className="min-h-11 rounded-xl bg-neutral-950 px-5 font-semibold text-white disabled:opacity-50">{saving ? "Creating…" : "Create product template"}</button></div>
    </form></div>}
  </div>;
}

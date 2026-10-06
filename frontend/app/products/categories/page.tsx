"use client";

import { FormEvent, useEffect, useState } from "react";
import Link from "next/link";
import { apiGet, apiPost } from "@/lib/api";
import { useOrganization } from "@/components/organization-provider";
import { PageHeader } from "@/components/page-header";

type Category = { id: string; name: string; description: string; is_active: boolean };
type Product = { category_id?: string | null };

export default function CategoriesPage() {
  const { organizationId } = useOrganization();
  const [categories, setCategories] = useState<Category[]>([]);
  const [products, setProducts] = useState<Product[]>([]);
  const [name, setName] = useState("");
  const [description, setDescription] = useState("");
  const [busy, setBusy] = useState(false);
  const [loading, setLoading] = useState(true);
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");
  async function load() {
    if (!organizationId) return;
    setLoading(true); setError("");
    try {
      const [groups, items] = await Promise.all([apiGet<Category[]>(`/products/categories?organization_id=${organizationId}`), apiGet<Product[]>(`/products?organization_id=${organizationId}`)]);
      setCategories(groups); setProducts(items);
    } catch (cause) { setError(cause instanceof Error ? cause.message : "Categories could not be loaded."); }
    finally { setLoading(false); }
  }
  useEffect(() => { queueMicrotask(() => void load()); }, [organizationId]);
  async function create(event: FormEvent) {
    event.preventDefault(); if (!organizationId) return;
    setBusy(true); setMessage("");
    try { await apiPost(`/products/categories?organization_id=${organizationId}`, { name: name.trim(), description: description.trim() }); setName(""); setDescription(""); setMessage("Category created."); await load(); }
    catch (err) { setMessage(err instanceof Error ? err.message : "Category could not be created."); }
    finally { setBusy(false); }
  }
  return <div className="space-y-6">
    <PageHeader eyebrow="Catalogue" title="Categories" description="Organize product templates using the store’s live category list." />
    <Link href="/products" className="text-sm font-semibold text-emerald-800 underline">← Back to products</Link>
    {message && <p role="status" className="rounded-xl bg-neutral-100 p-3 text-sm">{message}</p>}
    {error && <p className="rounded-xl bg-red-50 p-3 text-sm text-red-800">{error} <button onClick={() => void load()} className="underline">Retry</button></p>}
    <div className="grid gap-5 lg:grid-cols-[minmax(260px,.7fr)_1.3fr]">
      <form onSubmit={create} className="h-fit space-y-4 rounded-2xl border bg-white p-5"><div><h2 className="font-semibold">Create category</h2><p className="mt-1 text-sm text-neutral-500">Use categories such as Smartphones, Accessories, Audio or Wearables.</p></div><label className="block text-sm font-medium">Category name<input required minLength={2} value={name} onChange={(event) => setName(event.target.value)} className="mt-1 h-11 w-full rounded-xl border px-3 font-normal" /></label><label className="block text-sm font-medium">Description<textarea value={description} onChange={(event) => setDescription(event.target.value)} rows={3} className="mt-1 w-full rounded-xl border p-3 font-normal" /></label><button disabled={busy} className="min-h-11 w-full rounded-xl bg-neutral-950 px-4 font-semibold text-white disabled:opacity-50">{busy ? "Saving…" : "Create category"}</button></form>
      <section className="rounded-2xl border bg-white p-5"><div className="mb-4"><h2 className="font-semibold">Store categories</h2><p className="text-sm text-neutral-500">{categories.length} categories · counts reflect product templates</p></div>{loading ? <p className="py-8 text-sm text-neutral-500">Loading categories…</p> : categories.length === 0 ? <div className="py-8 text-center"><p className="font-semibold">No categories yet</p><p className="mt-1 text-sm text-neutral-500">Create the first category to organize your catalogue.</p></div> : <ul className="divide-y">{categories.map((category) => <li key={category.id} className="flex items-center justify-between gap-4 py-4"><div><p className="font-semibold">{category.name}</p><p className="mt-1 text-sm text-neutral-500">{category.description || "No description"}</p></div><span className="whitespace-nowrap text-sm text-neutral-600">{products.filter((item) => item.category_id === category.id).length} products · {category.is_active ? "Active" : "Inactive"}</span></li>)}</ul>}<p className="mt-4 border-t pt-4 text-xs text-neutral-500">The current backend supports listing and creating categories. Editing, deactivation and deletion are not available in this API.</p></section>
    </div>
  </div>;
}

"use client";

import { useEffect, useMemo, useState } from "react";
import { apiGet, apiPost } from "@/lib/api";
import { useOrganization } from "@/components/organization-provider";
import { PageHeader } from "@/components/page-header";
import { DataTable } from "@/components/data-table";

type Product = {
  id: string;
  name: string;
  sku?: string;
  category?: string;
  product_type?: string;
  is_active?: boolean;
};

export default function ProductsPage() {
  const { organizationId } = useOrganization();
  const [products, setProducts] = useState<Product[]>([]);
  const [filter, setFilter] = useState("All products");
  const [loading, setLoading] = useState(true);
  const [message, setMessage] = useState("");
  const [productName, setProductName] = useState("");
  const [productSku, setProductSku] = useState("");
  const [creating, setCreating] = useState(false);

  async function createProduct() {
    if (!organizationId || !productName.trim()) return;

    setCreating(true);

    try {
      await apiPost("/products", {
        organization_id: organizationId,
        name: productName.trim(),
        sku: productSku.trim(),
      });

      setProductName("");
      setProductSku("");
      setMessage("Product created.");
      await loadProducts();
    } catch {
      setMessage("Unable to create product.");
    } finally {
      setCreating(false);
    }
  }

  async function loadProducts() {
    if (!organizationId) return;

    setLoading(true);

    try {
      const data = await apiGet<Product[]>(
        `/products?organization_id=${organizationId}`,
      );

      setProducts(Array.isArray(data) ? data : []);
      setMessage("");
    } catch {
      setProducts([]);
      setMessage("Unable to load products.");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    void loadProducts();
  }, [organizationId]);

  const filteredProducts = useMemo(() => {
    if (filter === "All products") return products;

    if (filter === "Serialized") {
      return products.filter((product) => product.product_type === "serialized");
    }

    return products.filter(
      (product) => product.category?.toLowerCase() === filter.toLowerCase(),
    );
  }, [products, filter]);

  const rows = filteredProducts.map((product) => ({
    product: product.name,
    sku: product.sku || "—",
    category: product.category || "—",
    type: product.product_type || "—",
    status: product.is_active === false ? "Inactive" : "Active",
  }));

  return (
    <div className="space-y-6">
      <PageHeader
        eyebrow="Catalog"
        title="Products"
        description="Manage the store catalogue, SKUs, product types and active selling inventory."
      />

      <div className="rounded-2xl border border-[var(--border)] bg-[var(--surface)] p-5">
        <div className="mb-4">
          <h2 className="font-semibold">Add product</h2>
          <p className="text-sm text-[var(--muted)]">
            Create a product directly in the organization catalogue.
          </p>
        </div>

        <div className="grid gap-3 md:grid-cols-3">
          <input
            value={productName}
            onChange={(e) => setProductName(e.target.value)}
            placeholder="Product name"
            className="rounded-xl border border-[var(--border)] px-4 py-3"
          />
          <input
            value={productSku}
            onChange={(e) => setProductSku(e.target.value)}
            placeholder="SKU"
            className="rounded-xl border border-[var(--border)] px-4 py-3"
          />
          <button
            type="button"
            onClick={() => void createProduct()}
            disabled={creating || !productName.trim()}
            className="rounded-xl bg-black px-4 py-3 font-semibold text-white disabled:opacity-50"
          >
            {creating ? "Creating…" : "Create product"}
          </button>
        </div>
      </div>

      <div className="flex flex-wrap gap-2">
        {["All products", "Smartphones", "Accessories", "Serialized"].map(
          (item) => (
            <button
              key={item}
              type="button"
              onClick={() => setFilter(item)}
              className={`rounded-xl px-4 py-2 text-xs font-semibold ${
                filter === item
                  ? "bg-neutral-900 text-white"
                  : "border border-[var(--border)] bg-[var(--surface)] text-neutral-600"
              }`}
            >
              {item}
            </button>
          ),
        )}
      </div>

      {message && (
        <div className="rounded-xl border border-[var(--border)] bg-[var(--surface)] p-4 text-sm">
          {message}
        </div>
      )}

      {loading ? (
        <div className="rounded-2xl border border-[var(--border)] bg-[var(--surface)] p-6 text-sm">
          Loading products…
        </div>
      ) : rows.length === 0 ? (
        <div className="rounded-2xl border border-[var(--border)] bg-[var(--surface)] p-6 text-sm">
          No products found.
        </div>
      ) : (
        <DataTable
          columns={[
            { label: "Product", key: "product" },
            { label: "SKU", key: "sku" },
            { label: "Category", key: "category" },
            { label: "Type", key: "type" },
            { label: "Status", key: "status" },
          ]}
          rows={rows}
        />
      )}
    </div>
  );
}

"use client";

import { FormEvent, useEffect, useMemo, useState } from "react";
import { apiGet, apiPost, apiPatch } from "@/lib/api";
import { useOrganization } from "@/components/organization-provider";
import { PageHeader } from "@/components/page-header";

type Customer = {
  id: string;
  organization_id: string;
  name: string;
  phone?: string;
  email?: string;
  address?: string;
  notes?: string;
  is_active?: boolean;
};

export default function CustomersPage() {
  const { organizationId } = useOrganization();
  const [customers, setCustomers] = useState<Customer[]>([]);
  const [query, setQuery] = useState("");
  const [name, setName] = useState("");
  const [phone, setPhone] = useState("");
  const [email, setEmail] = useState("");
  const [busy, setBusy] = useState(false);
  const [message, setMessage] = useState("");
  const [editingId, setEditingId] = useState<string | null>(null);
  const [editingName, setEditingName] = useState("");
  const [editingPhone, setEditingPhone] = useState("");
  const [editingEmail, setEditingEmail] = useState("");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  async function load() {
    if (!organizationId) return;
    setLoading(true);
    setError("");
    try {
      const data = await apiGet<Customer[]>(
        `/customers?organization_id=${organizationId}`,
      );
      setCustomers(Array.isArray(data) ? data : []);
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : "Unable to load customers.");
    } finally { setLoading(false); }
  }

  useEffect(() => {
    queueMicrotask(() => void load());
  }, [organizationId]);

  async function updateCustomer(id: string) {
    try {
      await apiPatch(`/customers/${id}?organization_id=${organizationId}`, {
        name: editingName.trim(),
        phone: editingPhone.trim(),
        email: editingEmail.trim(),
      });
      setMessage("Customer updated.");
      setEditingId(null);
      await load();
    } catch (cause) {
      setMessage(cause instanceof Error ? cause.message : "Unable to update customer.");
    }
  }

  async function createCustomer(event: FormEvent) {
    event.preventDefault();
    if (!organizationId || !name.trim()) return;

    setBusy(true);
    setMessage("");

    try {
      await apiPost("/customers", {
        organization_id: organizationId,
        name: name.trim(),
        phone: phone.trim(),
        email: email.trim(),
      });

      setName("");
      setPhone("");
      setEmail("");
      setMessage("Customer created.");
      await load();
    } catch (error) {
      setMessage(error instanceof Error ? error.message : "Unable to create customer.");
    } finally {
      setBusy(false);
    }
  }

  const filtered = useMemo(
    () =>
      customers.filter((customer) =>
        `${customer.name} ${customer.phone ?? ""} ${customer.email ?? ""}`
          .toLowerCase()
          .includes(query.toLowerCase()),
      ),
    [customers, query],
  );

  return (
    <div className="space-y-6">
      <PageHeader eyebrow="Customer relationships" title="Customers" description="Customer profiles and purchase relationships for this organization." />

      <div className="grid gap-4 md:grid-cols-3">
        <div className="rounded-2xl border border-[var(--border)] bg-[var(--surface)] shadow-sm p-5">
          <p className="text-sm text-[var(--muted)]">Customers</p>
          <p className="mt-2 text-3xl font-semibold">{customers.length}</p>
        </div>
        <div className="rounded-2xl border border-[var(--border)] bg-[var(--surface)] shadow-sm p-5">
          <p className="text-sm text-[var(--muted)]">Active</p>
          <p className="mt-2 text-3xl font-semibold">
            {customers.filter((item) => item.is_active !== false).length}
          </p>
        </div>
        <div className="rounded-2xl border border-[var(--border)] bg-[var(--surface)] shadow-sm p-5">
          <p className="text-sm text-[var(--muted)]">Search results</p>
          <p className="mt-2 text-3xl font-semibold">{filtered.length}</p>
        </div>
      </div>

      <div className="grid gap-6 lg:grid-cols-[1fr_2fr]">
        <form onSubmit={createCustomer} className="rounded-2xl border border-[var(--border)] bg-[var(--surface)] shadow-sm p-5 space-y-4">
          <div>
            <h2 className="font-semibold">Add customer</h2>
            <p className="text-sm text-[var(--muted)]">Create a customer profile.</p>
          </div>

          <input
            value={name}
            onChange={(e) => setName(e.target.value)}
            placeholder="Full name"
            className="w-full rounded-xl border px-4 py-3"
            required
          />
          <input
            value={phone}
            onChange={(e) => setPhone(e.target.value)}
            placeholder="Phone"
            className="w-full rounded-xl border px-4 py-3"
          />
          <input
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            placeholder="Email"
            type="email"
            className="w-full rounded-xl border px-4 py-3"
          />

          <button
            disabled={busy}
            className="w-full rounded-xl bg-black px-4 py-3 text-white disabled:opacity-50"
          >
            {busy ? "Creating..." : "Create customer"}
          </button>

          {message && <p className="text-sm text-[var(--muted)]">{message}</p>}
        </form>

        <section className="rounded-2xl border border-[var(--border)] bg-[var(--surface)] shadow-sm p-5">
          <div className="mb-4 flex gap-3">
            <input
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              placeholder="Search customers..."
              className="flex-1 rounded-xl border px-4 py-3"
            />
            <button
              onClick={() => void load()}
              className="rounded-xl border px-4 py-3"
            >
              Refresh
            </button>
          </div>

          <div className="overflow-x-auto">
            <table className="w-full text-left text-sm">
              <thead>
                <tr className="border-b text-[var(--muted)]">
                  <th className="px-3 py-3">Name</th>
                  <th className="px-3 py-3">Phone</th>
                  <th className="px-3 py-3">Email</th>
                  <th className="px-3 py-3">Actions</th>
                  <th className="px-3 py-3">Status</th>
                </tr>
              </thead>
              <tbody>
                  {!loading && !error && filtered.map((customer) => (
                    <tr key={customer.id} className="border-b last:border-0">
                    <td className="px-3 py-4 font-medium">{editingId === customer.id ? <input aria-label="Customer name" value={editingName} onChange={(event) => setEditingName(event.target.value)} className="w-40 rounded border p-2" /> : customer.name}</td>
                    <td className="px-3 py-4">{editingId === customer.id ? <input aria-label="Customer phone" value={editingPhone} onChange={(event) => setEditingPhone(event.target.value)} className="w-36 rounded border p-2" /> : customer.phone || "—"}</td>
                    <td className="px-3 py-4">{editingId === customer.id ? <input aria-label="Customer email" type="email" value={editingEmail} onChange={(event) => setEditingEmail(event.target.value)} className="w-48 rounded border p-2" /> : customer.email || "—"}</td>
<td className="px-3 py-4">
  {editingId === customer.id ? <div className="flex gap-2"><button type="button" disabled={busy} onClick={() => void updateCustomer(customer.id)} className="rounded-lg border px-3 py-2 text-xs font-semibold">Save</button><button type="button" onClick={() => setEditingId(null)} className="rounded-lg border px-3 py-2 text-xs">Cancel</button></div> : <button
    type="button"
    onClick={() => { setEditingId(customer.id); setEditingName(customer.name); setEditingPhone(customer.phone ?? ""); setEditingEmail(customer.email ?? ""); }}
    className="rounded-lg border border-[var(--border)] px-3 py-2 text-xs font-semibold"
  >
    Edit
  </button>}
</td>
                    <td className="px-3 py-4">
                      {customer.is_active === false ? "Inactive" : "Active"}
                    </td>
                  </tr>
                  ))}
                  {loading && <tr><td colSpan={5} className="p-6 text-center text-sm text-neutral-500">Loading customers…</td></tr>}
                  {error && <tr><td colSpan={5} className="p-6 text-center text-sm text-red-700">{error} <button type="button" onClick={() => void load()} className="underline">Retry</button></td></tr>}
                  {!loading && !error && filtered.length === 0 && <tr><td colSpan={5} className="p-6 text-center text-sm text-neutral-500">No customers match this search.</td></tr>}
              </tbody>
            </table>
          </div>
        </section>
      </div>
    </div>
  );
}

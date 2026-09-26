"use client";

import { FormEvent, useEffect, useMemo, useState } from "react";
import { apiGet, apiPost } from "@/lib/api";
import { useOrganization } from "@/components/organization-provider";

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

  async function load() {
    if (!organizationId) return;
    try {
      const data = await apiGet<Customer[]>(
        `/customers?organization_id=${organizationId}`,
      );
      setCustomers(Array.isArray(data) ? data : []);
    } catch {
      setCustomers([]);
    }
  }

  useEffect(() => {
    void load();
  }, [organizationId]);

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
      <header>
        <p className="text-sm font-medium text-[var(--muted)]">CRM</p>
        <h1 className="text-3xl font-semibold tracking-tight">Customers</h1>
        <p className="mt-1 text-sm text-[var(--muted)]">
          Manage customer records and purchase relationships.
        </p>
      </header>

      <div className="grid gap-4 md:grid-cols-3">
        <div className="rounded-2xl border bg-white p-5">
          <p className="text-sm text-[var(--muted)]">Customers</p>
          <p className="mt-2 text-3xl font-semibold">{customers.length}</p>
        </div>
        <div className="rounded-2xl border bg-white p-5">
          <p className="text-sm text-[var(--muted)]">Active</p>
          <p className="mt-2 text-3xl font-semibold">
            {customers.filter((item) => item.is_active !== false).length}
          </p>
        </div>
        <div className="rounded-2xl border bg-white p-5">
          <p className="text-sm text-[var(--muted)]">Search results</p>
          <p className="mt-2 text-3xl font-semibold">{filtered.length}</p>
        </div>
      </div>

      <div className="grid gap-6 lg:grid-cols-[1fr_2fr]">
        <form onSubmit={createCustomer} className="rounded-2xl border bg-white p-5 space-y-4">
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

        <section className="rounded-2xl border bg-white p-5">
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
                  <th className="px-3 py-3">Status</th>
                </tr>
              </thead>
              <tbody>
                {filtered.map((customer) => (
                  <tr key={customer.id} className="border-b last:border-0">
                    <td className="px-3 py-4 font-medium">{customer.name}</td>
                    <td className="px-3 py-4">{customer.phone || "—"}</td>
                    <td className="px-3 py-4">{customer.email || "—"}</td>
                    <td className="px-3 py-4">
                      {customer.is_active === false ? "Inactive" : "Active"}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </section>
      </div>
    </div>
  );
}

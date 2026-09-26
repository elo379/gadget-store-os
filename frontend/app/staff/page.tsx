"use client";

import { FormEvent, useEffect, useState } from "react";
import { apiGet, apiPost } from "@/lib/api";
import { useOrganization } from "@/components/organization-provider";

type Staff = {
  id: string;
  user_id?: string;
  organization_id?: string;
  first_name?: string;
  last_name?: string;
  name?: string;
  email?: string;
  phone?: string;
  personnel_id?: string;
  status?: string;
};

export default function StaffPage() {
  const { organizationId } = useOrganization();
  const [staff, setStaff] = useState<Staff[]>([]);
  const [firstName, setFirstName] = useState("");
  const [lastName, setLastName] = useState("");
  const [phone, setPhone] = useState("");
  const [email, setEmail] = useState("");
  const [busy, setBusy] = useState(false);
  const [message, setMessage] = useState("");

  async function load() {
    if (!organizationId) return;
    try {
      const data = await apiGet<Staff[]>(
        `/staff?organization_id=${organizationId}`,
      );
      setStaff(Array.isArray(data) ? data : []);
    } catch {
      setStaff([]);
    }
  }

  useEffect(() => {
    void load();
  }, [organizationId]);

  async function createStaff(event: FormEvent) {
    event.preventDefault();
    if (!organizationId || !firstName.trim()) return;

    setBusy(true);
    setMessage("");

    try {
      await apiPost("/staff", {
        organization_id: organizationId,
        first_name: firstName.trim(),
        last_name: lastName.trim(),
        phone: phone.trim(),
        email: email.trim(),
      });

      setFirstName("");
      setLastName("");
      setPhone("");
      setEmail("");
      setMessage("Staff profile created.");
      await load();
    } catch (error) {
      setMessage(error instanceof Error ? error.message : "Unable to create staff.");
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="space-y-6">
      <header>
        <p className="text-sm font-medium text-[var(--muted)]">People</p>
        <h1 className="text-3xl font-semibold tracking-tight">Staff</h1>
        <p className="mt-1 text-sm text-[var(--muted)]">
          Manage staff profiles and store personnel.
        </p>
      </header>

      <div className="grid gap-6 lg:grid-cols-[1fr_2fr]">
        <form onSubmit={createStaff} className="rounded-2xl border bg-white p-5 space-y-4">
          <h2 className="font-semibold">Create staff profile</h2>

          <input
            value={firstName}
            onChange={(e) => setFirstName(e.target.value)}
            placeholder="First name"
            className="w-full rounded-xl border px-4 py-3"
            required
          />
          <input
            value={lastName}
            onChange={(e) => setLastName(e.target.value)}
            placeholder="Last name"
            className="w-full rounded-xl border px-4 py-3"
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
            {busy ? "Saving..." : "Create profile"}
          </button>

          {message && <p className="text-sm text-[var(--muted)]">{message}</p>}
        </form>

        <section className="rounded-2xl border bg-white p-5">
          <div className="mb-4 flex items-center justify-between">
            <div>
              <h2 className="font-semibold">Personnel</h2>
              <p className="text-sm text-[var(--muted)]">{staff.length} profiles</p>
            </div>
            <button
              onClick={() => void load()}
              className="rounded-xl border px-4 py-2"
            >
              Refresh
            </button>
          </div>

          <div className="overflow-x-auto">
            <table className="w-full text-left text-sm">
              <thead>
                <tr className="border-b text-[var(--muted)]">
                  <th className="px-3 py-3">Name</th>
                  <th className="px-3 py-3">Email</th>
                  <th className="px-3 py-3">Phone</th>
                  <th className="px-3 py-3">Status</th>
                </tr>
              </thead>
              <tbody>
                {staff.map((person) => (
                  <tr key={person.id} className="border-b last:border-0">
                    <td className="px-3 py-4 font-medium">
                      {person.name ||
                        `${person.first_name ?? ""} ${person.last_name ?? ""}`.trim() ||
                        "Unnamed"}
                    </td>
                    <td className="px-3 py-4">{person.email || "—"}</td>
                    <td className="px-3 py-4">{person.phone || "—"}</td>
                    <td className="px-3 py-4">{person.status || "Active"}</td>
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

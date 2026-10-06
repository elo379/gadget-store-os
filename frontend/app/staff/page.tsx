"use client";

import { FormEvent, useEffect, useState } from "react";
import { apiGet, apiPost } from "@/lib/api";
import { useOrganization } from "@/components/organization-provider";
import { PageHeader } from "@/components/page-header";

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
  staff_code?: string;
};

type TimebookRow = { staff_id: string; staff_code: string; date: string; clock_in: string | null; clock_out: string | null; worked_hours: number; late_minutes: number; early_departure_minutes: number; status: string };

export default function StaffPage() {
  const { organizationId } = useOrganization();
  const [staff, setStaff] = useState<Staff[]>([]);
  const [jobTitle, setJobTitle] = useState("");
  const [phone, setPhone] = useState("");
  const [email, setEmail] = useState("");
  const [busy, setBusy] = useState(false);
  const [message, setMessage] = useState("");
  const [month, setMonth] = useState(() => new Date().toISOString().slice(0, 7));
  const [timebook, setTimebook] = useState<TimebookRow[]>([]);
  const [currentUserId, setCurrentUserId] = useState("");
  const [loading, setLoading] = useState(true);
  const [loadError, setLoadError] = useState("");

  async function load() {
    if (!organizationId) return;
    setLoading(true); setLoadError("");
    try {
      const identity = await apiGet<{ user_id: string }>("/auth/me");
      setCurrentUserId(identity.user_id);
      const data = await apiGet<Staff[]>(
        `/staff/${organizationId}`,
      );
      setStaff(Array.isArray(data) ? data : []);
      try { setTimebook(await apiGet<TimebookRow[]>(`/staff/${organizationId}/timebook?month=${month}`)); } catch { setTimebook([]); }
    } catch {
      setStaff([]);
      setLoadError("Staff records could not be loaded.");
    } finally { setLoading(false); }
  }

  async function clockAction(person: Staff, action: "clock-in" | "clock-out") {
    if (!organizationId || !person.id) return;
    setBusy(true);
    setMessage("");
    try {
      await apiPost(`/staff/${organizationId}/${person.id}/${action}`, {});
      setMessage(action === "clock-in" ? "Checked in." : "Checked out.");
      await load();
    } catch (error) {
      setMessage(error instanceof Error ? error.message : "Unable to update attendance.");
    } finally { setBusy(false); }
  }

  useEffect(() => {
    queueMicrotask(() => void load());
  }, [organizationId, month]);

  async function createStaff(event: FormEvent) {
    event.preventDefault();
    if (!organizationId || !email.trim()) return;

    setBusy(true);
    setMessage("");

    try {
      await apiPost("/staff", {
        organization_id: organizationId,
        email: email.trim(),
        phone: phone.trim(),
        job_title: jobTitle.trim(),
      });

      setJobTitle("");
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
      <PageHeader eyebrow="People · Store team" title="Staff" description="Staff access, current status and attendance for this organization." />
      {loadError && <div role="alert" className="rounded-xl border border-red-200 bg-red-50 p-4 text-sm text-red-800">{loadError}<button type="button" onClick={() => void load()} className="ml-2 min-h-10 underline">Retry</button></div>}

      <div className="grid gap-6 lg:grid-cols-[1fr_2fr]">
        <form onSubmit={createStaff} className="rounded-2xl border border-[var(--border)] bg-[var(--surface)] shadow-sm p-5 space-y-4">
          <h2 className="font-semibold">Create staff profile</h2>

          <p className="text-sm text-[var(--muted)]">The email must belong to an active store account. Add new accounts from Settings &gt; Team &amp; Store Tree.</p>
          <input
            value={jobTitle}
            onChange={(e) => setJobTitle(e.target.value)}
            placeholder="Job title"
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

        <section className="rounded-2xl border border-[var(--border)] bg-[var(--surface)] shadow-sm p-5">
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
                  <th className="px-3 py-3">Attendance</th>
                </tr>
              </thead>
              <tbody>
                {staff.map((person) => (
                  <tr key={person.id} className="border-b last:border-0">
                    <td className="px-3 py-4 font-medium">
                      {person.name || person.email ||
                        `${person.first_name ?? ""} ${person.last_name ?? ""}`.trim() ||
                        "Unnamed"}
                    </td>
                    <td className="px-3 py-4">{person.email || "—"}</td>
                    <td className="px-3 py-4">{person.phone || "—"}</td>
                    <td className="px-3 py-4"><span className={`inline-flex rounded-full px-2.5 py-1 text-xs font-semibold capitalize ${person.status === "suspended" || person.status === "revoked" ? "bg-red-50 text-red-800" : person.status === "invited" || person.status === "pending" ? "bg-amber-50 text-amber-900" : "bg-emerald-50 text-emerald-800"}`}>{person.status || "Active"}</span></td>
                    <td className="px-3 py-4">{person.user_id === currentUserId && person.id ? <div className="flex gap-2"><button disabled={busy} onClick={() => void clockAction(person, "clock-in")} className="rounded-lg border px-2 py-1 disabled:opacity-50">Check in</button><button disabled={busy} onClick={() => void clockAction(person, "clock-out")} className="rounded-lg border px-2 py-1 disabled:opacity-50">Check out</button></div> : "—"}</td>
                  </tr>
                ))}
                {!loading && !loadError && staff.length === 0 && <tr><td colSpan={5} className="p-8 text-center text-sm text-[var(--muted)]">No staff profiles are available yet.</td></tr>}
                {loading && <tr><td colSpan={5} role="status" className="p-8 text-center text-sm text-[var(--muted)]">Loading staff records…</td></tr>}
              </tbody>
            </table>
          </div>
        </section>
      </div>

      <section className="rounded-2xl border border-[var(--border)] bg-[var(--surface)] p-5 shadow-sm">
        <div className="flex flex-wrap items-center justify-between gap-3">
          <div><h2 className="font-semibold">Monthly timebook</h2><p className="text-sm text-[var(--muted)]">Worked hours, lateness, early departures, and absences.</p></div>
          <input aria-label="Timebook month" type="month" value={month} onChange={(event) => setMonth(event.target.value)} className="rounded-lg border px-3 py-2" />
        </div>
        <div className="mt-4 overflow-x-auto"><table className="w-full text-left text-sm"><thead><tr className="border-b text-[var(--muted)]"><th className="px-3 py-2">Staff</th><th className="px-3 py-2">Date</th><th className="px-3 py-2">In / Out</th><th className="px-3 py-2">Hours</th><th className="px-3 py-2">Late</th><th className="px-3 py-2">Early</th><th className="px-3 py-2">Status</th></tr></thead><tbody>{timebook.map((row) => <tr key={`${row.staff_id}-${row.date}`} className="border-b last:border-0"><td className="px-3 py-3">{row.staff_code}</td><td className="px-3 py-3">{row.date}</td><td className="px-3 py-3">{row.clock_in ? new Date(row.clock_in).toLocaleTimeString() : "—"} / {row.clock_out ? new Date(row.clock_out).toLocaleTimeString() : "—"}</td><td className="px-3 py-3">{row.worked_hours}</td><td className="px-3 py-3">{row.late_minutes} min</td><td className="px-3 py-3">{row.early_departure_minutes} min</td><td className="px-3 py-3 capitalize">{row.status}</td></tr>)}{timebook.length === 0 ? <tr><td colSpan={7} className="px-3 py-6 text-center text-[var(--muted)]">No timebook entries for this month.</td></tr> : null}</tbody></table></div>
      </section>
    </div>
  );
}

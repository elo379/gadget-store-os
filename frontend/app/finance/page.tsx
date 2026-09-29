"use client";

import { FormEvent, useCallback, useEffect, useState } from "react";
import { apiGet, apiPatch, apiPost } from "@/lib/api";
import { useOrganization } from "@/components/organization-provider";

type Summary = { revenue: number | string; cogs: number | string; gross_profit: number | string; expenses: number | string; operating_result: number | string; payments_received: number | string; customer_outstanding: number | string; supplier_outstanding: number | string; inventory_value: number | string };
type Category = { id: string; name: string };
type Expense = { id: string; amount: number | string; reference_number: string; description: string; status: string; expense_date: string; payment_method: string; actor_id: string | null; category?: { name: string } };
type Reconciliation = { issue_count: number; issues: { code: string; reference: string; detail: string }[] };
const money = (v: number | string | undefined) => `₦${Number(v ?? 0).toLocaleString("en-NG", { minimumFractionDigits: 2 })}`;

export default function FinancePage() {
  const { organizationId } = useOrganization();
  const [summary, setSummary] = useState<Summary | null>(null);
  const [categories, setCategories] = useState<Category[]>([]);
  const [expenses, setExpenses] = useState<Expense[]>([]);
  const [reconciliation, setReconciliation] = useState<Reconciliation>({ issue_count: 0, issues: [] });
  const [error, setError] = useState("");
  const [saving, setSaving] = useState(false);
  const load = useCallback(async () => {
    if (!organizationId) return;
    try {
      const [s, c, e, r] = await Promise.all([
        apiGet<Summary>(`/finance/${organizationId}/summary`),
        apiGet<Category[]>(`/expenses/categories/${organizationId}`),
        apiGet<Expense[]>(`/expenses/${organizationId}`),
        apiGet<Reconciliation>(`/finance/${organizationId}/reconciliation`),
      ]);
      setSummary(s); setCategories(c); setExpenses(e); setReconciliation(r); setError("");
    } catch (err) { setError(err instanceof Error ? err.message : "Unable to load finance records."); }
  }, [organizationId]);
  useEffect(() => {
    const timer = window.setTimeout(() => { void load(); }, 0);
    return () => window.clearTimeout(timer);
  }, [load]);
  async function recordExpense(event: FormEvent<HTMLFormElement>) {
    event.preventDefault(); if (!organizationId) return;
    const formElement = event.currentTarget;
    const form = new FormData(formElement);
    setSaving(true); setError("");
    try {
      await apiPost("/expenses", { organization_id: organizationId, category_id: form.get("category_id"), amount: form.get("amount"), expense_date: form.get("expense_date"), payment_method: form.get("payment_method"), payment_account: form.get("payment_account"), reference_number: form.get("reference_number"), description: form.get("description"), attachment_reference: form.get("attachment_reference") });
      formElement.reset(); await load();
    } catch (err) { setError(err instanceof Error ? err.message : "Expense could not be recorded."); }
    finally { setSaving(false); }
  }
  async function changeStatus(id: string, status: string) {
    if (!organizationId) return;
    try { await apiPatch(`/expenses/${id}/status?organization_id=${organizationId}&status=${status}`, {}); await load(); }
    catch (err) { setError(err instanceof Error ? err.message : "Expense update failed."); }
  }
  const cards = [["Revenue", summary?.revenue], ["Payments received", summary?.payments_received], ["Customer outstanding", summary?.customer_outstanding], ["Supplier outstanding", summary?.supplier_outstanding], ["COGS", summary?.cogs], ["Gross profit", summary?.gross_profit], ["Expenses", summary?.expenses], ["Operating result", summary?.operating_result], ["Inventory value", summary?.inventory_value]] as const;
  return <div className="space-y-6">
    <header><p className="text-sm font-medium text-[var(--muted)]">Finance</p><h1 className="text-3xl font-semibold tracking-tight">Financial controls</h1><p className="mt-1 text-sm text-[var(--muted)]">Revenue less recorded acquisition cost gives gross profit. Operating result deducts recorded expenses.</p></header>
    {error && <div role="alert" className="rounded-xl border border-red-300 bg-red-50 p-3 text-sm text-red-800">{error}</div>}
    <div className="grid gap-3 sm:grid-cols-2 xl:grid-cols-4">{cards.map(([label, value]) => <section key={label} className="rounded-2xl border border-[var(--border)] bg-[var(--surface)] p-4"><p className="text-sm text-[var(--muted)]">{label}</p><p className="mt-2 text-xl font-semibold">{summary ? money(value) : "Loading…"}</p></section>)}</div>
    <section className="rounded-2xl border border-[var(--border)] bg-[var(--surface)] p-5"><div className="mb-3 flex items-center justify-between"><div><h2 className="font-semibold">Reconciliation</h2><p className="text-sm text-[var(--muted)]">Checks ledger payment states and linked events.</p></div><span className="rounded-full px-3 py-1 text-sm">{reconciliation.issue_count} issues</span></div>{reconciliation.issues.length === 0 ? <p className="text-sm text-green-700">No reconciliation issues found.</p> : <ul className="space-y-2">{reconciliation.issues.map((issue, i) => <li key={`${issue.code}-${i}`} className="rounded-lg bg-amber-50 p-3 text-sm"><strong>{issue.code} · {issue.reference}</strong><p>{issue.detail}</p></li>)}</ul>}</section>
    <section className="rounded-2xl border border-[var(--border)] bg-[var(--surface)] p-5"><h2 className="mb-4 font-semibold">Record an expense</h2><form onSubmit={recordExpense} className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
      <label className="text-sm">Category<select required name="category_id" className="mt-1 w-full rounded-lg border p-2">{categories.map(c => <option value={c.id} key={c.id}>{c.name}</option>)}</select></label>
      <label className="text-sm">Amount (₦)<input required min="0.01" step="0.01" type="number" name="amount" className="mt-1 w-full rounded-lg border p-2" /></label>
      <label className="text-sm">Date<input required type="date" name="expense_date" defaultValue={new Date().toISOString().slice(0, 10)} className="mt-1 w-full rounded-lg border p-2" /></label>
      <label className="text-sm">Reference<input required name="reference_number" className="mt-1 w-full rounded-lg border p-2" /></label>
      <label className="text-sm">Payment method<select name="payment_method" className="mt-1 w-full rounded-lg border p-2"><option value="cash">Cash</option><option value="bank_transfer">Bank transfer</option><option value="card">Card</option><option value="mobile_money">Mobile money</option><option value="credit">Unpaid / credit</option></select></label>
      <label className="text-sm">Payment account<input name="payment_account" placeholder="Till, bank, or wallet" className="mt-1 w-full rounded-lg border p-2" /></label>
      <label className="text-sm">Receipt attachment / reference<input name="attachment_reference" className="mt-1 w-full rounded-lg border p-2" /></label>
      <label className="text-sm">Description<input required name="description" className="mt-1 w-full rounded-lg border p-2" /></label>
      <button disabled={saving || !categories.length} className="rounded-xl bg-[var(--foreground)] px-4 py-2 text-[var(--background)] disabled:opacity-50">{saving ? "Saving…" : "Record expense"}</button>
    </form></section>
    <section className="overflow-x-auto rounded-2xl border border-[var(--border)] bg-[var(--surface)] p-5"><h2 className="mb-3 font-semibold">Expense register</h2><table className="w-full text-left text-sm"><thead><tr><th className="p-2">Date / reference</th><th className="p-2">Description</th><th className="p-2">Method</th><th className="p-2">Amount</th><th className="p-2">Status</th><th className="p-2">Action</th></tr></thead><tbody>{expenses.map(e => <tr key={e.id} className="border-t"><td className="p-2">{e.expense_date}<br />{e.reference_number}</td><td className="p-2">{e.description}</td><td className="p-2">{e.payment_method}</td><td className="p-2">{money(e.amount)}</td><td className="p-2">{e.status}</td><td className="p-2">{e.status === "recorded" && <button onClick={() => void changeStatus(e.id, "approved")} className="underline">Approve</button>}{e.status === "approved" && <button onClick={() => void changeStatus(e.id, "paid")} className="underline">Mark paid</button>}</td></tr>)}</tbody></table>{expenses.length === 0 && <p className="py-4 text-sm text-[var(--muted)]">No expenses recorded.</p>}</section>
  </div>;
}

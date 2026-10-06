"use client";

import { useCallback, useEffect, useState } from "react";
import { useOrganization } from "@/components/organization-provider";
import { PageHeader } from "@/components/page-header";
import { apiGet, apiPost } from "@/lib/api";

type Recommendation = { id: string; title: string; reason: string; status: string; action_payload: Record<string, string | null>; resulting_entity_id?: string | null };
type EventRow = { id: string; event_type: string; entity_type: string; created_at: string; payload: Record<string, unknown> };
type CopilotResult = { answer: string; provider: string; supported?: boolean; data: unknown };
type Intelligence = { sales: { revenue: number | string; gross_profit: number | string }; margin_rate: number | string; inventory: { stock_value_at_recorded_average_cost: number | string }; receivables: { total: number | string }; outstanding_purchase_orders: number | string; stockout_risks: { name: string; estimated_days_until_stockout: number | string }[]; dead_stock: { name: string; on_hand: number | string }[] };

export default function CommandCenterPage() {
  const { organizationId } = useOrganization();
  const [recommendations, setRecommendations] = useState<Recommendation[]>([]);
  const [events, setEvents] = useState<EventRow[]>([]);
  const [question, setQuestion] = useState("");
  const [answer, setAnswer] = useState<CopilotResult | null>(null);
  const [intelligence, setIntelligence] = useState<Intelligence | null>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");

  const refresh = useCallback(async () => {
    if (!organizationId) return;
    setError("");
    const [nextRecommendations, nextEvents, nextIntelligence] = await Promise.all([
      apiGet<Recommendation[]>(`/organizations/${organizationId}/automations/recommendations`),
      apiGet<EventRow[]>(`/organizations/${organizationId}/events?limit=20`),
      apiGet<Intelligence>(`/reports/${organizationId}/business-intelligence`),
    ]);
    setRecommendations(nextRecommendations);
    setEvents(nextEvents);
    setIntelligence(nextIntelligence);
  }, [organizationId]);

  useEffect(() => {
    let active = true;
    queueMicrotask(() => { if (active) void refresh().catch((cause: unknown) => { if (active) setError(cause instanceof Error ? cause.message : "Unable to load command center."); }); });
    return () => { active = false; };
  }, [refresh]);

  async function act(operation: () => Promise<unknown>) {
    setBusy(true); setError("");
    try { await operation(); await refresh(); }
    catch (cause) { setError(cause instanceof Error ? cause.message : "The operation could not be completed."); }
    finally { setBusy(false); }
  }

  async function ask(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!organizationId || question.trim().length < 2) return;
    setBusy(true); setError(""); setAnswer(null);
    try { setAnswer(await apiPost<CopilotResult>(`/copilot/${organizationId}/ask`, { question: question.trim() })); }
    catch (cause) { setError(cause instanceof Error ? cause.message : "Unable to answer this question."); }
    finally { setBusy(false); }
  }

  return <main className="space-y-6">
    <PageHeader eyebrow="Owner workspace" title="Business command center" description="Review recorded events, inspect data-backed reorder proposals, and ask questions against authorized GSOS reports." />
    {error && <p role="alert" className="rounded-xl border border-red-200 bg-red-50 p-4 text-sm text-red-800">{error}</p>}
    <section className="rounded-2xl border border-[var(--border)] bg-white p-5 sm:p-6">
      <div className="flex flex-wrap items-center justify-between gap-3"><div><h2 className="text-lg font-semibold">Reorder recommendations</h2><p className="mt-1 text-sm text-neutral-600">Based on current available stock, configured reorder levels, recorded 30-day sales, and purchase history.</p></div>
        <button disabled={busy || !organizationId} onClick={() => void act(() => apiPost(`/organizations/${organizationId}/automations/evaluate`, {}))} className="min-h-11 rounded-xl bg-[var(--accent)] px-4 text-sm font-semibold text-white disabled:opacity-50">{busy ? "Working…" : "Evaluate stock risks"}</button></div>
      {recommendations.length ? <ul className="mt-5 divide-y divide-[var(--border)]">{recommendations.map((row) => <li key={row.id} className="py-4">
        <div className="flex flex-wrap items-start justify-between gap-4"><div className="min-w-0"><p className="font-semibold">{row.title}</p><p className="mt-1 text-sm text-neutral-600">{row.reason}</p><p className="mt-2 text-xs text-neutral-500">Supplier: {row.action_payload.supplier_name ?? "Not established from purchase history"} · Lead time: {row.action_payload.supplier_lead_time_days == null ? "not recorded" : `${row.action_payload.supplier_lead_time_days} days`} · Stockout estimate: {row.action_payload.projected_stockout_days == null ? "not available" : `${row.action_payload.projected_stockout_days} days`} · Quantity: {row.action_payload.quantity ?? "—"} · Estimated cost: {row.action_payload.projected_acquisition_cost ?? "—"} · Projected margin: {row.action_payload.projected_margin ?? "—"}</p></div>
          <div className="flex items-center gap-2"><span className="rounded-full bg-neutral-100 px-3 py-1 text-xs font-semibold capitalize">{row.status}</span>{row.status === "pending" && <><button disabled={busy} onClick={() => void act(() => apiPost(`/organizations/${organizationId}/automations/recommendations/${row.id}/approve`, {}))} className="min-h-10 rounded-lg border px-3 text-sm font-semibold disabled:opacity-50">Approve & create PO</button><button disabled={busy} onClick={() => void act(() => apiPost(`/organizations/${organizationId}/automations/recommendations/${row.id}/reject`, {}))} className="min-h-10 rounded-lg border px-3 text-sm disabled:opacity-50">Reject</button></>}</div></div>
      </li>)}</ul> : <p className="py-10 text-center text-sm text-neutral-500">No recommendations recorded. Evaluate stock risks to calculate proposals from current business data.</p>}
    </section>
    <section className="rounded-2xl border border-[var(--border)] bg-white p-5 sm:p-6"><h2 className="text-lg font-semibold">Business health</h2><p className="mt-1 text-sm text-neutral-600">Calculated from recorded sales, inventory, payments and purchasing.</p>{intelligence ? <div className="mt-4 grid gap-3 sm:grid-cols-2 xl:grid-cols-4"><Health label="30-day revenue" value={intelligence.sales.revenue} /><Health label="30-day gross profit" value={intelligence.sales.gross_profit} /><Health label="Gross margin" value={`${(Number(intelligence.margin_rate) * 100).toFixed(1)}%`} /><Health label="Stock value" value={intelligence.inventory.stock_value_at_recorded_average_cost} /><Health label="Receivables" value={intelligence.receivables.total} /><Health label="Open purchase orders" value={intelligence.outstanding_purchase_orders} /></div> : <p className="mt-4 text-sm text-neutral-500">Business intelligence is unavailable.</p>}<div className="mt-5 grid gap-4 md:grid-cols-2"><InsightList title="Stockout risk (14 days)" rows={intelligence?.stockout_risks.map((row) => `${row.name} · ${Number(row.estimated_days_until_stockout).toFixed(1)} days`) ?? []} /><InsightList title="No sales in 90 days" rows={intelligence?.dead_stock.map((row) => `${row.name} · ${row.on_hand} on hand`) ?? []} /></div></section>
    <section className="rounded-2xl border border-[var(--border)] bg-white p-5 sm:p-6"><h2 className="text-lg font-semibold">GSOS Copilot</h2><p className="mt-1 text-sm text-neutral-600">Uses structured, organization-scoped reports. External AI is not connected.</p><form onSubmit={ask} className="mt-4 flex flex-col gap-3 sm:flex-row"><input value={question} onChange={(event) => setQuestion(event.target.value)} maxLength={500} className="min-h-11 min-w-0 flex-1 rounded-xl border px-3 text-sm" placeholder="Ask about revenue, profit, receivables, low stock, or best sellers" /><button disabled={busy || question.trim().length < 2} className="min-h-11 rounded-xl border px-4 text-sm font-semibold disabled:opacity-50">Ask GSOS</button></form>
      {answer && <div className="mt-4 rounded-xl bg-neutral-50 p-4"><p className="font-medium">{answer.answer}</p><pre className="mt-3 max-h-72 overflow-auto whitespace-pre-wrap break-words text-xs">{JSON.stringify(answer.data, null, 2)}</pre><p className="mt-2 text-xs text-neutral-500">Source: {answer.provider}</p></div>}
    </section>
    <section className="rounded-2xl border border-[var(--border)] bg-white p-5 sm:p-6"><h2 className="text-lg font-semibold">Business events</h2><p className="mt-1 text-sm text-neutral-600">Recent durable events recorded with the business transaction.</p>{events.length ? <ol className="mt-4 divide-y divide-[var(--border)]">{events.map((row) => <li key={row.id} className="flex flex-wrap justify-between gap-2 py-3"><span className="font-medium">{row.event_type.replaceAll("_", " ")}</span><span className="text-xs text-neutral-500">{row.entity_type} · {new Date(row.created_at).toLocaleString()}</span></li>)}</ol> : <p className="py-8 text-center text-sm text-neutral-500">No events have been recorded.</p>}</section>
  </main>;
}

function Health({ label, value }: { label: string; value: number | string }) { const amount = Number(value); const rendered = typeof value === "string" && value.endsWith("%") ? value : Number.isFinite(amount) ? `₦${amount.toLocaleString(undefined, { maximumFractionDigits: 2 })}` : String(value); return <div className="rounded-xl bg-neutral-50 p-4"><p className="text-xs text-neutral-500">{label}</p><p className="mt-2 text-lg font-semibold">{rendered}</p></div>; }
function InsightList({ title, rows }: { title: string; rows: string[] }) { return <div><h3 className="text-sm font-semibold">{title}</h3>{rows.length ? <ul className="mt-2 space-y-1 text-sm text-neutral-600">{rows.slice(0, 5).map((row) => <li key={row}>{row}</li>)}</ul> : <p className="mt-2 text-sm text-neutral-500">No matching products in recorded data.</p>}</div>; }

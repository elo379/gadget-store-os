"use client";

import { useCallback, useEffect, useState } from "react";
import { apiGet } from "@/lib/api";
import { PageHeader } from "@/components/page-header";
import { useOrganization } from "@/components/organization-provider";

type AuditEntry = { id: string; action: string; entity_type: string; entity_id: string | null; description: string; created_at: string; user_id: string | null };

export default function AuditPage() {
  const { organizationId } = useOrganization();
  const [entries, setEntries] = useState<AuditEntry[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const load = useCallback(async () => {
    if (!organizationId) return;
    setLoading(true); setError("");
    try { setEntries(await apiGet<AuditEntry[]>(`/audit/${organizationId}?limit=200`)); }
    catch (e) { setError(e instanceof Error ? e.message : "Audit log could not be loaded."); }
    finally { setLoading(false); }
  }, [organizationId]);
  useEffect(() => { void load(); }, [load]);
  return <div className="space-y-6">
    <PageHeader eyebrow="Control" title="Audit log" description="Server recorded actions for this organization." action={{ label: loading ? "Loading…" : "Refresh", onClick: () => void load() }} />
    {error && <div role="alert" className="rounded-xl bg-red-50 p-4 text-sm text-red-800">{error} <button onClick={() => void load()} className="ml-2 underline">Retry</button></div>}
    <section className="overflow-hidden rounded-2xl border border-[var(--border)] bg-white">
      {loading ? <p className="p-6 text-sm text-neutral-500">Loading audit entries…</p> : entries.length === 0 ? <p className="p-6 text-sm text-neutral-500">No audit entries are available.</p> : <div className="overflow-x-auto"><table className="w-full min-w-[700px] text-left text-sm"><thead className="bg-neutral-50 text-xs text-neutral-500"><tr><th className="p-4">When</th><th className="p-4">Action</th><th className="p-4">Record</th><th className="p-4">Description</th><th className="p-4">Actor</th></tr></thead><tbody>{entries.map((entry) => <tr key={entry.id} className="border-t"><td className="whitespace-nowrap p-4">{new Date(entry.created_at).toLocaleString()}</td><td className="p-4 font-medium">{entry.action}</td><td className="p-4">{entry.entity_type}{entry.entity_id ? <span className="block max-w-48 truncate font-mono text-xs text-neutral-500">{entry.entity_id}</span> : null}</td><td className="max-w-md p-4">{entry.description || "—"}</td><td className="p-4 font-mono text-xs">{entry.user_id || "System"}</td></tr>)}</tbody></table></div>}
    </section>
  </div>;
}

"use client";

import { useCallback, useEffect, useState } from "react";
import { apiGet } from "@/lib/api";
import { PageHeader } from "@/components/page-header";
import { useOrganization } from "@/components/organization-provider";

type AuditEntry = { id: string; organization_id?: string; action: string; entity_type: string; entity_id: string | null; description: string; metadata_json?: string; created_at: string; user_id: string | null };

function recordedAuthority(metadata?: string) {
  try {
    const values = JSON.parse(metadata ?? "{}") as Record<string, unknown>;
    const authority = values.authority ?? values.delegated_authority ?? values.capability ?? values.permission;
    return typeof authority === "string" && authority.trim() ? authority : "Not recorded";
  } catch {
    return "Not recorded";
  }
}

export default function AuditPage() {
  const { organizationId } = useOrganization();
  const [entries, setEntries] = useState<AuditEntry[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [query, setQuery] = useState("");
  const load = useCallback(async () => {
    if (!organizationId) return;
    setLoading(true); setError("");
    try { setEntries(await apiGet<AuditEntry[]>(`/audit/${organizationId}?limit=200`)); }
    catch (e) { setError(e instanceof Error ? e.message : "Audit log could not be loaded."); }
    finally { setLoading(false); }
  }, [organizationId]);
  useEffect(() => { queueMicrotask(() => void load()); }, [load]);
  const filteredEntries = entries.filter((entry) => `${entry.action} ${entry.entity_type} ${entry.entity_id ?? ""} ${entry.description} ${entry.user_id ?? "system"} ${new Date(entry.created_at).toLocaleString()}`.toLowerCase().includes(query.trim().toLowerCase()));
  return <div className="space-y-6">
    <PageHeader eyebrow="Control · Investigation" title="Audit log" description="Trace who changed which record, when, and in which organization. Actor identity and delegated authority stay distinct in the audit detail." action={{ label: loading ? "Loading…" : "Refresh", onClick: () => void load() }} />
    {error && <div role="alert" className="rounded-xl bg-red-50 p-4 text-sm text-red-800">{error} <button onClick={() => void load()} className="ml-2 underline">Retry</button></div>}
    <label className="block max-w-xl text-xs font-semibold text-[var(--muted)]">Filter audit activity<input aria-label="Filter audit entries by actor, action, resource, reason, or time" value={query} onChange={(event) => setQuery(event.target.value)} placeholder="Actor, action, record, reason, date…" className="mt-1 min-h-11 w-full rounded-xl border border-[var(--border)] px-4 text-sm font-normal text-[var(--foreground)]" /></label>
    <section className="overflow-hidden rounded-2xl border border-[var(--border)] bg-white">
      {loading ? <p role="status" className="p-6 text-sm text-neutral-500">Loading audit entries…</p> : entries.length === 0 ? <p className="p-6 text-sm text-neutral-500">No audit entries are available.</p> : filteredEntries.length === 0 ? <p className="p-6 text-sm text-neutral-500">No audit entries match this filter.</p> : <div className="overflow-x-auto"><table className="w-full min-w-[900px] text-left text-sm"><thead className="bg-neutral-50 text-xs text-neutral-500"><tr><th className="p-4">When · UTC</th><th className="p-4">Action</th><th className="p-4">Resource</th><th className="p-4">Reason / details</th><th className="p-4">Actor</th><th className="p-4">Authority</th><th className="p-4">Organization</th></tr></thead><tbody>{filteredEntries.map((entry) => <tr key={entry.id} className="border-t"><td className="whitespace-nowrap p-4">{new Date(entry.created_at).toLocaleString(undefined, { timeZone: "UTC", timeZoneName: "short" })}</td><td className="p-4 font-medium">{entry.action}</td><td className="p-4">{entry.entity_type}{entry.entity_id ? <span className="block max-w-48 truncate font-mono text-xs text-neutral-500">{entry.entity_id}</span> : null}</td><td className="max-w-md p-4">{entry.description || "No reason recorded"}</td><td className="p-4 font-mono text-xs">{entry.user_id || "System"}<span className="mt-1 block font-sans text-[10px] text-[var(--muted)]">Actor</span></td><td className="p-4 text-xs">{recordedAuthority(entry.metadata_json)}</td><td className="p-4 font-mono text-[10px]">{entry.organization_id ?? organizationId}</td></tr>)}</tbody></table></div>}
    </section>
  </div>;
}

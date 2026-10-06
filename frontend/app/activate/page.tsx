"use client";

import { FormEvent, useCallback, useEffect, useState } from "react";
import Link from "next/link";
import { ApiError, apiPost, getMyOrganizations, login } from "@/lib/api";
import { setActiveOrganizationId } from "@/lib/session";

type Invitation = { email: string; organization_id: string; organization_name: string; role_name: string; expires_at: string };
type ActivationState = "entry" | "verifying" | "verified" | "failed" | "activating" | "complete";

function verificationMessage(error: unknown) {
  const detail = error instanceof ApiError ? error.message.toLowerCase() : "";
  if (detail.includes("expired")) return "This activation invitation has expired. Ask an organization owner to issue a new invitation.";
  if (detail.includes("no longer active") || detail.includes("revoked") || detail.includes("accepted")) return "This activation invitation has already been used or revoked. Ask an organization owner for a new invitation.";
  if (detail.includes("invalid") || error instanceof ApiError && error.status === 422) return "This activation link or code is invalid. Check the activation ID and credential, or request a new invitation.";
  return "We could not verify this activation invitation. Please check your connection and try again.";
}

function activationMessage(error: unknown) {
  const detail = error instanceof ApiError ? error.message.toLowerCase() : "";
  if (detail.includes("expired")) return verificationMessage(error);
  if (detail.includes("no longer active") || detail.includes("revoked")) return verificationMessage(error);
  if (detail.includes("password")) return "That password could not be accepted. Use at least 8 characters and try again.";
  return "We could not complete activation. The invitation may have changed; verify it again or request a new one.";
}

export default function ActivatePage() {
  const [activationId, setActivationId] = useState("");
  const [credential, setCredential] = useState("");
  const [password, setPassword] = useState("");
  const [invitation, setInvitation] = useState<Invitation | null>(null);
  const [state, setState] = useState<ActivationState>("entry");
  const [message, setMessage] = useState("");

  const verify = useCallback(async (id: string, token: string) => {
    setInvitation(null);
    setMessage("");
    if (!id.trim() || !token.trim()) {
      setState("entry");
      setMessage("An activation ID and activation credential are required. Use your complete invitation link or enter both values below.");
      return;
    }
    setState("verifying");
    try {
      const result = await apiPost<Invitation>("/organizations/store-tree/invitations/verify", {
        activation_id: id.trim(), token: token.trim(),
      });
      setInvitation(result);
      setState("verified");
    } catch (error) {
      setState("failed");
      setMessage(verificationMessage(error));
    }
  }, []);

  useEffect(() => {
    const query = new URLSearchParams(window.location.search);
    const fragment = new URLSearchParams(window.location.hash.slice(1));
    const id = query.get("activation_id") ?? fragment.get("activation_id") ?? "";
    const token = query.get("token") ?? fragment.get("token") ?? "";
    queueMicrotask(() => {
      if (id) setActivationId(id);
      if (token) setCredential(token);
      if (id && token) void verify(id, token);
    });
  }, [verify]);

  async function verifyForm(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    await verify(activationId, credential);
  }

  async function activate(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!invitation) return;
    setState("activating");
    setMessage("");
    try {
      await apiPost("/organizations/store-tree/invitations/accept", {
        activation_id: activationId.trim(), token: credential.trim(), password,
      });
      // The backend invitation is authoritative for identity and role. Login
      // creates the normal session; the organization is resolved from the
      // resulting authorized membership list.
      await login(invitation.email, password);
      const organizations = await getMyOrganizations();
      const organization = organizations.find((item) => item.organization_id === invitation.organization_id);
      if (!organization) throw new Error("Organization membership could not be resolved.");
      setActiveOrganizationId(organization.organization_id);
      setState("complete");
      window.setTimeout(() => window.location.replace("/"), 500);
    } catch (error) {
      setState("failed");
      setMessage(activationMessage(error));
    }
  }

  const busy = state === "verifying" || state === "activating";
  return (
    <main className="flex min-h-screen items-center justify-center bg-[var(--background)] px-4 py-8 sm:px-6">
      <section className="w-full max-w-[460px] rounded-2xl border border-[var(--border)] bg-white p-5 shadow-sm sm:p-8">
        <div className="mb-7">
          <div className="text-2xl font-bold tracking-[-0.05em]">GSOS</div>
          <p className="mt-1 text-[10px] font-semibold uppercase tracking-[0.2em] text-[var(--muted)]">Gadget Store OS</p>
          <p className="mt-6 text-[11px] font-semibold uppercase tracking-[0.16em] text-[var(--accent)]">Account setup</p>
          <h1 className="mt-2 text-2xl font-semibold tracking-[-0.03em]">Activate your account</h1>
          <p className="mt-2 text-sm leading-6 text-[var(--muted)]">Use your organization invitation to set a permanent password and access your store workspace.</p>
        </div>

        {state === "complete" && invitation ? (
          <div role="status" className="rounded-xl border border-emerald-200 bg-emerald-50 p-4 text-sm leading-6 text-emerald-950">
            Your {invitation.role_name} account for <strong>{invitation.organization_name}</strong> is active. Opening your dashboard…
          </div>
        ) : invitation ? (
          <form onSubmit={activate} className="space-y-5">
            <div role="status" className="rounded-xl border border-emerald-200 bg-emerald-50 p-4 text-sm text-emerald-950">
              Invitation verified for <strong>{invitation.organization_name}</strong> · <strong className="capitalize">{invitation.role_name}</strong><br />{invitation.email}
            </div>
            <label htmlFor="activation-password" className="block text-xs font-semibold">Permanent password
              <input id="activation-password" type="password" autoComplete="new-password" minLength={8} required value={password} onChange={(event) => setPassword(event.target.value)} className="mt-2 h-12 w-full rounded-xl border border-[var(--border)] bg-[#fafaf8] px-4 text-sm font-normal outline-none focus:border-neutral-400" />
            </label>
            {message && <p role="alert" className="rounded-xl border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-800">{message}</p>}
            <button disabled={busy || state === "complete"} className="h-12 w-full rounded-xl bg-neutral-900 text-sm font-semibold text-white disabled:cursor-wait disabled:opacity-60">{state === "activating" ? "Activating…" : "Activate account"}</button>
          </form>
        ) : (
          <form onSubmit={verifyForm} className="space-y-5">
            <p className="rounded-xl bg-neutral-50 p-4 text-sm leading-6 text-neutral-700">An activation invitation is required to continue. Open the complete link you received, or enter its activation ID and credential below.</p>
            <label htmlFor="activation-id" className="block text-xs font-semibold">Activation ID
              <input id="activation-id" autoComplete="off" required value={activationId} onChange={(event) => setActivationId(event.target.value)} className="mt-2 h-12 w-full rounded-xl border border-[var(--border)] bg-[#fafaf8] px-4 text-sm font-normal outline-none focus:border-neutral-400" />
            </label>
            <label htmlFor="activation-credential" className="block text-xs font-semibold">Activation credential
              <input id="activation-credential" type="password" autoComplete="off" required value={credential} onChange={(event) => setCredential(event.target.value)} className="mt-2 h-12 w-full rounded-xl border border-[var(--border)] bg-[#fafaf8] px-4 text-sm font-normal outline-none focus:border-neutral-400" />
            </label>
            {message && <p role="alert" className="rounded-xl border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-800">{message}</p>}
            {state === "verifying" && <p role="status" className="text-sm text-neutral-600">Verifying your activation invitation…</p>}
            <button disabled={busy} className="h-12 w-full rounded-xl bg-neutral-900 text-sm font-semibold text-white disabled:cursor-wait disabled:opacity-60">{busy ? "Verifying…" : "Verify invitation"}</button>
          </form>
        )}
        <p className="mt-6 text-center text-sm text-neutral-600">Already activated? <Link href="/login" className="font-semibold text-emerald-800 underline underline-offset-4">Sign in</Link></p>
      </section>
    </main>
  );
}

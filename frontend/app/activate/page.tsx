"use client";

import { FormEvent, useState } from "react";
import { apiPost, login } from "@/lib/api";

export default function ActivatePage() {
  const [activationId, setActivationId] = useState("");
  const [credential, setCredential] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [message, setMessage] = useState("");
  const [busy, setBusy] = useState(false);

  async function activate(event: FormEvent) {
    event.preventDefault();
    setBusy(true);
    setMessage("");
    try {
      await apiPost("/store-tree/invitations/accept", {
        activation_id: activationId.trim(),
        token: credential.trim(),
        password,
      });
      await login(email.trim(), password);
      window.location.replace("/");
    } catch (error) {
      setMessage(error instanceof Error ? error.message : "Unable to activate this account.");
    } finally {
      setBusy(false);
    }
  }

  return (
    <main className="mx-auto flex min-h-screen max-w-lg items-center px-4 py-10">
      <form onSubmit={activate} className="w-full space-y-4 rounded-2xl border border-zinc-200 bg-white p-6 shadow-sm">
        <div>
          <p className="text-sm font-medium text-zinc-500">GSOS account setup</p>
          <h1 className="mt-1 text-2xl font-semibold">Activate your account</h1>
          <p className="mt-2 text-sm text-zinc-600">Use the one time details supplied by your store manager, then set your permanent password.</p>
        </div>
        <label className="block text-sm font-medium">Activation ID<input required value={activationId} onChange={(e) => setActivationId(e.target.value)} className="mt-1 w-full rounded-xl border px-3 py-3 font-normal" autoComplete="off" /></label>
        <label className="block text-sm font-medium">Activation credential<input required value={credential} onChange={(e) => setCredential(e.target.value)} className="mt-1 w-full rounded-xl border px-3 py-3 font-normal" autoComplete="off" /></label>
        <label className="block text-sm font-medium">Work email<input required type="email" value={email} onChange={(e) => setEmail(e.target.value)} className="mt-1 w-full rounded-xl border px-3 py-3 font-normal" autoComplete="email" /></label>
        <label className="block text-sm font-medium">Permanent password<input required minLength={8} type="password" value={password} onChange={(e) => setPassword(e.target.value)} className="mt-1 w-full rounded-xl border px-3 py-3 font-normal" autoComplete="new-password" /></label>
        {message ? <p role="alert" className="rounded-lg bg-red-50 p-3 text-sm text-red-800">{message}</p> : null}
        <button disabled={busy} className="w-full rounded-xl bg-zinc-950 px-4 py-3 font-medium text-white disabled:opacity-50">{busy ? "Activating…" : "Activate account"}</button>
      </form>
    </main>
  );
}

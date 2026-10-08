"use client";

import { FormEvent, useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { ApiError, apiPost, login } from "@/lib/api";

type CreatedOrganization = { id: string; name: string; slug: string; is_active: boolean };

export default function CreateOrganizationPage() {
  const router = useRouter();
  const [name, setName] = useState("");
  const [slug, setSlug] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [code, setCode] = useState("");
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);

  function updateName(value: string) {
    setName(value);
    setSlug(value.trim().toLowerCase().replace(/[^a-z0-9]+/g, "-").replace(/^-|-$/g, "").slice(0, 100));
  }

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setBusy(true);
    setError("");
    try {
      await apiPost<CreatedOrganization>("/organizations", {
        name: name.trim(),
        slug: slug.trim(),
        owner_email: email.trim(),
        owner_password: password,
        activation_code: code.trim().toUpperCase(),
      });
      await login(email.trim(), password);
      router.replace("/");
    } catch (cause) {
      setError(cause instanceof ApiError ? cause.message : "Unable to activate this organization right now.");
    } finally {
      setBusy(false);
    }
  }

  return (
    <main className="flex min-h-screen items-center justify-center bg-[var(--background)] px-4 py-8 sm:px-6">
      <section className="w-full max-w-[480px] rounded-2xl border border-[var(--border)] bg-white p-6 shadow-sm sm:p-8">
        <div className="text-2xl font-bold tracking-[-0.05em]">GSOS</div>
        <p className="mt-1 text-[10px] font-semibold uppercase tracking-[0.2em] text-[var(--muted)]">Gadget Store OS</p>
        <p className="mt-7 text-[11px] font-semibold uppercase tracking-[0.16em] text-[var(--accent)]">Organization setup</p>
        <h1 className="mt-2 text-2xl font-semibold tracking-[-0.03em]">Create your organization</h1>
        <p className="mt-2 text-sm leading-6 text-[var(--muted)]">Enter your one-time 24-character activation code and create the first owner account.</p>
        <form onSubmit={submit} className="mt-6 space-y-4">
          <label className="block text-xs font-semibold">Organization name
            <input required minLength={2} maxLength={150} value={name} onChange={(event) => updateName(event.target.value)} className="mt-2 h-12 w-full rounded-xl border border-[var(--border)] bg-[#fafaf8] px-4 text-sm font-normal" />
          </label>
          <label className="block text-xs font-semibold">Organization slug
            <input required minLength={2} maxLength={100} value={slug} onChange={(event) => setSlug(event.target.value.toLowerCase())} className="mt-2 h-12 w-full rounded-xl border border-[var(--border)] bg-[#fafaf8] px-4 text-sm font-normal" />
          </label>
          <label className="block text-xs font-semibold">Owner email
            <input type="email" autoComplete="email" required value={email} onChange={(event) => setEmail(event.target.value)} className="mt-2 h-12 w-full rounded-xl border border-[var(--border)] bg-[#fafaf8] px-4 text-sm font-normal" />
          </label>
          <label className="block text-xs font-semibold">Owner password
            <input type="password" autoComplete="new-password" minLength={8} maxLength={128} required value={password} onChange={(event) => setPassword(event.target.value)} className="mt-2 h-12 w-full rounded-xl border border-[var(--border)] bg-[#fafaf8] px-4 text-sm font-normal" />
          </label>
          <label className="block text-xs font-semibold">24-character activation code
            <input autoComplete="off" autoCapitalize="characters" spellCheck={false} required minLength={24} maxLength={24} pattern="[A-Za-z0-9]{24}" value={code} onChange={(event) => setCode(event.target.value.toUpperCase())} className="mt-2 h-12 w-full rounded-xl border border-[var(--border)] bg-[#fafaf8] px-4 font-mono text-sm font-normal tracking-wider" />
          </label>
          {error && <p role="alert" className="rounded-xl border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-800">{error}</p>}
          <button disabled={busy} className="h-12 w-full rounded-xl bg-neutral-900 text-sm font-semibold text-white disabled:cursor-wait disabled:opacity-60">{busy ? "Creating organization…" : "Create organization and sign in"}</button>
        </form>
        <p className="mt-5 text-center text-sm text-neutral-600">Already have an account? <Link href="/login" className="font-semibold text-emerald-800 underline underline-offset-4">Sign in</Link></p>
      </section>
    </main>
  );
}

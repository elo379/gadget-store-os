"use client";

import { FormEvent, useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { ApiError, login } from "@/lib/api";
import {
  authenticateWithPasskey,
  supportsPasskeys,
} from "@/lib/passkeys";

export default function LoginPage() {
  const router = useRouter();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const [passkeyLoading, setPasskeyLoading] = useState(false);
  const [passkeySupported, setPasskeySupported] = useState(false);

  useEffect(() => {
    setPasskeySupported(supportsPasskeys());
  }, []);

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError("");
    setLoading(true);

    try {
      await login(email.trim(), password);
      router.replace("/");
    } catch (err) {
      setError(
        err instanceof ApiError
          ? err.message
          : "Unable to connect to the GSOS server.",
      );
    } finally {
      setLoading(false);
    }
  }

  async function handlePasskey() {
    setError("");
    setPasskeyLoading(true);

    try {
      const result = await authenticateWithPasskey();

      localStorage.setItem("gsos_access_token", result.access_token);
      localStorage.setItem("gsos_refresh_token", result.refresh_token);

      router.replace("/");
    } catch (err) {
      setError(
        err instanceof Error
          ? err.message
          : "Passkey authentication failed.",
      );
    } finally {
      setPasskeyLoading(false);
    }
  }

  return (
    <main className="flex min-h-screen items-center justify-center bg-[var(--background)] px-5 py-10">
      <div className="w-full max-w-[420px]">
        <div className="mb-8">
          <div className="text-2xl font-bold tracking-[-0.05em]">
            GSOS
          </div>
          <p className="mt-1 text-[10px] font-semibold uppercase tracking-[0.2em] text-[var(--muted)]">
            Gadget Store OS
          </p>
        </div>

        <section className="rounded-2xl border border-[var(--border)] bg-white p-6 shadow-sm sm:p-8">
          <div className="mb-7">
            <p className="text-[11px] font-semibold uppercase tracking-[0.16em] text-[var(--accent)]">
              Secure access
            </p>
            <h1 className="mt-2 text-2xl font-semibold tracking-[-0.03em]">
              Welcome back
            </h1>
            <p className="mt-2 text-sm leading-6 text-[var(--muted)]">
              Sign in to access your store workspace.
            </p>
          </div>

          <form onSubmit={handleSubmit} className="space-y-5">
            <div>
              <label
                htmlFor="email"
                className="mb-2 block text-xs font-semibold"
              >
                Email
              </label>
              <input
                id="email"
                type="email"
                autoComplete="username"
                required
                value={email}
                onChange={(event) => setEmail(event.target.value)}
                className="h-12 w-full rounded-xl border border-[var(--border)] bg-[#fafaf8] px-4 text-sm outline-none transition focus:border-neutral-400"
                placeholder="you@example.com"
              />
            </div>

            <div>
              <label
                htmlFor="password"
                className="mb-2 block text-xs font-semibold"
              >
                Password
              </label>
              <input
                id="password"
                type="password"
                autoComplete="current-password"
                required
                value={password}
                onChange={(event) => setPassword(event.target.value)}
                className="h-12 w-full rounded-xl border border-[var(--border)] bg-[#fafaf8] px-4 text-sm outline-none transition focus:border-neutral-400"
                placeholder="Enter your password"
              />
            </div>

            {error && (
              <div className="rounded-xl border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">
                {error}
              </div>
            )}

            <button
              type="submit"
              disabled={loading || passkeyLoading}
              className="h-12 w-full rounded-xl bg-neutral-900 text-sm font-semibold text-white transition hover:bg-neutral-800 disabled:cursor-not-allowed disabled:opacity-60"
            >
              {loading ? "Signing in..." : "Sign in"}
            </button>

            {passkeySupported && (
              <>
                <div className="flex items-center gap-3">
                  <div className="h-px flex-1 bg-[var(--border)]" />
                  <span className="text-[11px] text-[var(--muted)]">
                    OR
                  </span>
                  <div className="h-px flex-1 bg-[var(--border)]" />
                </div>

                <button
                  type="button"
                  onClick={handlePasskey}
                  disabled={loading || passkeyLoading}
                  className="h-12 w-full rounded-xl border border-[var(--border)] bg-[var(--surface)] text-sm font-semibold transition hover:bg-black/[0.03] disabled:cursor-not-allowed disabled:opacity-60"
                >
                  {passkeyLoading
                    ? "Verifying passkey..."
                    : "Sign in with Passkey"}
                </button>
              </>
            )}
          </form>
        </section>

        <p className="mt-6 text-center text-[11px] text-[var(--muted)]">
          Authorized store personnel only.
        </p>
      </div>
    </main>
  );
}

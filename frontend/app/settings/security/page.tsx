"use client";

import { useState } from "react";
import { clearToken } from "@/lib/api";

export default function SecurityPage() {
  const [message, setMessage] = useState("");

  function signOut() {
    clearToken();
    window.location.href = "/login";
  }

  function revokeSessions() {
    setMessage(
      "Local session cleared. Other active sessions require server-side session revocation when enabled.",
    );
  }

  return (
    <div className="space-y-6">
      <header>
        <p className="text-sm font-medium text-[var(--muted)]">Administration</p>
        <h1 className="text-3xl font-semibold tracking-tight">Security</h1>
        <p className="mt-1 text-sm text-[var(--muted)]">
          Manage session and security controls.
        </p>
      </header>

      <section className="rounded-2xl border bg-white p-6">
        <h2 className="font-semibold">Current session</h2>
        <p className="mt-2 text-sm text-[var(--muted)]">
          Your authenticated GSOS session is protected by the application
          authentication layer.
        </p>

        <div className="mt-5 flex flex-wrap gap-3">
          <button
            onClick={revokeSessions}
            className="rounded-xl border px-5 py-3"
          >
            Revoke local session
          </button>

          <button
            onClick={signOut}
            className="rounded-xl bg-black px-5 py-3 text-white"
          >
            Sign out
          </button>
        </div>

        {message && (
          <p className="mt-4 text-sm text-[var(--muted)]">{message}</p>
        )}
      </section>

      <section className="rounded-2xl border bg-white p-6">
        <h2 className="font-semibold">Security principles</h2>

        <div className="mt-4 grid gap-3 md:grid-cols-3">
          {[
            ["Authentication", "Bearer-token authentication protects API access."],
            ["Authorization", "Organization permissions determine available actions."],
            ["Auditability", "Sensitive operational actions are designed to remain traceable."],
          ].map(([title, body]) => (
            <div key={title} className="rounded-xl bg-[var(--background)] p-4">
              <p className="font-medium">{title}</p>
              <p className="mt-1 text-sm text-[var(--muted)]">{body}</p>
            </div>
          ))}
        </div>
      </section>
    </div>
  );
}

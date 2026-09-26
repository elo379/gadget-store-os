"use client";

import { useState } from "react";

export default function BillingPage() {
  const [message, setMessage] = useState("");

  function manage() {
    setMessage(
      "Billing management is prepared for the organization billing provider integration.",
    );
  }

  return (
    <div className="space-y-6">
      <header>
        <p className="text-sm font-medium text-[var(--muted)]">Administration</p>
        <h1 className="text-3xl font-semibold tracking-tight">Billing</h1>
        <p className="mt-1 text-sm text-[var(--muted)]">
          Subscription and organization billing controls.
        </p>
      </header>

      <section className="rounded-2xl border bg-white p-6">
        <div className="flex flex-col gap-5 sm:flex-row sm:items-center sm:justify-between">
          <div>
            <p className="text-sm text-[var(--muted)]">Current plan</p>
            <h2 className="mt-1 text-2xl font-semibold">Store Workspace</h2>
            <p className="mt-1 text-sm text-[var(--muted)]">
              Core store management capabilities.
            </p>
          </div>

          <button
            onClick={manage}
            className="rounded-xl bg-black px-5 py-3 text-white"
          >
            Manage billing
          </button>
        </div>

        {message && (
          <p className="mt-5 rounded-xl bg-[var(--background)] p-4 text-sm text-[var(--muted)]">
            {message}
          </p>
        )}
      </section>

      <div className="grid gap-4 md:grid-cols-3">
        {[
          ["Inventory", "Products, stock and device records."],
          ["Sales", "POS, customers and transaction history."],
          ["Operations", "Purchasing, staff, finance and reporting."],
        ].map(([title, body]) => (
          <div key={title} className="rounded-2xl border bg-white p-5">
            <h2 className="font-semibold">{title}</h2>
            <p className="mt-1 text-sm text-[var(--muted)]">{body}</p>
          </div>
        ))}
      </div>
    </div>
  );
}

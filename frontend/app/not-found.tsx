import Link from "next/link";

export default function NotFound() {
  return (
    <main className="flex min-h-screen items-center justify-center bg-[var(--background)] px-5">
      <section className="w-full max-w-md rounded-2xl border border-[var(--border)] bg-white p-7 text-center shadow-sm">
        <p className="text-[11px] font-semibold uppercase tracking-[0.16em] text-[var(--accent)]">
          GSOS
        </p>

        <h1 className="mt-3 text-2xl font-semibold tracking-[-0.03em]">
          Page not found
        </h1>

        <p className="mt-2 text-sm leading-6 text-[var(--muted)]">
          The workspace page you requested does not exist.
        </p>

        <Link
          href="/"
          className="mt-6 inline-flex h-11 items-center rounded-xl bg-neutral-900 px-5 text-sm font-semibold text-white"
        >
          Return to dashboard
        </Link>
      </section>
    </main>
  );
}

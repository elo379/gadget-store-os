import Link from "next/link";

export default function NotFound() {
  return (
    <main className="flex min-h-[60vh] items-center justify-center px-5 py-10">
      <div className="text-center">
        <p className="text-xs font-semibold uppercase tracking-[0.16em] text-[var(--accent)]">
          GSOS
        </p>
        <h1 className="mt-2 text-3xl font-semibold">
          Page not found
        </h1>
        <p className="mt-2 text-sm text-[var(--muted)]">
          The page you're looking for doesn't exist.
        </p>
        <Link
          href="/"
          className="mt-6 inline-flex rounded-xl bg-black px-5 py-3 text-sm font-semibold text-white"
        >
          Return to dashboard
        </Link>
      </div>
    </main>
  );
}

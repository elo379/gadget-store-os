export default function Loading() {
  return (
    <div className="flex min-h-screen items-center justify-center bg-[var(--background)]">
      <div className="text-center">
        <div className="mx-auto h-8 w-8 animate-pulse rounded-full bg-neutral-900" />
        <p className="mt-4 text-sm text-[var(--muted)]">
          Loading GSOS...
        </p>
      </div>
    </div>
  );
}

import { AppShell } from "@/components/app-shell";
import { Icon } from "@/components/icon";

export default function POSPage() {
  return (
    <AppShell>
      <div className="mb-6 flex items-center justify-between">
        <div>
          <p className="text-[11px] font-semibold uppercase tracking-[0.16em] text-[var(--accent)]">
            Point of sale
          </p>
          <h1 className="mt-2 text-2xl font-semibold tracking-[-0.03em]">
            New sale
          </h1>
        </div>
        <button className="rounded-xl border border-[var(--border)] bg-white px-4 py-2.5 text-sm font-semibold">
          Hold sale
        </button>
      </div>

      <div className="grid gap-5 xl:grid-cols-[1fr_390px]">
        <section className="rounded-2xl border border-[var(--border)] bg-white p-5">
          <div className="flex gap-2">
            <div className="flex h-12 flex-1 items-center gap-3 rounded-xl border border-[var(--border)] bg-[#fafaf8] px-4 text-sm text-neutral-400">
              <Icon name="search" size={18} />
              Search product or scan barcode...
            </div>
            <button className="flex h-12 w-12 items-center justify-center rounded-xl bg-neutral-900 text-white">
              <Icon name="scan" />
            </button>
          </div>

          <div className="mt-6 rounded-xl border border-dashed border-neutral-300 px-6 py-20 text-center">
            <p className="text-sm font-semibold">Cart is empty</p>
            <p className="mt-1 text-xs text-[var(--muted)]">
              Search or scan a product to begin.
            </p>
          </div>
        </section>

        <aside className="rounded-2xl border border-[var(--border)] bg-white p-5">
          <p className="text-sm font-semibold">Order summary</p>

          <div className="mt-8 space-y-3 border-b border-[var(--border)] pb-5 text-sm">
            <div className="flex justify-between">
              <span className="text-[var(--muted)]">Subtotal</span>
              <span>₦0</span>
            </div>
            <div className="flex justify-between">
              <span className="text-[var(--muted)]">Discount</span>
              <span>₦0</span>
            </div>
          </div>

          <div className="flex justify-between py-5 text-lg font-semibold">
            <span>Total</span>
            <span>₦0</span>
          </div>

          <button className="h-12 w-full rounded-xl bg-[var(--accent)] text-sm font-semibold text-white">
            Charge ₦0
          </button>
        </aside>
      </div>
    </AppShell>
  );
}

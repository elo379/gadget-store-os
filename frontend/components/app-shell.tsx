"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { useState } from "react";
import { Icon } from "./icon";
import { AuthGate } from "./auth-gate";
import { clearToken } from "@/lib/api";

const navigation = [
  ["Dashboard", "/", "dashboard"],
  ["Sales", "/sales", "sales"],
  ["Inventory", "/inventory", "inventory"],
  ["Products", "/products", "products"],
  ["Devices & IMEI", "/devices", "scan"],
  ["Purchasing", "/purchasing", "purchasing"],
  ["Customers", "/customers", "customers"],
  ["Staff", "/staff", "staff"],
  ["Finance", "/finance", "finance"],
  ["Reports", "/reports", "reports"],
  ["Settings", "/settings", "settings"],
] as const;

export function AppShell({
  children,
}: {
  children: React.ReactNode;
}) {
  const pathname = usePathname();
  const [open, setOpen] = useState(false);

  const signOut = () => {
    clearToken();
    window.location.href = "/login";
  };

  const sidebar = (
    <aside className="flex h-full w-[250px] flex-col border-r border-[var(--border)] bg-white">
      <div className="flex h-20 items-center border-b border-[var(--border)] px-6">
        <div>
          <div className="text-lg font-bold tracking-[-0.04em]">
            GSOS
          </div>

          <div className="text-[9px] font-semibold uppercase tracking-[0.2em] text-[var(--muted)]">
            Gadget Store OS
          </div>
        </div>
      </div>

      <nav className="flex-1 space-y-1 overflow-y-auto px-3 py-5">
        <p className="px-3 pb-2 text-[10px] font-semibold uppercase tracking-[0.16em] text-neutral-400">
          Workspace
        </p>

        {navigation.map(([label, href, icon]) => {
          const active =
            href === "/"
              ? pathname === "/"
              : pathname.startsWith(href);

          return (
            <Link
              key={href}
              href={href}
              onClick={() => setOpen(false)}
              className={`flex h-10 items-center gap-3 rounded-xl px-3 text-sm font-medium ${
                active
                  ? "bg-[var(--accent-soft)] text-[var(--accent)]"
                  : "text-neutral-600 hover:bg-neutral-50 hover:text-neutral-950"
              }`}
            >
              <Icon name={icon as never} size={17} />
              {label}
            </Link>
          );
        })}
      </nav>

      <div className="border-t border-[var(--border)] p-4">
        <div className="rounded-xl bg-[#f7f7f5] p-3">
          <p className="text-xs font-semibold">Main Store</p>
          <p className="mt-1 text-[11px] text-[var(--muted)]">
            Owner workspace
          </p>
        </div>
      </div>
    </aside>
  );

  return (
    <AuthGate>
      <div className="min-h-screen bg-[var(--background)]">
        <div className="fixed inset-y-0 left-0 hidden lg:flex">
          {sidebar}
        </div>

        {open && (
          <div
            className="fixed inset-0 z-40 bg-black/30 lg:hidden"
            onClick={() => setOpen(false)}
          >
            <div
              className="h-full w-[280px]"
              onClick={(event) => event.stopPropagation()}
            >
              {sidebar}
            </div>
          </div>
        )}

        <div className="lg:pl-[250px]">
          <header className="sticky top-0 z-30 flex h-16 items-center border-b border-[var(--border)] bg-white/95 px-3 backdrop-blur sm:px-6">
            <button
              onClick={() => setOpen(true)}
              className="rounded-lg p-2 lg:hidden"
              aria-label="Open navigation"
            >
              <Icon name="menu" />
            </button>

            <div className="hidden max-w-xl flex-1 lg:block">
              <div className="flex h-10 items-center gap-3 rounded-xl border border-[var(--border)] bg-[#fafaf8] px-3 text-sm text-neutral-400">
                <Icon name="search" size={17} />
                Search products, IMEI, customers, sales...
              </div>
            </div>

            <div className="ml-auto flex items-center gap-2 sm:gap-3">
              <button
                className="rounded-xl border border-[var(--border)] bg-white p-2.5 text-neutral-600"
                aria-label="Notifications"
              >
                <Icon name="bell" size={17} />
              </button>

              <div className="hidden border-l border-[var(--border)] pl-3 text-right sm:block">
                <p className="text-xs font-semibold">Store Owner</p>
                <p className="text-[10px] text-[var(--muted)]">
                  Administrator
                </p>
              </div>

              <button
                onClick={signOut}
                className="flex h-9 w-9 items-center justify-center rounded-full bg-neutral-900 text-xs font-semibold text-white"
                aria-label="Sign out"
                title="Sign out"
              >
                SO
              </button>
            </div>
          </header>

          <main className="mx-auto max-w-[1500px] p-4 sm:p-6 lg:p-8">
            {children}
          </main>
        </div>
      </div>
    </AuthGate>
  );
}

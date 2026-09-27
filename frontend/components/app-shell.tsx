"use client";

import {
  createContext,
  useContext,
  useState,
  type ReactNode,
} from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { Icon, type IconName } from "./icon";

const ShellContext = createContext(false);

type NavItem = {
  label: string;
  href: string;
  icon: IconName;
};

const navItems: NavItem[] = [
  { label: "Dashboard", href: "/", icon: "dashboard" },
  { label: "Sales", href: "/sales", icon: "sales" },
  { label: "POS", href: "/sales/pos", icon: "sales" },
  { label: "Inventory", href: "/inventory", icon: "inventory" },
  { label: "Products", href: "/products", icon: "products" },
  { label: "Devices", href: "/devices", icon: "devices" },
  { label: "Customers", href: "/customers", icon: "customers" },
  { label: "Purchasing", href: "/purchasing", icon: "purchasing" },
  { label: "Staff", href: "/staff", icon: "staff" },
  { label: "Finance", href: "/finance", icon: "finance" },
  { label: "Reports", href: "/reports", icon: "reports" },
  { label: "Settings", href: "/settings", icon: "settings" },
];

export function AppShell({ children }: { children: ReactNode }) {
  const insideShell = useContext(ShellContext);

  if (insideShell) {
    return <>{children}</>;
  }

  return (
    <ShellContext.Provider value={true}>
      <ShellFrame>{children}</ShellFrame>
    </ShellContext.Provider>
  );
}

function ShellFrame({ children }: { children: ReactNode }) {
  const pathname = usePathname();
  const [mobileOpen, setMobileOpen] = useState(false);

  const isActive = (href: string) => {
    if (href === "/") {
      return pathname === "/";
    }

    return pathname === href || pathname.startsWith(`${href}/`);
  };

  return (
    <div className="min-h-screen bg-[var(--background)] text-[var(--foreground)]">
      <aside className="fixed inset-y-0 left-0 z-40 hidden w-[250px] border-r border-[var(--border)] bg-white lg:flex lg:flex-col">
        <div className="flex h-16 items-center border-b border-[var(--border)] px-5">
          <Link
            href="/"
            className="text-base font-bold tracking-[-0.03em]"
          >
            Gadget Store OS
          </Link>
        </div>

        <nav className="flex-1 overflow-y-auto px-3 py-4">
          <div className="space-y-1">
            {navItems.map((item) => (
              <Link
                key={item.href}
                href={item.href}
                className={[
                  "flex h-10 items-center gap-3 rounded-xl px-3 text-sm font-medium transition",
                  isActive(item.href)
                    ? "bg-[var(--accent-soft)] text-[var(--accent)]"
                    : "text-neutral-600 hover:bg-neutral-50 hover:text-neutral-950",
                ].join(" ")}
              >
                <Icon name={item.icon} size={17} />
                <span>{item.label}</span>
              </Link>
            ))}
          </div>
        </nav>

        <div className="border-t border-[var(--border)] p-3">
          <button
            type="button"
            className="flex h-10 w-full items-center rounded-xl px-3 text-sm font-medium text-neutral-600 transition hover:bg-neutral-50 hover:text-neutral-950"
          >
            Sign out
          </button>
        </div>
      </aside>

      {mobileOpen && (
        <button
          type="button"
          aria-label="Close navigation"
          className="fixed inset-0 z-40 bg-black/30 lg:hidden"
          onClick={() => setMobileOpen(false)}
        />
      )}

      <aside
        className={[
          "fixed inset-y-0 left-0 z-50 flex w-[280px] flex-col border-r border-[var(--border)] bg-white transition-transform lg:hidden",
          mobileOpen ? "translate-x-0" : "-translate-x-full",
        ].join(" ")}
      >
        <div className="flex h-16 items-center justify-between border-b border-[var(--border)] px-5">
          <Link
            href="/"
            className="text-base font-bold tracking-[-0.03em]"
            onClick={() => setMobileOpen(false)}
          >
            Gadget Store OS
          </Link>

          <button
            type="button"
            aria-label="Close navigation"
            className="rounded-lg p-2 text-neutral-500 hover:bg-neutral-50 hover:text-neutral-950"
            onClick={() => setMobileOpen(false)}
          >
            <Icon name="arrow-left" size={18} />
          </button>
        </div>

        <nav className="flex-1 overflow-y-auto px-3 py-4">
          <div className="space-y-1">
            {navItems.map((item) => (
              <Link
                key={item.href}
                href={item.href}
                onClick={() => setMobileOpen(false)}
                className={[
                  "flex h-10 items-center gap-3 rounded-xl px-3 text-sm font-medium transition",
                  isActive(item.href)
                    ? "bg-[var(--accent-soft)] text-[var(--accent)]"
                    : "text-neutral-600 hover:bg-neutral-50 hover:text-neutral-950",
                ].join(" ")}
              >
                <Icon name={item.icon} size={17} />
                <span>{item.label}</span>
              </Link>
            ))}
          </div>
        </nav>
      </aside>

      <div className="lg:pl-[250px]">
        <header className="sticky top-0 z-30 flex h-16 items-center border-b border-[var(--border)] bg-white/95 px-4 backdrop-blur sm:px-6">
          <button
            type="button"
            aria-label="Open navigation"
            className="mr-3 rounded-lg p-2 text-neutral-600 hover:bg-neutral-50 lg:hidden"
            onClick={() => setMobileOpen(true)}
          >
            <Icon name="menu" size={20} />
          </button>

          <div className="min-w-0 flex-1">
            <div className="truncate text-sm font-semibold">
              Workspace
            </div>
            <div className="hidden text-[11px] text-neutral-400 sm:block">
              Gadget Store Operations
            </div>
          </div>

          <div className="flex items-center gap-2">
            <button
              type="button"
              aria-label="Search"
              className="rounded-xl p-2 text-neutral-500 transition hover:bg-neutral-50 hover:text-neutral-950"
            >
              <Icon name="search" size={18} />
            </button>

            <button
              type="button"
              aria-label="Notifications"
              className="rounded-xl p-2 text-neutral-500 transition hover:bg-neutral-50 hover:text-neutral-950"
            >
              <Icon name="bell" size={18} />
            </button>
          </div>
        </header>

        <main className="mx-auto w-full max-w-[1500px] px-4 py-6 sm:px-6 lg:px-8">
          {children}
        </main>

        <footer className="mx-auto w-full max-w-[1500px] border-t border-[var(--border)] px-4 py-5 text-center text-xs text-[var(--muted)] sm:px-6 lg:px-8">
          © {new Date().getFullYear()} Gadget Store OS. All rights reserved.
        </footer>
      </div>
    </div>
  );
}

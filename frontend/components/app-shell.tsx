"use client";

import {
  createContext,
  useEffect,
  useContext,
  useRef,
  useState,
  type ReactNode,
} from "react";
import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { Icon, type IconName } from "./icon";
import { apiGet, apiPatch, getMyOrganizations, logout, type Organization } from "@/lib/api";
import { useOrganization } from "@/components/organization-provider";

const ShellContext = createContext(false);

type NavItem = {
  label: string;
  href: string;
  icon: IconName;
};

const navGroups: { label: string; items: NavItem[] }[] = [
  { label: "COMMAND CENTER", items: [{ label: "Dashboard", href: "/", icon: "dashboard" }] },
  { label: "SELL", items: [{ label: "POS", href: "/sales/pos", icon: "sales" }, { label: "Orders & Sales", href: "/sales", icon: "sales" }, { label: "Returns", href: "/returns", icon: "sales" }] },
  { label: "CATALOGUE", items: [{ label: "Products", href: "/products", icon: "products" }, { label: "Categories", href: "/products/categories", icon: "products" }, { label: "Device Registry", href: "/devices", icon: "devices" }] },
  { label: "STOCK", items: [{ label: "Inventory", href: "/inventory", icon: "inventory" }, { label: "Receiving & Purchasing", href: "/purchasing", icon: "purchasing" }, { label: "Suppliers", href: "/suppliers", icon: "purchasing" }] },
  { label: "CUSTOMERS", items: [{ label: "Customers", href: "/customers", icon: "customers" }, { label: "Warranty & Repairs", href: "/aftersales", icon: "customers" }] },
  { label: "PEOPLE", items: [{ label: "Staff & Attendance", href: "/staff", icon: "staff" }, { label: "Permissions", href: "/settings/roles", icon: "settings" }] },
  { label: "FINANCE", items: [{ label: "Finance", href: "/finance", icon: "finance" }] },
  { label: "REPORTS", items: [{ label: "Reports", href: "/reports", icon: "reports" }] },
  { label: "CONTROL", items: [{ label: "Audit Log", href: "/audit", icon: "settings" }, { label: "Organization & Settings", href: "/settings", icon: "settings" }, { label: "Security", href: "/settings/security", icon: "settings" }] },
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
  const router = useRouter();
  const { organizationId, setOrganizationId } = useOrganization();
  const [mobileOpen, setMobileOpen] = useState(false);
  const [searchOpen, setSearchOpen] = useState(false);
  const [search, setSearch] = useState("");
  const [results, setResults] = useState<{id: string; kind: string; label: string; detail?: string | null; href: string}[]>([]);
  const [searchLoading, setSearchLoading] = useState(false);
  const [searchError, setSearchError] = useState(false);
  const [notificationsOpen, setNotificationsOpen] = useState(false);
  const [notifications, setNotifications] = useState<{id: string; title: string; message: string; is_read: boolean}[]>([]);
  const [unreadCount, setUnreadCount] = useState(0);
  const [profileOpen, setProfileOpen] = useState(false);
  const [organizations, setOrganizations] = useState<Organization[]>([]);
  const overlayRef = useRef<HTMLDivElement>(null);
  const searchTriggerRef = useRef<HTMLButtonElement>(null);

  useEffect(() => {
    if (!organizationId) return;
    let active = true;
    apiGet<{unread_count: number}>(`/notifications/${organizationId}/unread-count`)
      .then((data) => { if (active) setUnreadCount(data.unread_count); })
      .catch(() => undefined);
    return () => { active = false; };
  }, [organizationId]);

  useEffect(() => {
    getMyOrganizations().then(setOrganizations).catch(() => setOrganizations([]));
  }, []);

  const activeOrganization = organizations.find((organization) => organization.organization_id === organizationId);

  useEffect(() => {
    if (!searchOpen || !organizationId || search.trim().length < 2) { setResults([]); setSearchLoading(false); setSearchError(false); return; }
    let active = true;
    setSearchLoading(true);
    setSearchError(false);
    const timer = window.setTimeout(() => {
      apiGet<{id: string; kind: string; label: string; detail?: string | null; href: string}[]>(`/search?organization_id=${organizationId}&query=${encodeURIComponent(search.trim())}`)
        .then((data) => { if (active) setResults(Array.isArray(data) ? data : []); })
        .catch(() => { if (active) { setResults([]); setSearchError(true); } })
        .finally(() => { if (active) setSearchLoading(false); });
    }, 200);
    return () => { active = false; window.clearTimeout(timer); };
  }, [organizationId, search, searchOpen]);

  useEffect(() => {
    setSearchOpen(false); setNotificationsOpen(false); setProfileOpen(false); setMobileOpen(false);
  }, [pathname]);

  useEffect(() => {
    if (!searchOpen && !notificationsOpen && !profileOpen) return;
    const onPointerDown = (event: PointerEvent) => {
      if (!overlayRef.current?.contains(event.target as Node)) {
        setSearchOpen(false); setNotificationsOpen(false); setProfileOpen(false);
      }
    };
    const onKeyDown = (event: KeyboardEvent) => {
      if (event.key === "Escape") {
        const searchWasOpen = searchOpen;
        setSearchOpen(false); setNotificationsOpen(false); setProfileOpen(false);
        if (searchWasOpen) searchTriggerRef.current?.focus();
      }
    };
    document.addEventListener("pointerdown", onPointerDown);
    document.addEventListener("keydown", onKeyDown);
    return () => { document.removeEventListener("pointerdown", onPointerDown); document.removeEventListener("keydown", onKeyDown); };
  }, [searchOpen, notificationsOpen, profileOpen]);

  async function toggleNotifications() {
    const opening = !notificationsOpen;
    setNotificationsOpen(opening);
    setSearchOpen(false);
    setProfileOpen(false);
    if (opening && organizationId) {
      try { setNotifications(await apiGet<{id: string; title: string; message: string; is_read: boolean}[]>(`/notifications/${organizationId}`)); }
      catch { setNotifications([]); }
    }
  }

  async function markRead(id: string) {
    if (!organizationId) return;
    try {
      await apiPatch(`/notifications/${organizationId}/${id}/read`, {});
      setNotifications((items) => items.map((item) => item.id === id ? {...item, is_read: true} : item));
      setUnreadCount((count) => Math.max(0, count - 1));
    } catch { /* Keep it unread so the action can be retried. */ }
  }

  const isActive = (href: string) => {
    return pathname === href;
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
          {navGroups.map((group) => <div key={group.label} className="mb-5">
            <p className="px-3 pb-2 text-[10px] font-bold tracking-[.12em] text-neutral-400">{group.label}</p>
            <div className="space-y-1">{group.items.map((item) => (
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
            ))}</div>
          </div>)}
        </nav>

        <div className="border-t border-[var(--border)] p-3">
          <Link href="/settings" className="block truncate px-3 pb-2 text-xs text-neutral-500">{activeOrganization?.name || "Store workspace"}</Link>
          <Link href="/settings/security" className="flex h-10 items-center rounded-xl px-3 text-sm font-medium text-neutral-600 hover:bg-neutral-50">Profile & security</Link>
          <button type="button" onClick={() => void logout()} className="flex h-10 w-full items-center rounded-xl px-3 text-sm font-medium text-neutral-600 hover:bg-neutral-50">Sign out</button>
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
          {navGroups.map((group) => <div key={group.label} className="mb-5">
            <p className="px-3 pb-2 text-[10px] font-bold tracking-[.12em] text-neutral-400">{group.label}</p>
            <div className="space-y-1">{group.items.map((item) => (
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
            ))}</div>
          </div>)}
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
              {activeOrganization?.name || "Store workspace"}
            </div>
            <div className="hidden text-[11px] text-neutral-400 sm:block">
              Gadget Store Operations
            </div>
          </div>

          <div ref={overlayRef} className="relative flex items-center gap-2">
            <button
              type="button"
              ref={searchTriggerRef}
              aria-label="Search"
              aria-expanded={searchOpen}
              aria-haspopup="dialog"
              onClick={() => { setSearchOpen((open) => !open); setNotificationsOpen(false); setProfileOpen(false); }}
              className="rounded-xl p-2 text-neutral-500 transition hover:bg-neutral-50 hover:text-neutral-950"
            >
              <Icon name="search" size={18} />
            </button>
            <button type="button" aria-label="Profile menu" aria-expanded={profileOpen} onClick={() => { setProfileOpen((open) => !open); setSearchOpen(false); setNotificationsOpen(false); }} className="flex h-10 items-center gap-2 rounded-xl border border-[var(--border)] px-3 text-sm font-semibold hover:bg-neutral-50"><span className="grid h-6 w-6 place-items-center rounded-full bg-neutral-900 text-[10px] text-white">GS</span><span className="hidden sm:inline">Profile</span></button>

            <button
              type="button"
              aria-label="Notifications"
              aria-expanded={notificationsOpen}
              onClick={() => void toggleNotifications()}
              className="rounded-xl p-2 text-neutral-500 transition hover:bg-neutral-50 hover:text-neutral-950"
            >
              <Icon name="bell" size={18} />
            </button>
            {unreadCount > 0 && <span className="absolute right-1 top-1 h-2 w-2 rounded-full bg-red-500" />}
            {searchOpen && <div role="dialog" aria-label="Global product search" className="fixed left-3 right-3 top-[4.5rem] z-50 rounded-xl border border-[var(--border)] bg-white p-3 shadow-xl sm:absolute sm:left-auto sm:right-0 sm:top-12 sm:w-[min(24rem,calc(100vw-2rem))]">
              <input autoFocus value={search} onChange={(event) => setSearch(event.target.value)} placeholder="Products, SKU, barcode, IMEI, customers, sales, suppliers" aria-label="Search products, devices, customers, sales and suppliers" className="h-11 w-full rounded-lg border px-3 text-sm" />
              <div className="mt-2 max-h-[min(60vh,24rem)] overflow-auto" aria-live="polite">{search.length < 2 ? <p className="p-2 text-sm text-neutral-500">Type at least 2 characters to search.</p> : searchLoading ? <p className="p-2 text-sm text-neutral-500">Searching workspace…</p> : searchError ? <p role="alert" className="p-2 text-sm text-red-700">Search failed. Try again.</p> : results.length === 0 ? <p className="p-2 text-sm text-neutral-500">No matching records.</p> : results.map((result) => <button key={`${result.kind}-${result.id}`} onClick={() => { setSearchOpen(false); setSearch(""); router.push(result.href); }} className="block min-h-12 w-full rounded-lg p-2 text-left hover:bg-neutral-50 focus-visible:outline focus-visible:outline-2 focus-visible:outline-[var(--accent)]"><span className="float-right rounded-full bg-neutral-100 px-2 py-0.5 text-[10px] font-semibold">{result.kind}</span><span className="block text-sm font-medium">{result.label}</span><span className="text-xs text-neutral-500">{result.detail || ""}</span></button>)}</div>
            </div>}
            {notificationsOpen && <div className="fixed left-3 right-3 top-[4.5rem] z-50 rounded-xl border border-[var(--border)] bg-white p-3 shadow-xl sm:absolute sm:left-auto sm:right-0 sm:top-12 sm:w-80"><p className="px-2 pb-2 text-sm font-semibold">Notifications</p><div className="max-h-[min(65vh,24rem)] overflow-auto">{notifications.length === 0 ? <p className="p-2 text-sm text-neutral-500">No notifications.</p> : notifications.map((item) => <button key={item.id} onClick={() => !item.is_read && void markRead(item.id)} className="block min-h-12 w-full rounded-lg p-2 text-left hover:bg-neutral-50"><span className="block text-sm font-medium">{item.title}{!item.is_read && <span className="ml-2 text-xs text-blue-600">New</span>}</span><span className="text-xs text-neutral-500">{item.message}</span></button>)}</div></div>}
            {profileOpen && <div className="fixed right-3 top-[4.5rem] z-50 w-[min(18rem,calc(100vw-1.5rem))] rounded-xl border border-[var(--border)] bg-white p-2 shadow-xl sm:absolute sm:right-0 sm:top-12"><Link onClick={() => setProfileOpen(false)} href="/settings" className="block min-h-11 rounded-lg px-3 py-3 text-sm hover:bg-neutral-50">Profile</Link><Link onClick={() => setProfileOpen(false)} href="/settings/security" className="block min-h-11 rounded-lg px-3 py-3 text-sm hover:bg-neutral-50">Security</Link>{organizations.length > 1 && <div className="border-t border-neutral-100 py-1">{organizations.map((organization) => <button key={organization.organization_id} onClick={() => { setOrganizationId(organization.organization_id); setProfileOpen(false); window.location.reload(); }} className="block min-h-11 w-full rounded-lg px-3 py-3 text-left text-sm hover:bg-neutral-50">Switch to {organization.name}{organization.organization_id === organizationId ? " · Current" : ""}</button>)}</div>}<button onClick={() => void logout()} className="mt-1 min-h-11 w-full rounded-lg border-t border-neutral-100 px-3 py-3 text-left text-sm text-red-700 hover:bg-red-50">Sign out</button></div>}
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

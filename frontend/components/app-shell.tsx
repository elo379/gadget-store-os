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
  permission?: string;
};

const navGroups: { label: string; items: NavItem[] }[] = [
  { label: "COMMAND CENTER", items: [{ label: "Dashboard", href: "/", icon: "dashboard" }] },
  { label: "SELL", items: [{ label: "Point of Sale", href: "/sales/pos", icon: "sales", permission: "sales.create" }, { label: "Orders", href: "/sales", icon: "sales", permission: "sales.view" }, { label: "Returns", href: "/returns", icon: "sales", permission: "sales.manage" }] },
  { label: "CATALOGUE", items: [{ label: "Products", href: "/products", icon: "products", permission: "products.view" }, { label: "Categories", href: "/products/categories", icon: "products", permission: "products.view" }, { label: "Device Registry", href: "/devices", icon: "devices", permission: "inventory.view" }] },
  { label: "STOCK", items: [{ label: "Inventory", href: "/inventory", icon: "inventory", permission: "inventory.view" }, { label: "Receiving", href: "/operations/receiving", icon: "purchasing", permission: "purchases.view" }, { label: "Transfers", href: "/operations/transfers", icon: "inventory", permission: "inventory.manage" }, { label: "Stock Counts", href: "/operations/counts", icon: "inventory", permission: "inventory.manage" }, { label: "Adjustments", href: "/operations/adjustments", icon: "inventory", permission: "inventory.manage" }, { label: "Low Stock", href: "/operations/low-stock", icon: "inventory", permission: "inventory.view" }] },
  { label: "PROCUREMENT", items: [{ label: "Suppliers", href: "/operations/suppliers", icon: "purchasing", permission: "suppliers.view" }, { label: "Purchase Orders", href: "/purchasing", icon: "purchasing", permission: "purchases.view" }, { label: "Receiving", href: "/operations/receiving", icon: "purchasing", permission: "purchases.view" }] },
  { label: "CUSTOMERS", items: [{ label: "Customers", href: "/customers", icon: "customers", permission: "customers.view" }, { label: "Customer debt", href: "/operations/debt", icon: "finance", permission: "customers.view" }, { label: "Warranty", href: "/operations/warranty", icon: "customers", permission: "customers.view" }, { label: "Repairs", href: "/operations/repairs", icon: "customers", permission: "customers.view" }] },
  { label: "PEOPLE", items: [{ label: "Staff", href: "/staff", icon: "staff", permission: "members.view" }, { label: "Attendance", href: "/operations/attendance", icon: "staff", permission: "attendance.view" }, { label: "Permissions", href: "/settings/roles", icon: "settings", permission: "members.view" }] },
  { label: "FINANCE", items: [{ label: "Financial controls", href: "/finance", icon: "finance", permission: "finance.view" }, { label: "Sales", href: "/operations/finance-sales", icon: "finance", permission: "sales.view" }, { label: "Payments", href: "/operations/payments", icon: "finance", permission: "finance.view" }, { label: "Expenses", href: "/operations/expenses", icon: "finance", permission: "expenses.manage" }, { label: "Profit", href: "/operations/profit", icon: "finance", permission: "finance.view" }] },
  { label: "GROWTH & OPERATIONS", items: [{ label: "Promotions", href: "/operations/promotions", icon: "products", permission: "products.manage" }, { label: "Business insights", href: "/operations/command-center", icon: "reports", permission: "reports.view" }] },
  { label: "REPORTS", items: [{ label: "Sales", href: "/operations/report-sales", icon: "reports", permission: "reports.view" }, { label: "Inventory", href: "/operations/report-inventory", icon: "reports", permission: "reports.view" }, { label: "Customers", href: "/operations/report-customers", icon: "reports", permission: "reports.view" }, { label: "Staff", href: "/operations/report-staff", icon: "reports", permission: "reports.view" }, { label: "Financial", href: "/operations/report-financial", icon: "reports", permission: "reports.view" }] },
  { label: "CONTROL", items: [{ label: "Audit Log", href: "/audit", icon: "settings", permission: "audit.view" }, { label: "Security", href: "/settings/security", icon: "settings" }, { label: "Organization", href: "/settings/team", icon: "settings", permission: "members.view" }, { label: "Settings", href: "/settings", icon: "settings", permission: "organization.manage" }] },
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
  const [notificationError, setNotificationError] = useState("");
  const [unreadCount, setUnreadCount] = useState(0);
  const [profileOpen, setProfileOpen] = useState(false);
  const [organizations, setOrganizations] = useState<Organization[]>([]);
  const [myPermissions, setMyPermissions] = useState<string[]>([]);
  const overlayRef = useRef<HTMLDivElement>(null);
  const searchTriggerRef = useRef<HTMLButtonElement>(null);

  useEffect(() => {
    if (!organizationId) return;
    let active = true;
    apiGet<{ permissions: string[] }>(`/organizations/${organizationId}/my-permissions`)
      .then((data) => { if (active) setMyPermissions(data.permissions); })
      .catch(() => { if (active) setMyPermissions([]); });
    apiGet<{unread_count: number}>(`/notifications/${organizationId}/unread-count`)
      .then((data) => { if (active) setUnreadCount(data.unread_count); })
      .catch((cause) => { if (active) setNotificationError(cause instanceof Error ? cause.message : "Unable to load notification status."); });
    return () => { active = false; };
  }, [organizationId]);

  const visibleNavGroups = navGroups.map((group) => ({ ...group, items: group.items.filter((item) => !item.permission || myPermissions.includes(item.permission)) })).filter((group) => group.items.length > 0);

  useEffect(() => {
    getMyOrganizations().then(setOrganizations).catch(() => setOrganizations([]));
  }, []);

  const activeOrganization = organizations.find((organization) => organization.organization_id === organizationId);

  useEffect(() => {
    if (!searchOpen || !organizationId || search.trim().length < 2) { queueMicrotask(() => { setResults([]); setSearchLoading(false); setSearchError(false); }); return; }
    let active = true;
    queueMicrotask(() => { setSearchLoading(true); setSearchError(false); });
    const timer = window.setTimeout(() => {
      apiGet<{id: string; kind: string; label: string; detail?: string | null; href: string}[]>(`/search?organization_id=${organizationId}&query=${encodeURIComponent(search.trim())}`)
        .then((data) => { if (active) setResults(Array.isArray(data) ? data : []); })
        .catch(() => { if (active) { setResults([]); setSearchError(true); } })
        .finally(() => { if (active) setSearchLoading(false); });
    }, 200);
    return () => { active = false; window.clearTimeout(timer); };
  }, [organizationId, search, searchOpen]);

  useEffect(() => {
    queueMicrotask(() => { setSearchOpen(false); setNotificationsOpen(false); setProfileOpen(false); setMobileOpen(false); });
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

  async function loadNotifications() {
    if (!organizationId) return;
    setNotificationError("");
    try { setNotifications(await apiGet<{id: string; title: string; message: string; is_read: boolean}[]>(`/notifications/${organizationId}`)); }
    catch (cause) { setNotifications([]); setNotificationError(cause instanceof Error ? cause.message : "Unable to load notifications."); }
  }

  async function toggleNotifications() {
    const opening = !notificationsOpen;
    setNotificationsOpen(opening); setSearchOpen(false); setProfileOpen(false);
    if (opening) await loadNotifications();
  }

  async function markRead(id: string) {
    if (!organizationId) return;
    try {
      await apiPatch(`/notifications/${organizationId}/${id}/read`, {});
      setNotifications((items) => items.map((item) => item.id === id ? {...item, is_read: true} : item));
      setUnreadCount((count) => Math.max(0, count - 1));
    } catch (cause) { setNotificationError(cause instanceof Error ? cause.message : "Unable to mark notification as read."); }
  }

  const isActive = (href: string) => {
    return pathname === href;
  };

  return (
    <div className="min-h-screen bg-[var(--background)] text-[var(--foreground)]">
      <aside className="gsos-sidebar fixed inset-y-0 left-0 z-40 hidden w-[260px] border-r lg:flex lg:flex-col">
        <div className="flex h-[4.5rem] items-center gap-3 border-b border-white/10 px-5">
          <span className="gsos-brand-mark" aria-hidden="true"><Icon name="devices" size={17} /></span>
          <div className="min-w-0"><Link href="/" className="block truncate text-sm font-bold tracking-[-0.025em] text-white">Gadget Store OS</Link><span className="mt-0.5 block text-[9px] font-bold tracking-[.18em] text-emerald-200/70">RETAIL OPERATIONS</span></div>
        </div>

        <nav className="flex-1 overflow-y-auto px-3 py-4">
          {visibleNavGroups.map((group) => <div key={group.label} className="mb-5">
            <p className="gsos-nav-label px-3 pb-2 text-[10px] font-bold tracking-[.14em]">{group.label}</p>
            <div className="space-y-1">{group.items.map((item) => (
              <Link
                key={item.href}
                href={item.href}
                className={[
                  "flex min-h-10 items-center gap-3 rounded-xl px-3 text-sm font-medium transition",
                  isActive(item.href)
                    ? "bg-[var(--accent-soft)] text-[var(--accent)]"
                    : "text-neutral-600 hover:bg-neutral-50 hover:text-neutral-950",
                ].join(" ")}
                aria-current={isActive(item.href) ? "page" : undefined}
              >
                <Icon name={item.icon} size={17} />
                <span>{item.label}</span>
              </Link>
            ))}</div>
          </div>)}
        </nav>

        <div className="border-t border-white/10 p-3">
          <Link href="/settings" className="mb-1 block truncate rounded-lg px-3 py-2 text-xs font-semibold text-emerald-100">{activeOrganization?.name || "Store workspace"}</Link>
          <Link href="/settings/security" className="flex min-h-10 items-center rounded-xl px-3 text-sm font-medium">Profile & security</Link>
          <button type="button" onClick={() => void logout()} className="flex min-h-10 w-full items-center rounded-xl px-3 text-sm font-medium">Sign out</button>
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
          "gsos-sidebar fixed inset-y-0 left-0 z-50 flex w-[min(86vw,320px)] flex-col border-r transition-transform lg:hidden",
          mobileOpen ? "translate-x-0" : "-translate-x-full",
        ].join(" ")}
      >
        <div className="flex h-[4.5rem] items-center justify-between border-b border-white/10 px-5">
          <Link
            href="/"
            className="flex items-center gap-3 text-sm font-bold tracking-[-0.025em] text-white"
            onClick={() => setMobileOpen(false)}
          >
            <><span className="gsos-brand-mark" aria-hidden="true"><Icon name="devices" size={17} /></span> Gadget Store OS</>
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
          {visibleNavGroups.map((group) => <div key={group.label} className="mb-5">
            <p className="gsos-nav-label px-3 pb-2 text-[10px] font-bold tracking-[.14em]">{group.label}</p>
            <div className="space-y-1">{group.items.map((item) => (
              <Link
                key={item.href}
                href={item.href}
                onClick={() => setMobileOpen(false)}
                className={[
                  "flex min-h-10 items-center gap-3 rounded-xl px-3 text-sm font-medium transition",
                  isActive(item.href)
                    ? "bg-[var(--accent-soft)] text-[var(--accent)]"
                    : "text-neutral-600 hover:bg-neutral-50 hover:text-neutral-950",
                ].join(" ")}
                aria-current={isActive(item.href) ? "page" : undefined}
              >
                <Icon name={item.icon} size={17} />
                <span>{item.label}</span>
              </Link>
            ))}</div>
          </div>)}
        </nav>
      </aside>

      <div className="lg:pl-[260px]">
        <header className="gsos-topbar sticky top-0 z-30 flex h-[4.5rem] items-center border-b border-[var(--border)] px-4 backdrop-blur sm:px-6">
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
            {notificationsOpen && <div className="fixed left-3 right-3 top-[4.5rem] z-50 rounded-xl border border-[var(--border)] bg-white p-3 shadow-xl sm:absolute sm:left-auto sm:right-0 sm:top-12 sm:w-80"><p className="px-2 pb-2 text-sm font-semibold">Notifications</p>{notificationError && <p role="alert" className="m-2 rounded-lg bg-red-50 p-2 text-xs text-red-700">{notificationError}<button type="button" onClick={() => void loadNotifications()} className="ml-2 underline">Retry</button></p>}<div className="max-h-[min(65vh,24rem)] overflow-auto">{!notificationError && notifications.length === 0 ? <p className="p-2 text-sm text-neutral-500">No notifications.</p> : notifications.map((item) => <button key={item.id} onClick={() => !item.is_read && void markRead(item.id)} className="block min-h-12 w-full rounded-lg p-2 text-left hover:bg-neutral-50"><span className="block text-sm font-medium">{item.title}{!item.is_read && <span className="ml-2 text-xs text-blue-600">New</span>}</span><span className="text-xs text-neutral-500">{item.message}</span></button>)}</div></div>}
            {profileOpen && <div className="fixed right-3 top-[4.5rem] z-50 w-[min(18rem,calc(100vw-1.5rem))] rounded-xl border border-[var(--border)] bg-white p-2 shadow-xl sm:absolute sm:right-0 sm:top-12"><Link onClick={() => setProfileOpen(false)} href="/settings" className="block min-h-11 rounded-lg px-3 py-3 text-sm hover:bg-neutral-50">Profile</Link><Link onClick={() => setProfileOpen(false)} href="/settings/security" className="block min-h-11 rounded-lg px-3 py-3 text-sm hover:bg-neutral-50">Security</Link>{organizations.length > 1 && <div className="border-t border-neutral-100 py-1">{organizations.map((organization) => <button key={organization.organization_id} onClick={() => { setOrganizationId(organization.organization_id); setProfileOpen(false); window.location.reload(); }} className="block min-h-11 w-full rounded-lg px-3 py-3 text-left text-sm hover:bg-neutral-50">Switch to {organization.name}{organization.organization_id === organizationId ? " · Current" : ""}</button>)}</div>}<button onClick={() => void logout()} className="mt-1 min-h-11 w-full rounded-lg border-t border-neutral-100 px-3 py-3 text-left text-sm text-red-700 hover:bg-red-50">Sign out</button></div>}
          </div>
        </header>

        <main className="gsos-main mx-auto w-full max-w-[1560px] px-4 sm:px-6 lg:px-9">
          {children}
        </main>

        <footer className="mx-auto w-full max-w-[1560px] border-t border-[var(--border)] px-4 py-5 text-center text-xs text-[var(--muted)] sm:px-6 lg:px-9">
          <span>© {new Date().getFullYear()} Gadget Store OS. All rights reserved.</span>
          <span className="mx-2 text-[var(--border)]" aria-hidden="true">·</span>
          <span className="font-medium tracking-wide">Powered by EloTech</span>
        </footer>
      </div>
      <nav aria-label="Quick navigation" className="gsos-mobile-dock fixed inset-x-0 bottom-0 z-30 grid grid-cols-5 border-t border-[var(--border)] px-2 pt-2 lg:hidden">
        {[
          { label: "Home", href: "/", icon: "dashboard" as const },
          { label: "Sell", href: "/sales/pos", icon: "sales" as const, permission: "sales.create" },
          { label: "Stock", href: "/inventory", icon: "inventory" as const, permission: "inventory.view" },
          { label: "Devices", href: "/devices", icon: "devices" as const, permission: "inventory.view" },
        ].filter((item) => !item.permission || myPermissions.includes(item.permission)).map((item) => <Link key={item.href} href={item.href} aria-current={isActive(item.href) ? "page" : undefined} className={`flex min-h-12 flex-col items-center justify-center gap-1 rounded-xl text-[10px] font-semibold ${isActive(item.href) ? "text-[var(--accent)]" : "text-[var(--muted)]"}`}><Icon name={item.icon} size={18} /><span>{item.label}</span></Link>)}
        <button type="button" onClick={() => setMobileOpen(true)} aria-label="Open full navigation" className="flex min-h-12 flex-col items-center justify-center gap-1 rounded-xl text-[10px] font-semibold text-[var(--muted)]"><Icon name="menu" size={18} /><span>More</span></button>
      </nav>
    </div>
  );
}

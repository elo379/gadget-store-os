"use client";

type IconName =
  | "dashboard" | "sales" | "inventory" | "products"
  | "purchasing" | "customers" | "staff" | "finance"
  | "reports" | "settings" | "search" | "plus"
  | "scan" | "bell" | "menu";

const paths: Record<IconName, string> = {
  dashboard: "M4 13h6V4H4v9Zm0 7h6v-5H4v5Zm10 0h6v-9h-6v9Zm0-16v5h6V4h-6Z",
  sales: "M5 4h14v16H5V4Zm3 4h8M8 12h8M8 16h5",
  inventory: "M4 7 12 3l8 4-8 4-8-4Zm0 0v10l8 4 8-4V7M12 11v10",
  products: "M6 4h12v16H6V4Zm3 4h6M9 12h6M9 16h4",
  purchasing: "M4 5h16M5 5l1 15h12l1-15M9 9h6M9 13h6",
  customers: "M16 20c0-2.2-1.8-4-4-4H8c-2.2 0-4 1.8-4 4M10 12a4 4 0 1 0 0-8 4 4 0 0 0 0 8M16 8a3 3 0 0 1 0 6",
  staff: "M8 20v-1a4 4 0 0 1 4-4h2a4 4 0 0 1 4 4v1M13 11a3 3 0 1 0 0-6 3 3 0 0 0 0 6M5 20v-1a4 4 0 0 1 3-3",
  finance: "M12 2v20M17 6.5C17 4.6 15 3 12 3S7 4.6 7 6.5 9 9 12 9s5 1.6 5 3.5-2 3.5-5 3.5-5-1.6-5-3.5",
  reports: "M5 20V9M12 20V4M19 20v-7",
  settings: "M12 15.5a3.5 3.5 0 1 0 0-7 3.5 3.5 0 0 0 0 7Z",
  search: "m20 20-4.5-4.5M10.8 17a6.2 6.2 0 1 0 0-12.4 6.2 6.2 0 0 0 0 12.4Z",
  plus: "M12 5v14M5 12h14",
  scan: "M4 8V5a1 1 0 0 1 1-1h3M16 4h3a1 1 0 0 1 1 1v3M20 16v3a1 1 0 0 1-1 1h-3M8 20H5a1 1 0 0 1-1-1v-3",
  bell: "M18 8a6 6 0 0 0-12 0c0 7-3 7-3 9h18c0-2-3-2-3-9M10 21h4",
  menu: "M4 7h16M4 12h16M4 17h16",
};

export function Icon({ name, size = 18 }: { name: IconName; size?: number }) {
  return (
    <svg width={size} height={size} viewBox="0 0 24 24" fill="none"
      stroke="currentColor" strokeWidth="1.7" strokeLinecap="round"
      strokeLinejoin="round" aria-hidden="true">
      <path d={paths[name]} />
    </svg>
  );
}

import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "Purchasing",
  description: "Manage suppliers and purchasing operations.",
};

export default function Layout({ children }: { children: React.ReactNode }) {
  return children;
}

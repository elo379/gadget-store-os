import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "Reports",
  description: "Review operational and business reports.",
};

export default function Layout({ children }: { children: React.ReactNode }) {
  return children;
}

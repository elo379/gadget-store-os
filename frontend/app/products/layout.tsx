import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "Products",
  description: "Manage products, SKUs and catalogue information.",
};

export default function Layout({ children }: { children: React.ReactNode }) {
  return children;
}

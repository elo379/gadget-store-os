import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "Sales",
  description: "Process sales and monitor store transactions.",
};

export default function Layout({ children }: { children: React.ReactNode }) {
  return children;
}

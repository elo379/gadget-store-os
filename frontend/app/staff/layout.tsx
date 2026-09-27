import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "Staff",
  description: "Manage store staff and access.",
};

export default function Layout({ children }: { children: React.ReactNode }) {
  return children;
}

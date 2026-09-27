import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "Customers",
  description: "Manage customer records and purchase relationships.",
};

export default function Layout({ children }: { children: React.ReactNode }) {
  return children;
}

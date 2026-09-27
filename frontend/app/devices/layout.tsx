import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "Devices",
  description: "Search and manage registered device records.",
};

export default function Layout({ children }: { children: React.ReactNode }) {
  return children;
}

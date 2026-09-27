import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "Settings",
  description: "Manage store configuration and preferences.",
};

export default function Layout({ children }: { children: React.ReactNode }) {
  return children;
}

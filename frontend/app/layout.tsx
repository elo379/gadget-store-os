import type { Metadata, Viewport } from "next";
import "./globals.css";
import { WorkspaceProvider } from "@/components/workspace-provider";

export const metadata: Metadata = {
  title: {
    default: "GSOS — Gadget Store OS",
    template: "%s — GSOS",
  },
  description: "Gadget Store Operating System",
  applicationName: "GSOS",
  manifest: "/manifest.webmanifest",
};

export const viewport: Viewport = {
  width: "device-width",
  initialScale: 1,
  viewportFit: "cover",
  themeColor: "#171717",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body><WorkspaceProvider>{children}</WorkspaceProvider></body>
    </html>
  );
}

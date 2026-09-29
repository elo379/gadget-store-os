import type { Metadata, Viewport } from "next";
import { WorkspaceProvider } from "@/components/workspace-provider";
import { ConditionalShell } from "@/components/conditional-shell";
import { AuthGate } from "@/components/auth-gate";
import { OfflineBanner } from "@/components/offline-banner";
import "./globals.css";

export const metadata: Metadata = {
  title: {
    default: "Gadget Store OS",
    template: "%s | Gadget Store OS",
  },
  description:
    "Gadget Store Operations Platform for sales, inventory, products, customers and store management.",
  applicationName: "Gadget Store OS",
  generator: "Next.js",
};

export const viewport: Viewport = {
  width: "device-width",
  initialScale: 1,
  viewportFit: "cover",
  interactiveWidget: "resizes-content",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body>
        <WorkspaceProvider>
          <AuthGate><ConditionalShell>{children}</ConditionalShell></AuthGate>
          <OfflineBanner />
        </WorkspaceProvider>
      </body>
    </html>
  );
}

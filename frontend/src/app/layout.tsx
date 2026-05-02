import type { Metadata } from "next";

import { AppProviders } from "@/components/AppProviders";
import "@/styles/globals.css";

export const metadata: Metadata = {
  title: "Loan Manager",
  description: "Internal loan management system"
};

export default function RootLayout({
  children
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body>
        <AppProviders>{children}</AppProviders>
      </body>
    </html>
  );
}

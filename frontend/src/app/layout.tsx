import type { Metadata } from "next";
import { Geist, Geist_Mono } from "next/font/google";
import { ClerkProvider } from "@clerk/nextjs";
import { SiteHeader } from "@/components/layout/site-header";
import { SiteFooter } from "@/components/layout/site-footer";
import { Toaster } from "@/components/ui/toast";
import { cn } from "@/lib/utils";
import "./globals.css";

const geistSans = Geist({
  variable: "--font-geist-sans",
  subsets: ["latin"],
  display: "swap",
});

const geistMono = Geist_Mono({
  variable: "--font-geist-mono",
  subsets: ["latin"],
  display: "swap",
});

export const metadata: Metadata = {
  metadataBase: new URL(process.env.NEXT_PUBLIC_APP_URL || "http://localhost:3000"),
  title: "AI Build Advisor",
  description: "From idea to production, one decision at a time. A conversational advisor that pressure-tests and architects your AI app before you build it.",
  openGraph: {
    title: "AI Build Advisor",
    description: "From idea to production, one decision at a time. A conversational advisor that pressure-tests and architects your AI app before you build it.",
    url: "https://advisor.example.com",
    siteName: "AI Build Advisor",
    images: [
      {
        url: "/og-image.jpg",
        width: 1200,
        height: 630,
      },
    ],
    locale: "en_US",
    type: "website",
  },
  twitter: {
    card: "summary_large_image",
    title: "AI Build Advisor",
    description: "From idea to production, one decision at a time. A conversational advisor that pressure-tests and architects your AI app before you build it.",
    images: ["/og-image.jpg"],
  },
};

export default function RootLayout({
  children,
}: Readonly<{ children: React.ReactNode }>) {
  return (
    <ClerkProvider>
      <html lang="en" className="dark" suppressHydrationWarning>
        <body
          suppressHydrationWarning
          className={cn(
            geistSans.variable,
            geistMono.variable,
            "min-h-screen flex flex-col bg-background text-foreground antialiased",
          )}
        >
          <SiteHeader />
          <main className="flex-1">{children}</main>
          <SiteFooter />
          <Toaster />
        </body>
      </html>
    </ClerkProvider>
  );
}

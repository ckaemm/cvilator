import type { Metadata } from "next";
import { Inter } from "next/font/google";
import { Navbar } from "@/components/navbar";
import { ToastProvider } from "@/components/toast";
import { ErrorBoundary } from "@/components/error-boundary";
import "./globals.css";

const inter = Inter({ subsets: ["latin"] });

export const metadata: Metadata = {
  title: "CVilator - ATS CV Optimizasyonu",
  description: "AI destekli CV analizi ve ATS optimizasyonu",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="tr" className="dark">
      <body className={inter.className}>
        <ToastProvider>
          <div className="min-h-screen bg-bg-primary">
            <Navbar />
            <main className="mx-auto max-w-7xl px-4 py-6 lg:px-6">
              <ErrorBoundary>{children}</ErrorBoundary>
            </main>
          </div>
        </ToastProvider>
      </body>
    </html>
  );
}

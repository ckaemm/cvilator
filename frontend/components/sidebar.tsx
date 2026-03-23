"use client";

import { useState } from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { LayoutDashboard, FileSearch, History, Menu, X, FileText } from "lucide-react";

const navItems = [
  { href: "/", label: "Dashboard", icon: LayoutDashboard },
  { href: "/analyze", label: "Analiz Et", icon: FileSearch },
  { href: "/history", label: "Geçmiş", icon: History },
];

export function Sidebar() {
  const pathname = usePathname();
  const [mobileOpen, setMobileOpen] = useState(false);

  return (
    <>
      {/* Mobile hamburger */}
      <button
        onClick={() => setMobileOpen(true)}
        className="fixed left-4 top-4 z-40 rounded-lg bg-bg-surface p-2 text-slate-300 shadow-lg lg:hidden hover:text-white transition-colors"
        aria-label="Menüyü aç"
      >
        <Menu className="h-5 w-5" />
      </button>

      {/* Mobile overlay */}
      {mobileOpen && (
        <div
          className="fixed inset-0 z-40 bg-black/50 lg:hidden"
          onClick={() => setMobileOpen(false)}
        />
      )}

      {/* Sidebar */}
      <aside
        className={`fixed inset-y-0 left-0 z-50 flex w-64 flex-col border-r border-slate-700/50 bg-bg-surface transition-transform duration-200
          ${mobileOpen ? "translate-x-0" : "-translate-x-full"} lg:translate-x-0`}
      >
        {/* Logo */}
        <div className="flex h-16 items-center justify-between px-6">
          <Link href="/" className="flex items-center gap-2" onClick={() => setMobileOpen(false)}>
            <FileText className="h-6 w-6 text-accent" />
            <span className="text-lg font-bold text-text-primary">CVilator</span>
          </Link>
          <button
            onClick={() => setMobileOpen(false)}
            className="text-slate-400 hover:text-white lg:hidden"
            aria-label="Menüyü kapat"
          >
            <X className="h-5 w-5" />
          </button>
        </div>

        {/* Nav */}
        <nav className="flex-1 space-y-1 px-3 py-4">
          {navItems.map((item) => {
            const isActive = pathname === item.href;
            return (
              <Link
                key={item.href}
                href={item.href}
                onClick={() => setMobileOpen(false)}
                className={`flex items-center gap-3 rounded-lg px-3 py-2.5 text-sm font-medium transition-colors
                  ${
                    isActive
                      ? "bg-accent/10 text-accent"
                      : "text-slate-400 hover:bg-slate-700/50 hover:text-white"
                  }`}
              >
                <item.icon className="h-5 w-5" />
                {item.label}
              </Link>
            );
          })}
        </nav>

        {/* Footer */}
        <div className="border-t border-slate-700/50 p-4">
          <p className="text-xs text-slate-500">CVilator v0.1.0</p>
        </div>
      </aside>
    </>
  );
}

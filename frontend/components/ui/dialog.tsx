"use client";

import { useEffect, useRef, type ReactNode } from "react";
import { X } from "lucide-react";

interface DialogProps {
  open: boolean;
  onClose: () => void;
  children: ReactNode;
}

function Dialog({ open, onClose, children }: DialogProps) {
  const overlayRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (open) {
      document.body.style.overflow = "hidden";
    } else {
      document.body.style.overflow = "";
    }
    return () => {
      document.body.style.overflow = "";
    };
  }, [open]);

  useEffect(() => {
    function handleEscape(e: KeyboardEvent) {
      if (e.key === "Escape") onClose();
    }
    if (open) {
      document.addEventListener("keydown", handleEscape);
      return () => document.removeEventListener("keydown", handleEscape);
    }
  }, [open, onClose]);

  if (!open) return null;

  return (
    <div
      ref={overlayRef}
      className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm"
      onClick={(e) => {
        if (e.target === overlayRef.current) onClose();
      }}
    >
      <div className="relative mx-4 w-full max-w-lg rounded-xl border border-slate-700 bg-bg-surface p-6 shadow-2xl">
        <button
          onClick={onClose}
          className="absolute right-4 top-4 text-slate-400 hover:text-white transition-colors"
        >
          <X className="h-5 w-5" />
        </button>
        {children}
      </div>
    </div>
  );
}

function DialogTitle({ children, className = "" }: { children: ReactNode; className?: string }) {
  return <h2 className={`text-lg font-semibold text-text-primary ${className}`}>{children}</h2>;
}

function DialogDescription({ children, className = "" }: { children: ReactNode; className?: string }) {
  return <p className={`mt-1 text-sm text-slate-400 ${className}`}>{children}</p>;
}

export { Dialog, DialogTitle, DialogDescription };

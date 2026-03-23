"use client";

import { createContext, useContext, useState, useCallback, type ReactNode } from "react";
import { CheckCircle2, AlertCircle, Info, X } from "lucide-react";

type ToastType = "success" | "error" | "info";

interface Toast {
  id: number;
  type: ToastType;
  message: string;
}

interface ToastContextValue {
  toast: (type: ToastType, message: string) => void;
}

const ToastContext = createContext<ToastContextValue>({ toast: () => {} });

export function useToast() {
  return useContext(ToastContext);
}

let nextId = 0;

export function ToastProvider({ children }: { children: ReactNode }) {
  const [toasts, setToasts] = useState<Toast[]>([]);

  const addToast = useCallback((type: ToastType, message: string) => {
    const id = nextId++;
    setToasts((prev) => [...prev, { id, type, message }]);
    setTimeout(() => {
      setToasts((prev) => prev.filter((t) => t.id !== id));
    }, 3000);
  }, []);

  const removeToast = useCallback((id: number) => {
    setToasts((prev) => prev.filter((t) => t.id !== id));
  }, []);

  return (
    <ToastContext.Provider value={{ toast: addToast }}>
      {children}
      {/* Toast container */}
      <div className="fixed right-4 top-4 z-[100] flex flex-col gap-2 w-80">
        {toasts.map((t) => (
          <div
            key={t.id}
            className={`flex items-start gap-3 rounded-lg border px-4 py-3 shadow-lg animate-fade-in-up
              ${
                t.type === "success"
                  ? "border-success/30 bg-green-950/90 text-green-300"
                  : t.type === "error"
                  ? "border-danger/30 bg-red-950/90 text-red-300"
                  : "border-accent/30 bg-blue-950/90 text-blue-300"
              }`}
          >
            {t.type === "success" && <CheckCircle2 className="mt-0.5 h-4 w-4 shrink-0" />}
            {t.type === "error" && <AlertCircle className="mt-0.5 h-4 w-4 shrink-0" />}
            {t.type === "info" && <Info className="mt-0.5 h-4 w-4 shrink-0" />}
            <p className="flex-1 text-sm">{t.message}</p>
            <button onClick={() => removeToast(t.id)} className="shrink-0 opacity-60 hover:opacity-100">
              <X className="h-4 w-4" />
            </button>
          </div>
        ))}
      </div>
    </ToastContext.Provider>
  );
}

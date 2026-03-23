import type { HTMLAttributes } from "react";

type BadgeVariant = "default" | "success" | "warning" | "danger" | "outline";

interface BadgeProps extends HTMLAttributes<HTMLSpanElement> {
  variant?: BadgeVariant;
}

const variantStyles: Record<BadgeVariant, string> = {
  default: "bg-accent/20 text-blue-400 border-accent/30",
  success: "bg-success/20 text-green-400 border-success/30",
  warning: "bg-warning/20 text-amber-400 border-warning/30",
  danger: "bg-danger/20 text-red-400 border-danger/30",
  outline: "bg-transparent text-slate-300 border-slate-600",
};

function Badge({ variant = "default", className = "", ...props }: BadgeProps) {
  return (
    <span
      className={`inline-flex items-center rounded-full border px-2.5 py-0.5 text-xs font-medium ${variantStyles[variant]} ${className}`}
      {...props}
    />
  );
}

export { Badge };
export type { BadgeProps, BadgeVariant };

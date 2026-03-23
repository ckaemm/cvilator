import type { HTMLAttributes } from "react";

interface CardProps extends HTMLAttributes<HTMLDivElement> {}

function Card({ className = "", ...props }: CardProps) {
  return (
    <div
      className={`rounded-xl border border-slate-700/50 bg-bg-surface shadow-lg ${className}`}
      {...props}
    />
  );
}

function CardHeader({ className = "", ...props }: CardProps) {
  return <div className={`p-6 pb-0 ${className}`} {...props} />;
}

function CardTitle({ className = "", ...props }: CardProps) {
  return <h3 className={`text-lg font-semibold text-text-primary ${className}`} {...props} />;
}

function CardDescription({ className = "", ...props }: CardProps) {
  return <p className={`mt-1 text-sm text-slate-400 ${className}`} {...props} />;
}

function CardContent({ className = "", ...props }: CardProps) {
  return <div className={`p-6 ${className}`} {...props} />;
}

export { Card, CardHeader, CardTitle, CardDescription, CardContent };

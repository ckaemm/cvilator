import type { HTMLAttributes } from "react";

interface CardProps extends HTMLAttributes<HTMLDivElement> {}

function Card({ className = "", ...props }: CardProps) {
  return (
    <div
      className={`rounded-2xl border border-white/5 bg-bg-surface transition-all duration-200 hover:scale-[1.02] hover:shadow-lg hover:shadow-black/20 ${className}`}
      {...props}
    />
  );
}

function CardHeader({ className = "", ...props }: CardProps) {
  return <div className={`p-6 pb-0 ${className}`} {...props} />;
}

function CardTitle({ className = "", ...props }: CardProps) {
  return <h3 className={`text-lg font-bold text-white ${className}`} {...props} />;
}

function CardDescription({ className = "", ...props }: CardProps) {
  return <p className={`mt-1 text-sm text-text-secondary ${className}`} {...props} />;
}

function CardContent({ className = "", ...props }: CardProps) {
  return <div className={`p-6 ${className}`} {...props} />;
}

export { Card, CardHeader, CardTitle, CardDescription, CardContent };

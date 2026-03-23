import { forwardRef, type InputHTMLAttributes } from "react";

interface InputProps extends InputHTMLAttributes<HTMLInputElement> {}

const Input = forwardRef<HTMLInputElement, InputProps>(
  ({ className = "", ...props }, ref) => {
    return (
      <input
        ref={ref}
        className={`w-full rounded-lg border border-slate-600 bg-bg-primary px-3 py-2 text-sm text-text-primary
          placeholder:text-slate-500
          focus:border-accent focus:outline-none focus:ring-1 focus:ring-accent
          disabled:opacity-50 disabled:cursor-not-allowed
          ${className}`}
        {...props}
      />
    );
  }
);

Input.displayName = "Input";
export { Input };

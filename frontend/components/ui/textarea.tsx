import { forwardRef, type TextareaHTMLAttributes } from "react";

interface TextareaProps extends TextareaHTMLAttributes<HTMLTextAreaElement> {}

const Textarea = forwardRef<HTMLTextAreaElement, TextareaProps>(
  ({ className = "", ...props }, ref) => {
    return (
      <textarea
        ref={ref}
        className={`w-full rounded-lg border border-slate-600 bg-bg-primary px-3 py-2 text-sm text-text-primary
          placeholder:text-slate-500
          focus:border-accent focus:outline-none focus:ring-1 focus:ring-accent
          disabled:opacity-50 disabled:cursor-not-allowed
          min-h-[80px] resize-y
          ${className}`}
        {...props}
      />
    );
  }
);

Textarea.displayName = "Textarea";
export { Textarea };

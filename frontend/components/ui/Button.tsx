import { ButtonHTMLAttributes } from "react";
import clsx from "clsx";

type Variant = "primary" | "secondary" | "ghost";

export function Button({
  variant = "secondary",
  className,
  ...props
}: ButtonHTMLAttributes<HTMLButtonElement> & { variant?: Variant }) {
  return (
    <button
      className={clsx(
        "inline-flex items-center justify-center gap-1.5 rounded-lg px-3 py-1.5 text-sm font-medium transition-colors disabled:cursor-not-allowed disabled:opacity-50",
        variant === "primary" && "text-[var(--accent-foreground)] bg-[var(--accent)] hover:opacity-90",
        variant === "secondary" &&
          "border bg-[var(--surface)] text-[var(--foreground)] hover:bg-[var(--surface-muted)]",
        variant === "ghost" && "text-[var(--muted)] hover:text-[var(--foreground)]",
        className
      )}
      style={variant === "secondary" ? { borderColor: "var(--border)" } : undefined}
      {...props}
    />
  );
}

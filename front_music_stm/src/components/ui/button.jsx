import React from "react";

/**
 * Props:
 * - children
 * - className: string (apéndice)
 * - variant: "primary" | "outline" | "ghost" (optional)
 * - size: "sm" | "md" | "lg" (optional)
 * - loading: boolean
 * - ...rest (type, onClick, disabled, etc)
 */
export default function Button({
  children,
  className = "",
  variant = "primary",
  size = "md",
  loading = false,
  disabled = false,
  ...rest
}) {
  // base
  let base = "inline-flex items-center justify-center gap-2 font-medium rounded-md transition-colors focus:outline-none focus:ring-2 focus:ring-offset-2";

  // variant styles (tailwind utilities)
  const variants = {
    primary: "bg-indigo-600 text-white hover:bg-indigo-700 focus:ring-indigo-500",
    outline: "border border-gray-300 bg-white text-gray-800 hover:bg-gray-50 focus:ring-gray-300",
    ghost: "bg-transparent text-gray-800 hover:bg-gray-100 focus:ring-gray-200",
    gradient: "text-white bg-gradient-to-r from-indigo-600 to-pink-500 hover:from-indigo-700 hover:to-pink-600 focus:ring-pink-400"
  };

  // size styles
  const sizes = {
    sm: "text-sm px-3 py-1.5 h-8",
    md: "text-sm px-4 py-2 h-10",
    lg: "text-base px-6 py-3 h-12",
  };

  const cls = `${base} ${variants[variant] ?? variants.primary} ${sizes[size] ?? sizes.md} ${disabled || loading ? "opacity-60 cursor-not-allowed" : ""} ${className}`;

  return (
    <button className={cls} disabled={disabled || loading} {...rest}>
      {loading && (
        <svg className="animate-spin w-4 h-4 mr-2 text-current" viewBox="0 0 24 24" fill="none" aria-hidden>
          <circle cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" opacity="0.25" />
          <path d="M22 12a10 10 0 00-10-10" stroke="currentColor" strokeWidth="4" strokeLinecap="round" />
        </svg>
      )}
      <span>{children}</span>
    </button>
  );
}

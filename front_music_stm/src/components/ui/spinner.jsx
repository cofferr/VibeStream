import React from "react";

export default function Spinner({ size = 16, className = "" }) {
  const s = typeof size === "number" ? `${size}px` : size;
  return (
    <svg className={`animate-spin ${className}`} width={s} height={s} viewBox="0 0 24 24" fill="none" aria-hidden>
      <circle cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" opacity="0.25" />
      <path d="M22 12a10 10 0 00-10-10" stroke="currentColor" strokeWidth="4" strokeLinecap="round" />
    </svg>
  );
}
export { Spinner };

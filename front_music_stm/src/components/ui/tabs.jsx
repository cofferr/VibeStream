import React, { useState } from "react";

export default function Tabs({ children, defaultValue }) {
  // Simple Tab wrapper (expects TabList, TabTrigger, TabContent as children by convention)
  return <div>{children}</div>;
}

/* Simple minimal Tab components for layout — they're uncontrolled for now.
   For complex behavior use @headlessui/react Tab or Radix (but you said minimal). */

export function TabsList({ className = "", children }) {
  return <div className={`inline-flex bg-gray-100 rounded-md p-1 ${className}`}>{children}</div>;
}

export function TabsTrigger({ className = "", children, active = false, onClick }) {
  const base = "px-4 py-2 rounded text-sm font-medium";
  const activeCls = active ? "bg-white shadow-sm" : "text-gray-600";
  return (
    <button className={`${base} ${activeCls} ${className}`} onClick={onClick}>
      {children}
    </button>
  );
}

export function TabsContent({ className = "", children }) {
  return <div className={className}>{children}</div>;
}

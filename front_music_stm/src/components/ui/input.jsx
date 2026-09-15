import React from "react";

const Input = React.forwardRef(({ className = "", type = "text", ...props }, ref) => {
  const base = "block w-full rounded-md border px-3 py-2 text-sm bg-white text-gray-900 placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-indigo-500";
  return <input ref={ref} type={type} className={`${base} ${className}`} {...props} />;
});
Input.displayName = "Input";
export default Input;
export { Input };

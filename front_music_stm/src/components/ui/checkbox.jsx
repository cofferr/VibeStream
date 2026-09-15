import React from "react";

const Checkbox = React.forwardRef(({ className = "", checked, ...props }, ref) => {
  return (
    <input
      ref={ref}
      type="checkbox"
      checked={checked}
      className={`h-4 w-4 rounded-sm border-gray-300 focus:ring-indigo-500 ${className}`}
      {...props}
    />
  );
});
Checkbox.displayName = "Checkbox";
export default Checkbox;
export { Checkbox };

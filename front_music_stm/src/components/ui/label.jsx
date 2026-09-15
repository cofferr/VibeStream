import React from "react";

const Label = React.forwardRef(({ className = "", children, ...props }, ref) => {
  return (
    <label ref={ref} className={`text-sm font-medium text-gray-700 ${className}`} {...props}>
      {children}
    </label>
  );
});
Label.displayName = "Label";
export default Label;
export { Label };

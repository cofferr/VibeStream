import React from "react";

const Card = React.forwardRef(({ className = "", children, ...props }, ref) => {
  return (
    <div ref={ref} className={`bg-white border border-gray-200 rounded-lg shadow-sm ${className}`} {...props}>
      {children}
    </div>
  );
});
Card.displayName = "Card";

const CardHeader = ({ className = "", children }) => (
  <div className={`px-6 py-4 border-b border-gray-100 ${className}`}>{children}</div>
);
const CardContent = ({ className = "", children }) => <div className={`p-6 ${className}`}>{children}</div>;
const CardFooter = ({ className = "", children }) => <div className={`px-6 py-4 border-t border-gray-100 ${className}`}>{children}</div>;
const CardTitle = ({ className = "", children }) => <h3 className={`text-xl font-semibold ${className}`}>{children}</h3>;
const CardDescription = ({ className = "", children }) => <p className={`text-sm text-gray-500 ${className}`}>{children}</p>;

export default Card;
export { Card, CardHeader, CardContent, CardFooter, CardTitle, CardDescription };

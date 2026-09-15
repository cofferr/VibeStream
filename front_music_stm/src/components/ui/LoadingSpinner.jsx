// src/components/common/LoadingSpinner.js
import React from 'react';

const LoadingSpinner = ({ 
  size = 'medium', 
  text = 'Cargando...',
  className = '' 
}) => {
  const sizeClasses = {
    small: 'w-6 h-6',
    medium: 'w-8 h-8',
    large: 'w-12 h-12'
  };

  const textSizes = {
    small: 'text-sm',
    medium: 'text-base',
    large: 'text-lg'
  };

  return (
    <div className={`flex flex-col items-center justify-center p-4 ${className}`}>
      <div 
        className={`
          animate-spin rounded-full border-4 border-gray-600 border-t-purple-500
          ${sizeClasses[size]}
        `}
      ></div>
      {text && (
        <p className={`mt-2 text-gray-400 ${textSizes[size]}`}>
          {text}
        </p>
      )}
    </div>
  );
};

export default LoadingSpinner;
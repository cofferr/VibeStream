// src/components/common/ErrorMessage.js
import React from 'react';
import { AlertCircle, RefreshCw } from 'lucide-react';

const ErrorMessage = ({ 
  message, 
  onRetry, 
  type = 'error',
  className = '' 
}) => {
  const typeStyles = {
    error: {
      bg: 'bg-red-900',
      border: 'border-red-700',
      text: 'text-red-200',
      icon: 'text-red-400'
    },
    warning: {
      bg: 'bg-yellow-900',
      border: 'border-yellow-700',
      text: 'text-yellow-200',
      icon: 'text-yellow-400'
    },
    info: {
      bg: 'bg-blue-900',
      border: 'border-blue-700',
      text: 'text-blue-200',
      icon: 'text-blue-400'
    }
  };

  const styles = typeStyles[type];

  return (
    <div className={`${styles.bg} ${styles.border} border rounded-lg p-4 ${className}`}>
      <div className="flex items-start">
        <AlertCircle className={`flex-shrink-0 mt-0.5 ${styles.icon}`} size={20} />
        <div className="ml-3 flex-1">
          <h3 className={`text-sm font-medium ${styles.text}`}>
            {type === 'error' ? 'Error' : 
             type === 'warning' ? 'Advertencia' : 'Información'}
          </h3>
          <div className={`mt-1 text-sm ${styles.text}`}>
            <p>{message}</p>
          </div>
          {onRetry && (
            <div className="mt-4">
              <button
                type="button"
                onClick={onRetry}
                className={`inline-flex items-center gap-2 px-3 py-2 border border-transparent shadow-sm text-sm font-medium rounded-md text-white ${
                  type === 'error' ? 'bg-red-600 hover:bg-red-700' :
                  type === 'warning' ? 'bg-yellow-600 hover:bg-yellow-700' :
                  'bg-blue-600 hover:bg-blue-700'
                } focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-purple-500`}
              >
                <RefreshCw size={16} />
                Reintentar
              </button>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default ErrorMessage;
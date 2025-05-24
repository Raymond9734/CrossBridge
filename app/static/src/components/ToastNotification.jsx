import React, {  useEffect } from 'react';
import { CheckCircle, AlertCircle, Info, X } from 'lucide-react';

// Toast Notification Component
const Toast = ({ message, type, isVisible, onClose }) => {
    useEffect(() => {
      if (isVisible) {
        const timer = setTimeout(onClose, 3000);
        return () => clearTimeout(timer);
      }
    }, [isVisible, onClose]);
  
    if (!isVisible) return null;
  
    const icons = {
      success: <CheckCircle className="w-5 h-5 text-green-500" />,
      error: <AlertCircle className="w-5 h-5 text-red-500" />,
      info: <Info className="w-5 h-5 text-blue-500" />
    };
  
    const bgColors = {
      success: 'bg-green-50 border-green-200',
      error: 'bg-red-50 border-red-200',
      info: 'bg-blue-50 border-blue-200'
    };
  
    return (
      <div className={`fixed top-4 right-4 z-50 p-4 rounded-lg border ${bgColors[type]} shadow-lg animate-pulse`}>
        <div className="flex items-center gap-3">
          {icons[type]}
          <span className="text-sm font-medium">{message}</span>
          <button onClick={onClose} className="ml-4 text-gray-400 hover:text-gray-600">
            <X className="w-4 h-4" />
          </button>
        </div>
      </div>
    );
};
  
export default Toast;
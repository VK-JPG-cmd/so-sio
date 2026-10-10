import React from 'react';
import { useNotification } from '../../context/NotificationContext';
import { CheckCircle2, AlertCircle, Info, AlertTriangle, X } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';

export const ToastContainer: React.FC = () => {
  const { toasts, removeToast } = useNotification();

  const iconMap = {
    success: <CheckCircle2 className="w-4 h-4 text-[#2F7C5B] shrink-0" />,
    error: <AlertCircle className="w-4 h-4 text-[#C8485E] shrink-0" />,
    warning: <AlertTriangle className="w-4 h-4 text-[#FBF5A5] shrink-0" />,
    info: <Info className="w-4 h-4 text-[#FBF5A5] shrink-0" />,
  };

  const borderMap = {
    success: 'border-[#2F7C5B]/50',
    error: 'border-[#C8485E]/50',
    warning: 'border-[#FBF5A5]/60',
    info: 'border-[#434346]',
  };

  return (
    <div className="fixed bottom-6 right-6 z-50 flex flex-col gap-2 max-w-sm w-full pointer-events-none">
      <AnimatePresence>
        {toasts.map((toast) => (
          <motion.div
            key={toast.id}
            initial={{ opacity: 0, y: 16, scale: 0.95 }}
            animate={{ opacity: 1, y: 0, scale: 1 }}
            exit={{ opacity: 0, scale: 0.95, transition: { duration: 0.15 } }}
            className={`pointer-events-auto p-4 rounded-2xl bg-[#111312] text-[#F7F7F6] border ${borderMap[toast.type]} shadow-2xl flex items-start gap-3`}
          >
            {iconMap[toast.type]}
            <div className="flex-1 min-w-0">
              <h5 className="text-xs font-bold text-white tracking-tight">{toast.title}</h5>
              {toast.message && (
                <p className="text-xs text-[#9A9B9C] mt-0.5 leading-relaxed">{toast.message}</p>
              )}
            </div>
            <button
              onClick={() => removeToast(toast.id)}
              className="text-[#9A9B9C] hover:text-[#FBF5A5] p-1 rounded-lg hover:bg-[#222423] transition-colors"
            >
              <X className="w-3.5 h-3.5" />
            </button>
          </motion.div>
        ))}
      </AnimatePresence>
    </div>
  );
};

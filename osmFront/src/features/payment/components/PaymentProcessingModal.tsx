"use client";
import { PaymentProcessingModalProps } from "../types";

export default function PaymentProcessingModal({
  isOpen,
  message = "Processing your payment..."
}: PaymentProcessingModalProps) {
  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-black/10 flex items-center justify-center z-50">
      <div className="bg-white rounded-xl shadow-lg p-6 flex flex-col items-center gap-4 w-[300px]">
        
        {/* Spinner */}
        <div className="w-12 h-12 border-4 border-blue-500 border-t-transparent rounded-full animate-spin"></div>
        
        {/* Message */}
        <p className="text-gray-700 font-medium text-center">{message}</p>
      </div>
    </div>
  );
}

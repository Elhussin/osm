"use client";

import { useState } from "react";
import { axiosInstance } from "@/src/shared/api/axios";
import { getBaseUrl } from "@/src/shared/utils/getBaseUrl";
import { apiConfig } from "@/src/shared/api/apiConfig";
import { PayPalButtonProps } from "../types";
import PaymentProcessingModal from "./PaymentProcessingModal";
import { useTranslations } from "next-intl";
export default function PayPalButton({ clientId, planId, planDirection, label, method }: PayPalButtonProps) {
  const t = useTranslations('paymantPage');
  const [loading, setLoading] = useState(false);

  const createOrder = async () => {
    try {
      setLoading(true);
      apiConfig.ignoreSubdomain = true;

      const baseUrl = getBaseUrl(undefined, apiConfig.ignoreSubdomain);
      const res = await axiosInstance.post(
        `${baseUrl}/api/tenants/create-payment-order/`,
        {
          client_id: clientId,
          plan_id: planId,
          direction: planDirection,
          method: method?.toLowerCase() || "paypal"
        }
      );

      const data = res.data;
      console.log("PayPal Order Response:", data);

      if (data.approval_url && data.order_id) {
        // حفظ order_id في localStorage أو SessionStorage لاستخدامه لاحقًا في PayPalProcessingPage
        sessionStorage.setItem("paypal_order_id", data.order_id);

        // توجيه المستخدم مباشرة إلى PayPal للموافقة
        window.location.href = data.approval_url;
      } else {
        console.error("Failed to create PayPal order", data);
        alert("Failed to create PayPal order");
      }
    } catch (err) {
      console.error("Error creating PayPal order", err);
    } finally {
      setLoading(false);
    }
  };

  return (
    <button
      onClick={createOrder}
      disabled={loading}
      className="w-full py-2 px-4 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50"
    >
      {loading ? 
            <PaymentProcessingModal isOpen={true} message={t('processing')} />
      : label || `${planDirection}`}
    </button>
  );
}

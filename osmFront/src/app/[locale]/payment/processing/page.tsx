"use client";
import { useEffect, useState } from "react";
import { Loader2 } from "lucide-react";
import { useSearchParams, useRouter } from "next/navigation";
import { axiosInstance } from "@/src/shared/api/axios";
import { getBaseUrl } from "@/src/shared/utils/getBaseUrl";
import { apiConfig } from "@/src/shared/api/apiConfig";

export default function PayPalProcessingPage() {
  const searchParams = useSearchParams();
  const router = useRouter();
  const [status, setStatus] = useState<"loading" | "error">("loading");

  useEffect(() => {
    const orderId = searchParams.get("orderID") || searchParams.get("token");
    const clientId = searchParams.get("client_id");
    const planID = searchParams.get("plan");
    const direction = searchParams.get("direction");
    const duration = searchParams.get("duration");
    const state = searchParams.get("status");

    
    if (state === "cancelled") {
      router.replace("/payment/cancel");
      return;
    }

    if (!orderId || !clientId || !planID) {
      router.replace("/payment/fail");
      return;
    }

    const executePayment = async () => {
      try {
        apiConfig.ignoreSubdomain = true;
        const baseUrl = getBaseUrl(undefined, apiConfig.ignoreSubdomain);

        const res = await axiosInstance.post(
          `${baseUrl}/api/tenants/paypal/execute/`,
          {
            order_id: orderId,
            client_id: clientId,
            plan_id: planID,
            direction: direction,
            duration: duration,
          }
        );

        if (res.status === 200) {
          router.replace("/payment/success");
        } else {
          setStatus("error");
          router.replace("/payment/fail");
        }
      } catch (error) {
        console.log("error", error);
        setStatus("error");
        router.replace("/payment/fail");
      }
    };

    executePayment();
  }, [searchParams, router]);

  return (
    <div className="min-h-screen flex flex-col justify-center items-center bg-gray-50 p-6">
      <Loader2 className="w-12 h-12 text-blue-600 animate-spin mb-4" />
      <h1 className="text-2xl font-bold text-gray-800">
        Processing your payment...
      </h1>
      <p className="text-gray-600 mt-2 text-center max-w-sm">
        Please wait while we confirm your payment with PayPal.
      </p>
    </div>
  );
}

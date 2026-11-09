"use client";

import { useSearchParams } from "next/navigation";
import Paymant from "@/src/features/payment/components/Paymant";
export default function PaymentPage() {
  const searchParams = useSearchParams();
  const planId = searchParams.get("planId");
  const amount = searchParams.get("amount");
  const planName = searchParams.get("planName");
  const clientId = searchParams.get("clientId");
  const planDirection = searchParams.get("planDirection");
  return (
    <>
    {planId && amount && planName && clientId &&planDirection&&
      <Paymant
      planId={planId}
      amount={amount}
      planName={planName}
      clientId={clientId}
      planDirection={planDirection}
    />
    }
    </>
  );

}

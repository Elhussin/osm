// app/paypal/success/page.tsx
"use client";

import Link from "next/link";
import { CheckCircle } from "lucide-react";

export default function PayPalSuccessPage() {
  return (
    <div className="min-h-screen flex flex-col justify-center items-center bg-green-50 p-6">
      <CheckCircle className="text-green-600 w-20 h-20 mb-4" />
      <h1 className="text-3xl font-bold text-green-700">Payment Successful!</h1>
      <p className="text-gray-700 mt-2 text-center max-w-md">
        Thank you for your payment. Your subscription has been activated successfully.
      </p>
      <Link
        href="/dashboard"
        className="mt-6 px-6 py-3 bg-green-600 text-white rounded-lg shadow hover:bg-green-700 transition"
      >
        Go to Dashboard
      </Link>
    </div>
  );
}

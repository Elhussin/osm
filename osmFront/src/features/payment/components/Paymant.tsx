import { useUser } from "@/src/features/auth/hooks/UserContext";
import { useState} from "react";
import PayPalButton from "./PayPalButton";
import { useTranslations } from "next-intl";
import { PayPalButtonProps } from "../types";
import {bankDetial,contact,paymentMethods} from '@/src/shared/constants/conteact';



export default function Payment(props:PayPalButtonProps) {
  const {planId,amount,planName,clientId,planDirection} = props;
  const { user } = useUser();
  const t = useTranslations('paymantPage');
  const [paymentMethod, setPaymentMethod] = useState<"paypal" | "stripe" | "cash" | "bank" | "other">("paypal");
  return (
    <div className="min-h-screen flex items-center justify-center bg-surface p-6">
      <div className="w-full max-w-lg bg-body rounded-2xl shadow-lg p-6 space-y-6">
        
        {/* العنوان */}
        <h1 className="text-2xl font-bold text-center text-main">{t('title')}</h1>

        {/* تفاصيل الخطة */}
        <div className="bg-surface rounded-xl p-4 space-y-2">
          <h2 className="text-lg font-semibold">{t('plan')}: <span className="text-primary capitalize">{planName}</span></h2>
          <p>{t('duration')}: <span className="capitalize text-primary"> {planDirection}</span></p>
          <p className="text-xl font-bold text-green-600">${amount}</p>
        </div>

        {/* اختيار طريقة الدفع */}
        <div>
          <h3 className="font-semibold mb-2">{t('choosePlan')}</h3>
          <div className="grid grid-cols-2 gap-3">
            {paymentMethods.map((method) => (
              <button
                key={method.value}
                onClick={() => setPaymentMethod(method.value as any)}
                className={`flex items-center justify-center gap-2 border rounded-lg p-3 text-sm font-medium transition ${
                  paymentMethod === method.value
                    ? "border-blue-500 bg-blue-50 text-blue-600"
                    : "border-gray-300 hover:bg-gray-100"
                }`}
              >
                <span>{method.icon}</span>
                {method.label}
              </button>
            ))}
          </div>
        </div>

        {/* عرض الزر حسب الاختيار */}
        <div className="mt-4">
          {paymentMethod === "paypal" && user?.client && planId && 
            
                <PayPalButton
                  clientId={clientId}
                  planId={planId}
                  planDirection={planDirection}
                  label={t('paypal')}
                />
              
            }


          {paymentMethod === "stripe" && (
            <p className="text-gray-600 text-center">{t('stripe')}</p>
          )}

          {paymentMethod === "cash" && (
            <p className="text-gray-600 text-center">{t('cash')}</p>
          )}

          {paymentMethod === "bank" && (
            <div className="text-sm text-gray-700">
              <p>{t('bankName')}: {bankDetial.bankName}</p>
              <p>{t('accountNumber')}: {bankDetial.accountNumber}</p>
              <p>{t('iban')}: {bankDetial.iban}</p>
            </div>
          )}

          {paymentMethod === "other" && (
            <>
            <p className="text-gray-600 text-center">{t('other')} </p>
            <div className="flex flex-row gap-2">
            <a
                href={`mailto:${contact.email}?subject=Payment%20Issue`}
                className="mt-6 w-full py-2 px-4 bg-primary text-white rounded-lg hover:bg-opacity-90 transition"
              >
                {t('sendEmail')}
              </a>
              <a
                href={`tel:${contact.phone}`}
                className="mt-6 w-full py-2 px-4 bg-primary text-white rounded-lg hover:bg-opacity-90 transition"
              >
                {t('callUs')}
              </a>
              <a
                href={`https://wa.me/${contact.phone}`}
                className="mt-6 w-full py-2 px-4 bg-primary text-white rounded-lg hover:bg-opacity-90 transition"
                target="_blank"
             >
                {t('whatsapp')}
              </a>
            </div>
            </>
          )}
        </div>
      </div>
    </div>
  );
}

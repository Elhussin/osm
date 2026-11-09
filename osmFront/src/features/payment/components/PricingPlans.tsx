"use client";
import { useTranslations } from 'next-intl';
import { Users, Store, Package, Check, Link as LinkIcon } from 'lucide-react';
import {FetchData} from '@/src/shared/api/api';
import { useEffect, useState } from 'react';
import { useUser } from '@/src/features/auth/hooks/UserContext';
import { Link } from '@/src/app/i18n/navigation';
import { PricingPlansProps } from '../types';
export default function PricingPlans({ clientId }: PricingPlansProps) {
  const t = useTranslations('pricingSection');
  const { user } = useUser();
  const [plans, setPlans] = useState<any>(null);
    useEffect(() => {
      (async () => {
        const data = await FetchData({url: `/api/tenants/subscription-plans/` });
       console.log("FetchData",data);
        if(user)
          setPlans(data.results.filter((p:any) => p.name !== "trial")) 
        else
          setPlans(data.results)
        })();

    }, [user]);

  return (
    <section className="py-20 bg-gray-50 dark:bg-gray-900" id="pricing">
          <div className="container mx-auto px-4 text-center">
          <h2 className="text-3xl font-bold mb-12 text-gray-900 dark:text-white">
          {t('title')}
        </h2>

      <div className="grid gap-4 grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 md:grid-cols-3">
      {plans?.length > 0 && plans
        .map((plan:any) => (
          <div
            key={plan.id}
            className="bg-white dark:bg-gray-800 shadow-md rounded-2xl p-6 flex flex-col justify-between border hover:scale-[1.02] transition-transform"
          >
            <div>
              {/* اسم الباقة */}
              <h3 className="text-xl font-semibold mb-2">
                {t(plan.name)}
              </h3>

              {/* السعر الشهري */}
              <p className="text-2xl font-bold text-blue-600 mb-4">
                ${plan.month_price}/
                <span className="text-lg">
                  {plan.field_labels.month_price}
                </span>
              </p>

              {/* السعر السنوي */}
              {plan.year_price !== "0.00" && (
                <p className="text-2xl font-bold text-blue-600 mb-4">
                  ${plan.year_price}/
                  <span className="text-lg">
                    {plan.field_labels.year_price}
                  </span>
                </p>
              )}

              {/* الخصائص */}
              <ul className="space-y-2 text-gray-700 mb-4">
                <li className="flex items-center gap-2">
                  <Users className="w-4 h-4 text-blue-500" />{" "}
                  {plan.field_labels.max_users}: {plan.max_users}
                </li>
                <li className="flex items-center gap-2">
                  <Store className="w-4 h-4 text-purple-500" />{" "}
                  {plan.field_labels.max_branches}: {plan.max_branches}
                </li>
                <li className="flex items-center gap-2">
                  <Package className="w-4 h-4 text-green-500" />{" "}
                  {plan.field_labels.max_products}:{" "}
                  {plan.max_products.toLocaleString()}
                </li>

                {/* لو فيه Features من الباكيند */}
                {plan.features?.map((feature: string, index: number) => (
                  <li key={index} className="flex items-center gap-2">
                    <Check className="w-4 h-4 text-green-500" /> {feature}
                  </li>
                ))}
              </ul>
            </div>

            {/* أزرار الدفع */}

             {!user && <Link
                href={`/auth/register?plan=${plan.name}`}
                className="mt-6 w-full py-2 px-4 bg-primary text-white rounded-lg hover:bg-opacity-90 transition"
              >
                {plan.name === 'enterprise' ? t('contactUs') : t('choosePlan')}
              </Link>}


           {user && 
           <div className="flex justify-center gap-4">
              <Link
                href={`/payment?planId=${plan.id}&direction=${plan.field_labels.month_price}&amount=${plan.month_price}&planName=${plan.name}&clientId=${clientId}&planDirection=month`}
                className="mt-6 w-full py-2 px-4 bg-primary text-white rounded-lg hover:bg-opacity-90 transition"
              >
                {plan.field_labels.month_price}
              </Link>
              <Link
                href={`/payment?planId=${plan.id}&direction=${plan.field_labels.year_price}&amount=${plan.year_price}&planName=${plan.name}&clientId=${clientId}&planDirection=year`}
                className="mt-6 w-full py-2 px-4 bg-primary text-white rounded-lg hover:bg-opacity-90 transition"
              >
                {plan.field_labels.year_price}
              </Link>
            </div>
            }
          </div>
        ))}
    </div>
    </div>
    </section>
  );
}


  
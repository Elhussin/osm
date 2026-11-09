"use client";
import { useTranslations } from 'next-intl';
import { Link } from '@/src/app/i18n/navigation';
import { PLAN_LIMITS } from '@/src/shared/constants/plans';
import { Users, Store, Package, Check } from 'lucide-react';

export default function PricingSection() {
  const t = useTranslations('pricingSection');
  const plans = Object.keys(PLAN_LIMITS) as (keyof typeof PLAN_LIMITS)[];

  return (
    <section className="py-20 bg-gray-50 dark:bg-gray-900" id="pricing">
      <div className="container mx-auto px-4 text-center">
        <h2 className="text-3xl font-bold mb-12 text-gray-900 dark:text-white">
          {t('title')}
        </h2>

        <div className="grid gap-4 grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 md:grid-cols-3">
          {plans.map((plan) => {
            const data = t.raw(`plans.${plan}`) as {
              name: string;
              description: string;
              features: string[];
            };
            const planData = PLAN_LIMITS[plan];

            return (
              <div
                key={plan}
                className="bg-white dark:bg-gray-800 shadow-md rounded-2xl p-6 flex flex-col justify-between border hover:scale-[1.02] transition-transform"
              >
                <div>
                  <h3 className="text-xl font-semibold text-gray-800 dark:text-white">
                    {data.name}
                  </h3>
                  <p className="text-3xl font-bold my-2 text-primary">
                    {planData.price_month === 0 ? t('free') : `$${planData.price_month}/${t('month')}`}
                  </p>
                  <p className="text-3xl font-bold my-2 text-primary">
                    {planData.price_year === 0 ?"" : `$${planData.price_year}/${t('year')}`}
                  </p>
                  <p className="text-gray-600 dark:text-gray-300 mb-4">{data.description}</p>

                  <ul className="text-sm text-start space-y-2 text-gray-700 dark:text-gray-300">
                    <li className="flex items-center gap-2">
                      <Users className="w-4 h-4 text-blue-500" /> {t('maxUsers')}: {planData.max_users}
                    </li>
                    <li className="flex items-center gap-2">
                      <Store className="w-4 h-4 text-purple-500" /> {t('maxBranches')}: {planData.max_branches}
                    </li>
                    <li className="flex items-center gap-2">
                      <Package className="w-4 h-4 text-green-500" /> {t('maxProducts')}: {planData.max_products.toLocaleString()}
                    </li>
                    {data.features.map((feature, index) => (
                    <li key={index} className="flex items-center gap-2">
                      <Check className="w-4 h-4 text-green-500" /> {feature}
                    </li>
                  ))}
               
                  </ul>
       

                </div>
                <Link
                  href={`/auth/register?plan=${plan}`}
                  className="mt-6 w-full py-2 px-4 bg-primary text-white rounded-lg hover:bg-opacity-90 transition"
                >
                  {plan === 'enterprise' ? t('contactUs') : t('choosePlan')}
                </Link>
              </div>
            );
          })}
        </div>
      </div>
    </section>
  );
}


'use client';
import { useMemo } from 'react';
import useSWR from 'swr';
import { useUser } from '@/src/features/auth/hooks/UserContext';
import PricingPlans from '@/src/features/payment/components/PricingPlans';
import { Users, Store, CreditCard, Calendar, AlertTriangle, Check } from 'lucide-react';
import { useTranslations } from 'next-intl';
import Link from 'next/link';
import { FetchData } from '@/src/shared/api/api';

const fetcher = (url: string) => FetchData({ url });

export default function Profile() {
  const { user } = useUser();
  const t = useTranslations("profilePage");

  // جلب بيانات العميل باستخدام SWR فقط إذا كان user.owner
  const shouldFetch =
    user?.role?.name?.toLowerCase() === 'owner' && !!user?.client;
// `/api/tenants/clients/${user.client}`;
  const { data: clientData, error, isLoading } = useSWR(
    shouldFetch ? `/api/tenants/clients/${user.client}` : null,
    fetcher,
    {
      revalidateOnFocus: false, // ما يعيد التحميل إذا ركزت على التبويب
      dedupingInterval: 60000, // كاش دقيقة واحدة
    }
  );

  // حساب الأيام المتبقية والمظهر
  const { daysLeft, statusColor, progressWidth } = useMemo(() => {
    if (!clientData) return { daysLeft: null, statusColor: '', progressWidth: '0%' };

    const today = new Date();
    const paidUntil = new Date(clientData.paid_until);
    const days = Math.ceil(
      (paidUntil.getTime() - today.getTime()) / (1000 * 60 * 60 * 24)
    );

    const color =
      clientData.plans?.name === 'trial'
        ? 'bg-yellow-100 text-yellow-800'
        : days <= 0
        ? 'bg-red-100 text-red-800'
        : 'bg-green-100 text-green-800';

    const width = days > 0 ? `${Math.min((days / 30) * 100, 100)}%` : '0%';

    return { daysLeft: days, statusColor: color, progressWidth: width };
  }, [clientData]);

  // حالة الخطأ
  if (error) {
    return <div className="p-6 text-red-500">❌ {t('failedToLoad')}</div>;
  }

  console.log(clientData, "clientData", user, "user");
  return (
    <>
      {user && (
        <div className="max-w-6xl mx-auto p-6 space-y-6">
          <h2 className="text-xl font-semibold mb-4 flex items-center gap-2">
            {t('welcomeMessage')} : {user.username}
          </h2>

          {/* بيانات المستخدم */}
          <section className="bg-surface p-6 rounded-xl shadow-md border">
            <h2 className="text-xl font-semibold mb-4 flex items-center gap-2">
              <Users className="w-5 h-5 text-blue-500" /> {t('userInformation')}
            </h2>
            <div className="grid sm:grid-cols-2 gap-4 capitalize">
              <p><strong>{t('username')}:</strong> {user?.username}</p>
              <p><strong>{t('email')}:</strong> {user?.email}</p>
              <p><strong>{t('role')}:</strong> {user?.role?.name}</p>
              {user?.role?.name?.toLowerCase() === 'owner' && (
                <>
                  <Link
                    href={`/dashboard/tenant-settings`}
                    className="text-blue-600 hover:underline"
                  >
                    Setting
                  </Link>
                  <p><strong>Client ID:</strong> {user?.client}</p>
                </>
              )}
            </div>
          </section>

          {/* بيانات العميل */}
          {user?.role?.name?.toLowerCase() === 'owner' && (
            <section className="bg-surface p-6 rounded-xl shadow-md border">
              <h2 className="text-xl font-semibold mb-4 flex items-center gap-2">
                <Store className="w-5 h-5 text-purple-500" /> {t('clientInformation')}
              </h2>

              {/* حالة التحميل */}
              {isLoading && (
                <div className="animate-pulse space-y-4">
                  <div className="h-4 bg-gray-200 rounded w-1/3"></div>
                  <div className="h-4 bg-gray-200 rounded w-1/2"></div>
                  <div className="h-4 bg-gray-200 rounded w-1/4"></div>
                </div>
              )}

              {/* البيانات بعد التحميل */}
              {clientData && (
                <>
                  <div className="grid sm:grid-cols-2 gap-4 mb-4">
                    <p><strong>{t('clientName')}:</strong> {clientData?.name}</p>
                    <p className="flex items-center gap-2">
                      <CreditCard className="w-4 h-4" /> <strong>{t('plan')}:</strong>
                      <span className={`px-2 py-0.5 rounded-full text-sm ${statusColor}`}>
                        {clientData?.plans?.name}
                      </span>
                    </p>
                    <p><strong>{t('maxUsers')}:</strong> {clientData?.max_users}</p>
                    <p><strong>{t('maxProducts')}:</strong> {clientData?.max_products}</p>
                    <p><strong>{t('maxBranches')}:</strong> {clientData?.max_branches}</p>
                    <p className="flex items-center gap-2">
                      <Calendar className="w-4 h-4" /> <strong>{t('paidUntil')}:</strong>{' '}
                      {clientData?.paid_until}
                    </p>
                  </div>

                  {/* شريط التقدم */}
                  <div className="mb-4">
                    <div className="w-full h-2 bg-gray-200 rounded-full overflow-hidden">
                      <div
                        className={`h-full ${
                          daysLeft !== null && daysLeft <= 7 ? 'bg-red-500' : 'bg-green-500'
                        }`}
                        style={{ width: progressWidth }}
                      />
                    </div>
                    {daysLeft !== null && (
                      <p className="text-sm mt-1 text-gray-600">
                        {daysLeft > 0
                          ? `${t('subscriptionExpiresIn')}: ${daysLeft}`
                          : t('subscriptionExpired')}
                      </p>
                    )}
                  </div>

                  {/* تنبيهات حالة الاشتراك */}
                  {daysLeft !== null && daysLeft <= 7 && daysLeft > 0 && (
                    <div className="mt-2 p-2 bg-yellow-100 text-yellow-700 rounded flex items-center gap-2">
                      <AlertTriangle className="w-4 h-4" /> {t('subscriptionAboutToExpire')}
                    </div>
                  )}
                  {daysLeft !== null && daysLeft <= 0 && (
                    <div className="mt-2 p-2 bg-red-100 text-red-700 rounded flex items-center gap-2">
                      <AlertTriangle className="w-4 h-4" /> {t('subscriptionExpired')}
                    </div>
                  )}
                  {daysLeft !== null && daysLeft > 7 && (
                    <div className="mt-2 p-2 bg-green-100 text-green-700 rounded flex items-center gap-2">
                      <Check className="w-4 h-4" /> {t('subscriptionActive')}
                    </div>
                  )}
                </>
              )}
            </section>
          )}

          {/* عرض خطط الترقية */}
          {user?.role?.name?.toLowerCase() === 'owner' &&
            clientData &&
            (clientData.plans?.name === 'trial' || (daysLeft !== null && daysLeft <= 0)) && (
              <div id="pricingSectian">
                <PricingPlans clientId={String(clientData.uuid)} />
              </div>
            )}
        </div>
      )}
    </>
  );
}

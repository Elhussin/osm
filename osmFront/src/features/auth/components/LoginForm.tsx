"use client";

import { useUser } from "@/src/features/auth/hooks/UserContext";
import { formRequestProps } from "@/src/shared/types";
import { useApiForm } from "@/src/shared/hooks/useApiForm";
import { useTranslations } from "next-intl";
import { useSearchParams, useRouter } from "next/navigation";
import { safeToast } from "@/src/shared/utils/safeToast";
import { cn } from "@/src/shared/utils/cn";
import { useEffect, useMemo } from "react";
import Image from "next/image";
import { Link } from "@/src/app/i18n/navigation";
import { useLocale } from "next-intl";
export default function LoginForm(props: formRequestProps) {
  const {
    title,
    message,
    submitText = "Login",
    alias,
    mode = "login",
    istenant = false,
  } = props;
  const t = useTranslations("login");
  const { refetchUser, user, loading } = useUser();
  const router = useRouter();
  const searchParams = useSearchParams();
  const locale = useLocale() || "en";

  // 🧩 نستخدم useMemo لتثبيت redirect حتى لا يعاد تغييره كل render
  const redirect = useMemo(() => {
    return searchParams.get("redirect") || `/${locale}/profile`;
  }, [searchParams, locale]);
  const { handleSubmit, submitForm, errors, isBusy, register } = useApiForm({
    alias,
  });

  const onSubmit = async (data: any) => {
    try {
      const result = await submitForm(data);
      if (!result?.success) return;

      if (mode === "login") {
        const res = await refetchUser();
        console.log(res);
        if (res?.success) {
          safeToast(message || t("successMessage"), { type: "success" });
          router.replace(redirect);
        } else {
          safeToast(t("errorMessage"), { type: "error" });
        }
      } else if (mode === "create") {
        safeToast(message || t("successMessage"), { type: "success" });
        router.replace(`/${locale}/auth/login`);
      }
    } catch {
      safeToast(t("errorMessage"), { type: "error" });
    }
  };

  useEffect(() => {
    if (loading) return;
    if (!loading && user) {
      router.replace(redirect);
    }
  }, [loading, user, redirect, router]);

  return (
    <div className={cn("flex justify-center px-4 py-8 bg")}>
      <div
        className={cn(
          "max-w-5xl w-full grid grid-cols-1 bg-surface md:grid-cols-2 gap-8 rounded-2xl shadow-xl overflow-hidden"
        )}
      >
        {/* الفورم */}
        <div className="p-6 md:p-10">
          <h1 className="text-center text-2xl font-semibold mb-6">{title}</h1>

          <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
            {/* اسم المستخدم */}
            <div>
              <label className="label">{t("userNameLabel")}</label>
              <input
                {...register(istenant ? "name" : "username")}
                className="input-text"
                placeholder={t("userNamePlaceholder")}
              />
              {errors[istenant ? "name" : "username"] && (
                <p className="error-text">
                  {errors[istenant ? "name" : "username"]?.message as string}
                </p>
              )}
            </div>

            {/* البريد (فقط عند إنشاء حساب) */}
            {mode === "create" && (
              <div>
                <label className="label">{t("emailLabel")}</label>
                <input
                  {...register("email")}
                  className="input-text"
                  placeholder={t("emailPlaceholder")}
                />
                {errors.email && (
                  <p className="error-text">{errors.email.message as string}</p>
                )}
              </div>
            )}

            {/* كلمة المرور */}
            <div>
              <label className="label">{t("passwordLabel")}</label>
              <input
                {...register("password")}
                type="password"
                className="input-text"
                placeholder={t("passwordPlaceholder")}
              />
              {errors.password && (
                <p className="error-text">
                  {errors.password.message as string}
                </p>
              )}
            </div>
            {/* زر الإرسال */}
            <button
              type="submit"
              disabled={isBusy}
              className="btn btn-primary w-full text-white"
            >
              {isBusy ? submitText + "..." : submitText}
            </button>
            <div className="flex flex-col gap-2">
              {mode === "login" ? (
                <>
                  <Link
                    href="./register"
                    className=" w-full text-primary underline"
                  >
                    {t("register")}
                  </Link>
                  <Link
                    href="./forgot-password"
                    className="w-full text-primary underline"
                  >
                    {t("forgotPassword")}
                  </Link>
                </>
              ) : (
                <Link href="./login" className=" w-full text-primary underline">
                  {t("button")}
                </Link>
              )}
            </div>
          </form>
        </div>

        {/* الجانب الأيمن (صورة + رسالة ترحيب) */}
        <div className={cn("hidden md:flex items-center justify-center p-2")}>
          <div className="relative w-full h-[400px] text-white text-center flex items-center justify-center  bg-primary rounded-2xl ">
            <Image
              src="/media/start.jpg"
              alt="Start APP"
              fill
              className="absolute inset-0 w-full h-full object-cover opacity-70 rounded-2xl"
              priority
              sizes="(max-width: 768px) 100vw, (max-width: 1200px) 50vw, 33vw"
            />

            <div className="absolute bottom-3 z-10 space-y-4">
              <h2 className="text-3xl font-bold">{t("welcomeTitle")}</h2>
              <p className="text-lg">{t("welcomeMessage")}</p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

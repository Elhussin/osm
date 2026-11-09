"use client";

import LoginForm from "@/src/features/auth/components/LoginForm";
import { useTranslations } from "next-intl";
export default function LoginPage() {
  const t = useTranslations("login");
  return (
    <LoginForm
      alias="users_login_create"
      className="container"
      title={t("title")}
      message={t("message")}
      submitText={t("button")}
    />
  );
}

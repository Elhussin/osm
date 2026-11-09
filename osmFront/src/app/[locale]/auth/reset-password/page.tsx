"use client";
import { useSearchParams } from "next/navigation";
import { useApiForm } from "@/src/shared/hooks/useApiForm";
import { safeToast } from "@/src/shared/utils/safeToast";
import { useTranslations } from "next-intl";
import { ActionButton } from "@/src/shared/components/ui/buttons";

export default function ResetPasswordPage() {
  const searchParams = useSearchParams();
  const uid = searchParams.get("uid") || "";
  const token = searchParams.get("token") || "";
  const t = useTranslations("resetPassword");
  const formRequest = useApiForm({
    alias: "users_password_reset_confirm_create",
    defaultValues: { uid, token, password: "" },
    onSuccess: () => {
      safeToast(t("SuccessMessage"), { type: "success" });
    },
  });

  const handleReset = async (values: any) => {
    await formRequest.submitForm(values);
  };

  return (
    <div className="flex items-center justify-center">
      {formRequest.formState.isSubmitSuccessful ? (
        <div className="bg-white shadow-lg rounded-2xl p-6 text-center max-w-md w-full">
          <h2 className="text-xl font-semibold text-green-600 mb-2">
            {t("SuccessMessage")} 🎉
          </h2>
          <p className="text-gray-600">{t("loginMessage")}</p>
        </div>
      ) : (
        <div className="bg-white shadow-lg rounded-2xl p-8 w-full max-w-md">
          <h2 className="text-2xl font-bold text-gray-800 mb-6 text-center">
            {t("title")}
          </h2>
          <form
            onSubmit={formRequest.handleSubmit(handleReset)}
            className="space-y-5"
          >
            <input type="hidden" {...formRequest.register("uid")} />

            <input type="hidden" {...formRequest.register("token")} />

            {/* Password Field */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                {t("passwordLabel")}
              </label>
              <input
                type="password"
                placeholder={t("passwordPlaceholder")}
                className="w-full px-4 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-500"
                {...formRequest.register("password", {
                  required: t("passwordRequired"),
                })}
              />
              {formRequest.formState.errors.password && (
                <p className="text-sm text-red-500 mt-1">
                  {formRequest.formState.errors.password.message as string}
                </p>
              )}
              {formRequest.formState.errors.uid && (
                <p className="text-sm text-red-500 mt-1">
                  {formRequest.formState.errors.uid.message as string}
                </p>
              )}
              {formRequest.formState.errors.token && (
                <p className="text-sm text-red-500 mt-1">
                  {formRequest.formState.errors.token.message as string}
                </p>
              )}
            </div>

            {/* Submit Button */}
            <ActionButton
              label={`${formRequest.isBusy ? t("sending") : t("button")}`}
              type="submit"
              disabled={formRequest.isBusy}
              variant="primary"
              className="w-full"
              // className="w-full bg-indigo-600 text-white py-2 rounded-lg hover:bg-indigo-700 transition disabled:opacity-50"
            ></ActionButton>

            {/* Root Error */}
            {formRequest.errors.root && (
              <p className="text-center text-sm text-red-600 mt-3">
                {formRequest.errors.root}
              </p>
            )}
          </form>
        </div>
      )}
    </div>
  );
}

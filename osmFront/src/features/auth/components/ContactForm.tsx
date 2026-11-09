"use client";

import { useApiForm } from "@/src/shared/hooks/useApiForm";
import { useTranslations } from "next-intl";
import { toast } from "sonner";
export default function ContactForm() {
  const t = useTranslations("contact");

const {handleSubmit, submitForm, errors, isBusy, register} = useApiForm({ alias: "crm_contact_us_create" });

  const onSubmit = async (data: any) => {
    const result = await submitForm(data);
    if (result?.success) {
      toast.success(t("successMessage"));
    } else {
      toast.error(t("errorMessage"));
    }
  };

  return (
    <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
      <div>
        <label className="block mb-1">{t("name")}</label>
        <input
          {...register("name")}
          type="text"
          className="input-text"
          required
        />
        {errors.name && <p className="text-red-500">{errors.name.message}</p>}
      </div>

      <div>
        <label className="block mb-1">{t("email")}</label>
        <input
          {...register("email")}
          type="email"
          className="input-text"
          required
        />
        {errors.email && <p className="text-red-500">{errors.email.message}</p>}
      </div>
      <div>
        <label className="block mb-1">{t("subject")}</label>
        <input
          {...register("subject")}
          type="tel"
          className="input-text"
          required
        />
        {errors.subject && <p className="text-red-500">{errors.subject.message}</p>}
      </div>
      <div>
        <label className="block mb-1">{t("message")}</label>
        <textarea
          {...register("message")}
          rows={4}
          className="input-text"
          required
        />
        {errors.message && <p className="text-red-500">{errors.message.message}</p>}
      </div>

      <button
        type="submit"
        disabled={isBusy}
        className="px-6 py-2 bg-blue-600 text-white rounded hover:bg-blue-700 transition"
      >
        {t("submit")}
      </button>
    </form>
  );
}

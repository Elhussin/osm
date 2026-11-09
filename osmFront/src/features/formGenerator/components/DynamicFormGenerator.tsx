"use client";
import React, { useState, useEffect } from "react";
import { z } from "zod";
import { schemas } from "@/src/shared/api/schemas";
import { Loading3 } from "@/src/shared/components/ui/loding";
import { DynamicFormProps } from "@/src/shared/types/DynamicFormTypes";
import {
  defaultConfig,
  ignoredFields,
} from "@/src/features/formGenerator/constants/generatFormConfig";
import { RenderField } from "./ RenderField";
import { cn } from "@/src/shared/utils/cn";
import { CirclePlus, ArrowLeft } from "lucide-react";
import { formsConfig } from "@/src/features/formGenerator/constants/entityConfig";
import { useMemo } from "react";
import { safeToast } from "@/src/shared/utils/safeToast";
import { useTranslations } from "next-intl";
import { ActionButton } from "@/src/shared/components/ui/buttons";
import { useRouter } from "@/src/app/i18n/navigation";
import DynamicFormDialog from "@/src/shared/components/ui/dialogs/DynamicFormDialog";
import { relationshipConfigs } from "@/src/features/formGenerator/constants/generatFormConfig";
import { useApiForm } from "@/src/shared/hooks/useApiForm";
import { useMergedTranslations } from "@/src/shared/utils/useMergedTranslations";
import { NotFound } from "@/src/shared/components/views/NotFound";

export default function DynamicFormGenerator(props: DynamicFormProps) {
  const router = useRouter();
  const [showModal, setShowModal] = useState(false);
  const [currentFieldName, setCurrentFieldName] = useState("");
  const { entity, id, setData, defaultValues } = props;
  const [loading, setLoading] = useState(false);
  const [fetchForginKey, setFetchForginKey] = useState(false);

  if (!entity) throw new Error("entity is required");
  // const t = useTranslations('formsConfig');
  const t = useMergedTranslations(["viewDetailsCard", entity, "formsConfig"]);
  const form = formsConfig[entity];
  const alias = useMemo(
    () => (id ? form.updateAlias : form.createAlias),
    [id, form]
  );
  const fetchAlias = useMemo(() => form.retrieveAlias, [form]);
  const showResetButton = form.showResetButton ?? true;
  const showBackButton = form.showBackButton ?? true;
  const className = form.className || "";
  const relationConfig = relationshipConfigs[currentFieldName];
  const action = id ? "update" : "create";

  const submitText = useMemo(
    () => `${t(action)} ${t(entity)}`,
    [id, t, entity]
  );

  const successMessage = useMemo(
    () => `${t("success")} ${t(action)} ${t(entity)}`,
    [id, t, entity]
  );

  const errorMessage = useMemo(
    () => `${t("failed")} ${t(action)} ${t(entity)}`,
    [id, t, entity]
  );

  const title = useMemo(() => `${t(action)} ${t(entity)}`, [id, t, entity]);

  const userConfig: Record<string, any> = form.userConfig || {};

  const config = { ...defaultConfig, ...userConfig };
  // Guard against optional schemaName being undefined in some forms
  const schema = form.schemaName
    ? ((schemas as any)[form.schemaName] as z.ZodObject<any> | undefined)
    : undefined;
  const shape = (schema as any)?.shape || {};
  const effectiveIgnoredFields = useMemo(
    () => (id ? [...ignoredFields, "password"] : ignoredFields),
    [id]
  );

  const allFields = useMemo(
    () => Object.keys(shape).filter((f) => !effectiveIgnoredFields.includes(f)),
    [shape, effectiveIgnoredFields]
  );

  const visibleFields = config.fieldOrder || allFields;

  // Ensure alias and fetchAlias are always strings to satisfy type requirements
  const safeAlias: string = alias ?? "";
  const safeFetchAlias: string = fetchAlias ?? "";
  const canSubmit = Boolean(safeAlias);
  console.log("defaultValues", defaultValues);
  const formRequest = useApiForm({
    alias: safeAlias,
    defaultValues: defaultValues || {},
  });
  const fetchDefaultData = useApiForm({
    alias: safeFetchAlias,
    defaultValues: { id: id },
  });

  const onSubmit = async (data: any, e?: React.BaseSyntheticEvent) => {
    e?.preventDefault();
    const result = await formRequest.submitForm(data);
    if (result?.success) {
      safeToast(successMessage || "Submitted successfully", {
        type: "success",
      });
      // formRequest.refetch();
      if (setData) {
        setData(result.data);
        return;
      } else {
        formRequest?.reset(result.data);
        // console.log()
        formRequest.setValue(currentFieldName, result.data.id);
        // setDefaultValues(result.data);
      }
    } else if (errorMessage) {
      safeToast(errorMessage, { type: "error" });
    }
  };

  useEffect(() => {
    if (id) {
      const fetchData = async () => {
        setLoading(true);
        const result = await fetchDefaultData.query.refetch();
        formRequest?.reset(result.data);
        setLoading(false);
      };
      fetchData();
    }
  }, [id]);

  if (loading) {
    return <Loading3 />;
  }
  if (!schema) {
    return <NotFound error={t("thisFormDoesNotExist")} />;
  }
  return (
    <div className={cn(className) + " container"}>
      <div className="head">
        <h2 className="title">{title ? title : form.schemaName}</h2>

        {showBackButton && !setData && (
          <ActionButton
            icon={<ArrowLeft size={16} />}
            variant="success"
            title={t("back")}
            onClick={() => router.back()}
          />
        )}
      </div>

      <form
        onSubmit={formRequest.handleSubmit(onSubmit)}
        className={config.containerClasses}
      >
        {visibleFields.map((fieldName) => (
          <RenderField
            key={fieldName}
            fieldName={fieldName}
            fieldSchema={shape[fieldName]}
            form={formRequest}
            config={config}
            mode={id ? "edit" : "create"}
            setShowModal={(show: boolean) => {
              if (show) setCurrentFieldName(fieldName);
              setShowModal(show);
            }}
            fetchForginKey={fetchForginKey}
            setFetchForginKey={setFetchForginKey}
            t={t}
          />
        ))}

        <div className="flex gap-3 pt-4">
          <ActionButton
            type="submit"
            label={
              formRequest.formState.isSubmitting
                ? `${t("saving")}...`
                : submitText || t("create")
            }
            className={`${config.submitButtonClasses} ${
              formRequest.formState.isSubmitting || !canSubmit
                ? "opacity-50 cursor-not-allowed"
                : ""
            }`}
            disabled={formRequest.formState.isSubmitting || !canSubmit}
            variant="info"
            title={submitText || t("create")}
            icon={<CirclePlus size={16} />}
          />
        </div>
      </form>
      {showModal && (
        <DynamicFormDialog
          entity={relationConfig.entityName || ""}
          onClose={() => {
            setShowModal(false);
            setFetchForginKey(true);
          }}
        />
      )}
    </div>
  );
}

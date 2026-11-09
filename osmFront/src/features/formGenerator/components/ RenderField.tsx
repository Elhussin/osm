"use client";
import { z } from "zod";

import { useEffect } from "react";
import {
  detectFieldType,
} from "../utils/detectFieldType";
import { ForeignKeyField } from "./ForeignKeyField";
import { UnionField } from "./UnionField";
import { useFieldOptions } from "../hooks/useFieldOptions";
import { unwrapSchema } from "../utils/unwrapSchema";
import { getFieldLabel,isFieldRequired } from "../utils";
import { fieldTemplates } from "../constants/generatFormConfig";
import { RHFSelect } from "./RHFSelect";
// ============================
// RenderField Component
// ============================
export const RenderField = ({ fieldName, fieldSchema, form, config, mode, setShowModal,fetchForginKey,setFetchForginKey,t }: any) => {
  const fieldType = detectFieldType(fieldName, fieldSchema);
  const template =
    fieldTemplates[fieldType] || fieldTemplates["text"] || {
      component: "input",
      type: "text",
    };

  const unwrappedSchema = unwrapSchema(fieldSchema);
  // const label = getFieldLabel(fieldName, fieldSchema);
  const label = t(fieldName);
  const required = isFieldRequired(fieldSchema);

  // Handle select / foreignkey options
  const { data: options, loading } = useFieldOptions(
    fieldName,
    fieldType,
    unwrappedSchema as z.ZodEnum<any>
  );


  useEffect(() => {
    if (!loading && options?.length) {
      const currentValue = form.getValues(fieldName);
      const exists = options.some((o: any) => o.value === currentValue);
      if (!exists) {
        // reset للقيمة الافتراضية لو موجودة بالـ defaultValues
        const defaultValue = form.formState.defaultValues?.[fieldName];
        if (defaultValue) {
          form.setValue(fieldName, defaultValue);
        }
      }
    }
  }, [loading, options, fieldName, form]);

  if (loading) {
    return <div className="animate-pulse h-9 w-full bg-gray-100 rounded" />;
  }
  // ============================
  // Renders by fieldType
  // ============================
  // foreignkey
  if (fieldType === "foreignkey") {
    return (
      <ForeignKeyField
        key={fieldName}
        fieldName={fieldName}
        register={form.register}
        config={config}
        label={label}
        required={required}
        errors={form.formState.errors}
        form={form}
        setShowModal={setShowModal}
        fetchForginKey={fetchForginKey}
        setFetchForginKey={setFetchForginKey}
      />
    );
  }

  if (fieldType === "union") {
    return (
      <UnionField
        key={fieldName}
        fieldName={fieldName}
        fieldSchema={fieldSchema}
        register={form.register}
        config={config}
        label={label}
        required={required}
        errors={form.formState.errors}
      />
    );
  }
  // checkbox
  if (template.wrapper === "checkbox") {
    return (
      <div key={fieldName} className={config.spacing}>
        <div className="flex items-center space-x-2">
          <input
            id={fieldName}
            type="checkbox"
            {...form.register(fieldName)}
            className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
          />
          <label htmlFor={fieldName} className={config.labelClasses}>
            {label}
          </label>
        </div>
        {form.formState.errors[fieldName] && (
          <p className={config.errorClasses}>
            {form.formState.errors[fieldName]?.message as string}
          </p>
        )}
      </div>
    );
  }

  // select
  if (fieldType === "select") {

    return (
      <>
        {label && (
          <label htmlFor={fieldName} className="block font-medium text-sm m-1">
            {label}
            {required ? <span className="text-red-500"> *</span> : ''}
          </label>
        )}

        <RHFSelect
          name={fieldName}
          control={form.control}
          parsedOptions={options}
          label={label}
          required={required}
          placeholder="Select a value"
          className="flex-1" // يملأ المساحة المتبقية
        />
      </>
    )
  }
  // textarea
  if (fieldType === "textarea") {
    return (
      <div key={fieldName} className={config.spacing}>
        <label htmlFor={fieldName} className={config.labelClasses}>
          {label}
          {required && <span className="text-red-500">*</span>}
        </label>
        <textarea
          id={fieldName}
          {...form.register(fieldName)}
          className={config.baseClasses}
          rows={template.props?.rows || 2}
          placeholder={`${label}...`}
          autoComplete="off"
        />
        {form.formState.errors[fieldName] && (
          <p className={config.errorClasses}>
            {form.formState.errors[fieldName]?.message as string}
          </p>
        )}
      </div>
    );
  }

  // array
  if (fieldType === "array") {
    return (
      <div key={fieldName} className={config.spacing}>
        <label htmlFor={fieldName} className={config.labelClasses}>
          {label}
          {required && <span className="text-red-500">*</span>}
        </label>
        <input
          id={fieldName}
          type="text"
          {...form.register(fieldName)}
          className={config.baseClasses}
          placeholder="add values separated by commas"
          autoComplete="off"
        />
        <p className="text-xs text-gray-500">
          add values separated by commas
        </p>
        {form.formState.errors[fieldName] && (
          <p className={config.errorClasses}>
            {form.formState.errors[fieldName]?.message as string}
          </p>
        )}
      </div>
    );
  }

  // object
  if (fieldType === "object") {
    return (
      <div key={fieldName} className={config.spacing}>
        <label htmlFor={fieldName} className={config.labelClasses}>
          {label}
          {required && <span className="text-red-500">*</span>}
        </label>
        <input
          id={fieldName}
          type="text"
          {...form.register(fieldName)}
          className={config.baseClasses}
          autoComplete="off"
          placeholder="JSON object"
        />
        {form.formState.errors[fieldName] && (
          <p className={config.errorClasses}>
            {form.formState.errors[fieldName]?.message as string}
          </p>
        )}
      </div>
    );
  }

  // default input
  const inputType = template.type || "text";
  const isDisabled =
    mode === "edit" &&
    (fieldName === "username" || fieldName === "password");

  return (
    <div key={fieldName} className={config.spacing}>
      <label htmlFor={fieldName} className={config.labelClasses}>
        {label}
        {required && <span className="text-red-500">*</span>}
      </label>
      <input
        id={fieldName}
        type={inputType}
        {...form.register(fieldName)}
        className={config.baseClasses}
        placeholder={`${label}...`}
        disabled={isDisabled}
        autoComplete="off"
        {...(template.props || {})}
      />
      {form.formState.errors[fieldName] && (
        <p className={config.errorClasses}>
          {form.formState.errors[fieldName]?.message as string}
        </p>
      )}
    </div>
  );
};

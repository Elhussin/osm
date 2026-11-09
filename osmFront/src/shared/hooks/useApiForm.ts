
/**
 * [useApiForm](cci:1://file:///home/hussin/code/summary/front-end/src/hooks/useApiForm.ts:16:0-138:1) is a custom hook designed to handle form submissions and API interactions.
 * It leverages `react-hook-form` for form management and `react-query` for data fetching and mutations.
 *
 * @param {useFormRequestProps} options - The configuration options for the hook.
 * @param {string} options.alias - The alias for the API endpoint to interact with.
 * @param {object} options.defaultValues - Default values for the form fields.
 * @param {Function} [options.onSuccess] - Callback function to execute on successful form submission.
 * @param {Function} [options.onError] - Callback function to execute on form submission error.
 * @param {Function} [options.transform] - Function to transform form values before submission.
 * @param {boolean} [options.showToast=true] - Flag to show toast notifications on errors.
 *
 * @returns {UseApiFormReturn} An object containing form methods, query, mutation, and utility functions.
 * @returns {object} methods - Methods provided by `react-hook-form` for form handling.
 * @returns {object} query - The `react-query` object for handling GET requests.
 * @returns {object} mutation - The `react-query` object for handling POST/PUT/DELETE requests.
 * @returns {Function} submitForm - Function to submit the form.
 * @returns {Function} resetForm - Function to reset the form to default values.
 * @returns {Function} fetchDirect - Function to directly fetch data without cache.
 * @returns {Function} prefetch - Function to prefetch data for a given set of values.
 * @returns {boolean} isSubmitting - Indicates if the form is being submitted.
 * @returns {object} errors - Form validation errors.
 * @returns {object} formErrors - Comprehensive form errors including root errors.
 */


"use client";
import { useMemo } from "react";
import { ZodType, ZodObject } from "zod";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import api from "../api/axios";
import type { useFormRequestProps, UseApiFormReturn } from "../types";
import { handleServerErrors } from "../utils/handleServerErrors";
import { handleErrorStatus } from "../utils/handleErrorStatus";
import { useTranslations } from 'next-intl';
function hasParameters(
  endpoint: any
): endpoint is { parameters: { body?: ZodType<any>; query?: ZodType<any> } } {
  return "parameters" in endpoint;
}

export function useApiForm(options: useFormRequestProps): UseApiFormReturn {
  const {
    alias,
    defaultValues,
    onSuccess,
    onError,
    transform,
    showToast = true,
    skipCache = false,
    enabled = true, // Default to true to maintain backward compatibility
  } = options;
  const t = useTranslations("errors")

  const queryClient = useQueryClient();

  // Get endpoint
  const endpoint = useMemo(() => {
    const found = api.api.find((e) => e.alias === alias);
    if (!found) return null;
    return found;
  }, [alias]);

  // Extract Schema 
  const schema: ZodType<any> | undefined =
    endpoint && hasParameters(endpoint)
      ? endpoint.parameters?.body ?? endpoint.parameters?.query
      : undefined;

  // Resolver
  const resolver =
    schema instanceof ZodObject
      ? zodResolver(schema)
      : (values: any) => ({ values, errors: {} });

  // useForm
  const methods = useForm<any>({
    resolver,
    defaultValues,
    mode: "onChange",
  });


  // GET 
  const queryKey = useMemo(() => [alias, JSON.stringify(defaultValues || {})], [alias, defaultValues]);
  const query = useQuery({
    queryKey,
    queryFn: () => api.customRequest(alias as string, defaultValues),
    // Only enable if: enabled flag is true AND it's a GET method AND alias exists
    enabled: Boolean(enabled && alias && endpoint?.method === "get"),
    // force refresh عند الحاجة
    staleTime: skipCache ? 0 : 5 * 60 * 1000,
  });

  const prefetch = async (newValues: any) => {
    const prefetchKey = [alias, JSON.stringify(newValues || {})];
    if (!queryClient.getQueryData(prefetchKey)) {
      await queryClient.prefetchQuery({
        queryKey: prefetchKey,
        queryFn: () => api.customRequest(alias as string, newValues),
      });
    }
  };


  const fetchDirect = async () => {
    await queryClient.invalidateQueries({ queryKey });
    return api.customRequest(alias as string, defaultValues);
  };
  // Mutation Form POST / PUT / DELETE
  const mutation = useMutation({
    mutationFn: async (payload: any) => {
      if (!endpoint?.alias) throw new Error(`Endpoint alias is undefined for alias "${alias}"`);
      return api.customRequest(endpoint.alias, payload);
    },
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey });
      onSuccess?.(data);
    },
    onError: (error: any) => {
      handleServerErrors(error, methods.setError, { t, showToast });
      const normalized = handleErrorStatus(error, t);
      onError?.(normalized);
    },
  });

  // Reset Form
  const resetForm = () => {
    methods.reset(defaultValues);
    queryClient.invalidateQueries({ queryKey });
  };

  const submitForm = async (data?: any) => {
    const isValid = await methods.trigger();
    if (!isValid) {
      const fieldErrors = Object.values(methods.formState.errors).map(
        (err: any) => err?.message
      );
      return { success: false, error: fieldErrors.join(", ") || "Validation failed" };
    }

    const values = data ?? methods.getValues();
    let payload = transform ? transform(values) : values;

    try {

      if (!transform && Object.values(values).some(v => v instanceof File)) {
        const fd = new FormData();
        Object.entries(values).forEach(([k, v]) => {
          if (v instanceof File) fd.append(k, v);
          else fd.append(k, JSON.stringify(v));
        });
        payload = fd;
      }

      const response = await mutation.mutateAsync(payload);

      onSuccess?.(response);
      return { success: true, data: response };
    } catch (error: any) {

      handleServerErrors(error, methods.setError, { t });
      const normalized = handleErrorStatus(error, t);
      onError?.(normalized);
      return { success: false, error: normalized };
    }
  };



  const isBusy = query.isLoading || query.isFetching || methods.formState.isSubmitting || mutation.isPending;
  return {
    ...methods,
    query,
    mutation,
    submitForm,
    resetForm,
    fetchDirect,
    prefetch,
    isBusy: isBusy,
    errors: { ...methods.formState.errors, root: methods.formState.errors.root?.message },
  };

}

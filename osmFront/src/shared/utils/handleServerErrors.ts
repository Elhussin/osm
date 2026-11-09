
import { safeToast } from "./safeToast";
import { translate } from "./translate";
import { normalizeErrors } from "./normalizeErrors";
import { handleErrorStatus } from "./handleErrorStatus";

/**
 * Handles server-side errors by mapping them to form fields or displaying toast notifications.
 * 
 * This utility function processes error responses from API calls and integrates with form handling libraries
 * (like react-hook-form) to set field-specific errors. It also handles general errors via toast notifications.
 *
 * @param {any} error - The error object received from the API response (usually an Axios error).
 * @param {(name: string, error: any) => void} setError - The `setError` function from the form library (e.g., react-hook-form) to register errors on specific fields.
 * @param {Object} [options] - Configuration options.
 * @param {boolean} [options.showToast=true] - Whether to show a toast notification for non-field errors or general failures. Default is `true`.
 * @param {(key: string) => string} [options.t] - Optional translation function to localize error messages.
 * 
 * @returns {void}
 * 
 * @example
 * // Usage in a component with react-hook-form
 * const { setError } = useForm();
 * try {
 *   await api.post('/data', payload);
 * } catch (err) {
 *   handleServerErrors(err, setError, { t: t });
 * }
 */

export function handleServerErrors(
  error: any,
  setError: (name: string, error: any) => void,
  options: { showToast?: boolean; t?: (key: string) => string } = { showToast: true }
) {
  const { showToast, t } = options;
  const serverErrors = error?.response?.data;

  // 1. Handle Structured JSON Object Errors (Field-specific validation errors)
  if (serverErrors && typeof serverErrors === "object" && !Array.isArray(serverErrors)) {
    // Flatten nested errors (e.g., { user: { email: "Invalid" } } -> "user.email")
    const normalized = normalizeErrors(serverErrors);

    for (const [field, message] of Object.entries(normalized)) {
      setError(field as any, { type: "server", message: translate(message, t) });
    }

    // Handle non-field specific errors (e.g., "detail" or "non_field_errors")
    const nonFieldError =
      (Array.isArray(serverErrors?.non_field_errors) &&
        serverErrors.non_field_errors.join(" ")) ||
      serverErrors?.detail;

    if (nonFieldError && showToast) {
      safeToast(translate(nonFieldError, t), { type: "error" });
    }

    return;
  }

  // 2. Handle Array Errors (List of error messages)
  if (Array.isArray(serverErrors)) {
    const message = serverErrors.map((e: any) => e.msg || e).join(" ");
    if (showToast) safeToast(translate(message, t), { type: "error" });
    setError("root", { type: "server", message: translate(message, t) });
    return;
  }

  // 3. Fallback: Handle Generic HTTP Status Errors (e.g., 500, 404)
  const normalized = handleErrorStatus(error, t);
  setError("root", { type: "server", message: normalized.message });

  if (showToast) {
    safeToast(normalized.message, { type: "error" });
  }
}

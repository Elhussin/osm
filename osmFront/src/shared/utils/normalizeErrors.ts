/**
 * Normalize backend errors to a flat object with field paths as keys.
 *
 * @param {Object} backendErrors - The error object received from the API response (usually an Axios error).
 * @param {string} [prefix=""] - Optional prefix to prepend to field paths (used for nested objects).
 * @returns {Object} A flat object where keys are field paths and values are error messages.
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
export function normalizeErrors(backendErrors: any, prefix = ""): Record<string, any> {
  const normalized: Record<string, any> = {};

  for (const key in backendErrors) {
    const value = backendErrors[key];
    const fieldPath = prefix ? `${prefix}.${key}` : key;

    if (Array.isArray(value) && typeof value[0] === "object") {
      value.forEach((v, i) => {
        Object.assign(normalized, normalizeErrors(v, `${fieldPath}.${i}`));
      });
    } else if (Array.isArray(value)) {
      normalized[fieldPath] = value.join(" ");
    } else if (typeof value === "object" && value !== null) {
      Object.assign(normalized, normalizeErrors(value, fieldPath));
    } else {
      normalized[fieldPath] = value;
    }
  }

  return normalized;
}


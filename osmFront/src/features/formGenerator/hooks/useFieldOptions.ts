import { z } from "zod";

/**
 * Generates selectable field options based on a ZodEnum schema.
 *
 * @param {string} fieldName - The name of the field (for reference or debugging purposes).
 * @param {string} fieldType - The type of the field (e.g., "select").
 * @param {z.ZodEnum<any>} [schema] - Optional Zod enum schema defining possible option values.
 * @returns {{ data: { label: string; value: string }[]; loading: boolean }}
 * An object containing:
 *  - `data`: an array of options formatted as `{ label, value }`.
 *  - `loading`: a boolean indicating if the data is being loaded (always `false` here).
 *
 * @example
 * const schema = z.enum(["Admin", "User", "Guest"]);
 * const { data } = useFieldOptions("role", "select", schema);
 * // data = [
 * //   { label: "Admin", value: "Admin" },
 * //   { label: "User", value: "User" },
 * //   { label: "Guest", value: "Guest" }
 * // ]
 */
export function useFieldOptions(fieldName: string, fieldType: string, schema?: z.ZodEnum<any>) {
  if (fieldType === "select" && schema) {
    return {
      data: schema.options.map((opt: any) => ({ label: opt, value: opt })),
      loading: false,
    };
  }

  return { data: [], loading: false };
}

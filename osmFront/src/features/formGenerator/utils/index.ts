"use client";
import { z } from 'zod';

/**
 * Generates a user-friendly label for a given field based on its name or schema description.
 *
 * - If the Zod schema includes a `.describe("...")`, that description is used as the label.
 * - Otherwise, the function converts the field name into a readable label:
 *   - Replaces underscores (`_`) with spaces.
 *   - Capitalizes the first letter.
 *
 * Example:
 * ```ts
 * const schema = z.string().describe("Email Address");
 * getFieldLabel("email", schema); // "Email Address"
 *
 * getFieldLabel("user_name"); // "User name"
 * ```
 *
 * @param field - The name of the field (e.g. "email", "user_name").
 * @param schema - Optional Zod schema that may include a description.
 * @returns A formatted, human-readable label for the field.
 */
export function getFieldLabel(field: string, schema?: z.ZodTypeAny): string {
  return schema?.description || field.replace(/_/g, ' ').replace(/^\w/, c => c.toUpperCase());
}

/**
 * Determines whether a Zod schema field is required.
 *
 * The function checks if the field is wrapped in a `ZodOptional` schema.
 * - If it's **not** optional → returns `true` (required).
 * - If it's optional → returns `false`.
 *
 * Example:
 * ```ts
 * isFieldRequired(z.string()); // true
 * isFieldRequired(z.string().optional()); // false
 * ```
 *
 * @param schema - The Zod schema representing the field.
 * @returns `true` if the field is required, otherwise `false`.
 */
export function isFieldRequired(schema: z.ZodTypeAny): boolean {
  return !(schema instanceof z.ZodOptional);
}

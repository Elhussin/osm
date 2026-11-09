
import { z } from "zod";

/**
 * Extracts all possible option values from a Zod union schema.
 *
 * This function iterates through each option defined inside a ZodUnion
 * and returns a list of possible values or types.
 *
 * - For `ZodLiteral` options, it extracts the literal value (e.g. `"active"`, `"pending"`).
 * - For `ZodString` options, it adds the generic type name `'string'`.
 *
 * Example:
 * ```ts
 * const statusSchema = z.union([
 *   z.literal("active"),
 *   z.literal("inactive"),
 *   z.literal("pending")
 * ]);
 * 
 * getUnionOptions(statusSchema);
 * // => ["active", "inactive", "pending"]
 * 
 * const mixedSchema = z.union([
 *   z.string(),
 *   z.literal("unknown")
 * ]);
 * 
 * getUnionOptions(mixedSchema);
 * // => ["string", "unknown"]
 * ```
 *
 * @param schema - The Zod union schema to extract options from.
 * @returns An array of string values representing all union options.
 */
export function getUnionOptions(schema: z.ZodUnion<any>): string[] {
    const options: string[] = [];
    schema._def.options.forEach((option: any) => {
      if (option instanceof z.ZodLiteral) {
        options.push(option.value as string);
      } else if (option instanceof z.ZodString) {
        options.push('string');
      }
    });
    return options;
  }
  
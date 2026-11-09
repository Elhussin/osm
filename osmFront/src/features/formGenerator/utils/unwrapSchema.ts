import { z } from 'zod';
/**
 * Recursively unwraps a Zod schema to get its underlying base type.
 *
 * This function removes all optional, nullable, and default wrappers
 * from a Zod schema until it reaches the core (inner) schema.
 *
 * Example:
 * ```ts
 * const wrapped = z.optional(z.nullable(z.string().default("Hi")));
 * const base = unwrapSchema(wrapped);
 * // base is now a ZodString
 * ```
 *
 * @param schema - The Zod schema to unwrap.
 * @returns The innermost Zod schema without optional, nullable, or default wrappers.
 */
export function unwrapSchema(schema: z.ZodTypeAny): z.ZodTypeAny {
    while (
      schema instanceof z.ZodOptional ||
      schema instanceof z.ZodNullable ||
      schema instanceof z.ZodDefault
    ) {
      schema = schema._def.innerType as z.ZodTypeAny;
    }
    return schema;
  }
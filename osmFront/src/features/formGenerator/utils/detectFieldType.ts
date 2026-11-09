import { z } from 'zod';
import { unwrapSchema } from './unwrapSchema';
import { relationshipConfigs } from '../constants/generatFormConfig';
/**
 * Detects the most suitable UI field type for a given field based on its name and Zod schema definition.
 *
 * The function first unwraps the schema to remove optional, nullable, or default wrappers.
 * It then uses heuristics based on the field name (e.g. "email", "password", "date") 
 * and the underlying Zod type (e.g. ZodString, ZodNumber, ZodBoolean) 
 * to infer an appropriate input type for rendering forms dynamically.
 *
 * Example:
 * ```ts
 * detectFieldType('email', z.string().email()); // "email"
 * detectFieldType('age', z.number()); // "number"
 * detectFieldType('is_active', z.boolean()); // "checkbox"
 * detectFieldType('notes', z.string().max(300)); // "textarea"
 * ```
 *
 * @param field - The name of the field (e.g. "email", "user_id", "description").
 * @param rawSchema - The raw Zod schema associated with the field.
 * @returns A string representing the inferred field type (e.g. "text", "email", "number", "checkbox", "textarea").
 */
export function detectFieldType(field: string, rawSchema: z.ZodTypeAny): string {
    const schema = unwrapSchema(rawSchema);
    if (field.endsWith('_id') && relationshipConfigs[field]) {
      return 'foreignkey';
    }
    const fieldLower = field.toLowerCase();
    if (fieldLower.includes('email')) return 'email';
    if (fieldLower.includes('password')) return 'password';
    if (fieldLower.includes('phone') || fieldLower.includes('tel')) return 'tel';
    if (fieldLower.includes('url') || fieldLower.includes('website')) return 'url';
    if (fieldLower.includes('color')) return 'color';
    if (fieldLower.includes('date')) return 'date';
    if (fieldLower.includes('time')) return 'time';
    if (fieldLower.includes('description') || fieldLower.includes('content') || fieldLower.includes('notes')) return 'textarea';
  
    if (schema instanceof z.ZodBoolean) return 'checkbox';
    if (schema instanceof z.ZodEnum) return 'select';
    if (schema instanceof z.ZodUnion) return 'union';
    if (schema instanceof z.ZodNumber) return 'number';
  
    if (schema instanceof z.ZodString) {
      const checks = schema._def.checks || [];
      const hasEmail = checks.some((c: any) => c.kind === 'email');
      const hasUrl = checks.some((c: any) => c.kind === 'url');
      const hasMinLength = checks.some((c: any) => c.kind === 'min' && c.value >= 6);
      const hasMaxLength = checks.some((c: any) => c.kind === 'max' && c.value > 100);
  
      if (hasEmail) return 'email';
      if (hasUrl) return 'url';
      if (hasMinLength && fieldLower.includes('password')) return 'password';
      if (hasMaxLength) return 'textarea';
    }
  
    if (schema instanceof z.ZodArray) return 'array';
    if (schema instanceof z.ZodObject) return 'object';
  
    return 'text';
  }
  
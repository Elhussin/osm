import { ZodObject, ZodTypeAny, ZodRawShape } from "zod";

type FieldMeta = {
  key: string;
  label: string;
  zodType: ZodTypeAny;
};

export function generateViewFieldsWithLabels(
  schema: ZodObject<ZodRawShape>,
  options?: {
    hiddenFields?: string[];
    fieldLabels?: Record<string, string>;
  }
): FieldMeta[] {
  const shape = schema.shape;

  return Object.entries(shape)
    .filter(([key]) => !options?.hiddenFields?.includes(key))
    .map(([key, zodType]) => {
      // استخدم label مخصص إن وُجد، أو الوصف من Zod، أو الاسم الافتراضي
      const customLabel = options?.fieldLabels?.[key];
      const zodLabel = (zodType as any).description;
      const fallbackLabel = key.replace(/_/g, " ").replace(/\b\w/g, c => c.toUpperCase());

      return {
        key,
        label: customLabel || zodLabel || fallbackLabel,
        zodType: zodType as ZodTypeAny,
      };
    });
}

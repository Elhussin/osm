
import { endpoints } from '@/src/shared/api/schemas';
import { SearchField } from '@/src/shared/types/search';
import { formatLabel} from './cardViewHelper'

// : "text" | "number" | "date" | "select" 
export function detectFieldType(name: string, schemaDef?: any):any{
  if (schemaDef?.typeName === "ZodEnum") {
    return "select";
  }
  
  if (name.toLowerCase().includes("id")) {
    return "number";
  }
  if (schemaDef?.typeName === "ZodDate" || schemaDef?.typeName === "ZodDateTime") {
    return "date";
  }
  return "text";
}

export function generateSearchFieldsFromEndpoint(
  alias: string,
  labels?: Record<string, string>
): SearchField[] {
  const endpoint = endpoints.find((e) => e.alias === alias);
  if (!endpoint || !("parameters" in endpoint) || !Array.isArray(endpoint.parameters)) {
    return [];
  }

  return (
    endpoint.parameters?.map((param: any) => {
      const schemaDef: any = param.schema._def;
      const type = detectFieldType(param.name, schemaDef);

      return {
        name: param.name,
        label: labels?.[param.name] || formatLabel(param.name),
        type,
        options:
          schemaDef?.typeName === "ZodEnum"
            ? schemaDef.values.map((v: string) => ({ label: v, value: v }))
            : undefined,
      };
    }) ?? []
  );
}



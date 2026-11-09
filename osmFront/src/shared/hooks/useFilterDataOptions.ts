import { useEffect, useState } from "react";
import { useApiForm } from "@/src/shared/hooks/useApiForm";
import { detectFieldType } from "@/src/shared/utils/generateSearchFields";

export function useFilterDataOptions(
  alias: string,
  options?: { enabled?: boolean } // تمرير enabled للتحكم
) {
  const [fields, setFields] = useState<any[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [errors, setErrors] = useState<any>(null);

  const fetchData = useApiForm({ alias });
  const enabled = options?.enabled ?? true; // بشكل افتراضي مفعل

  useEffect(() => {
    if (!enabled || !alias) return; // لو غير مفعل أو alias فارغ، ما نعملش fetch

    const fetch = async () => {
      try {
        setIsLoading(true);
        setErrors(null);
        const result = await fetchData.query.refetch();

        if (Array.isArray(result?.data)) {
          const mapped = result.data.map((item: any) => {
            const type = detectFieldType(item.name); // helper لتحديد النوع
            return {
              name: item.name,
              label: item.label,
              type: item.values.length > 0 ? "select" : type,
              options: item.values.map((val: string) => ({
                label: val,
                value: val,
              })),
            };
          });

          setFields(mapped);
        }
      } catch (err) {
        setErrors(err);
      } finally {
        setIsLoading(false);
      }
    };

    fetch();
  }, [alias, enabled]); // اضفنا enabled dependency

  return { fields, isLoading, errors };
}

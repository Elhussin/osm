import { useEffect, useState } from "react";
import { useApiForm } from "../../hooks/useApiForm";
import { formatLabel } from "@/src/shared/utils/cardViewHelper";

export function useSearchFieldsFromOptions(alias: string) {
  const [fields, setFields] = useState<any[]>([]);
  const fetchData = useApiForm({ alias });


  useEffect(() => {
 
    async function fetch() {
      try{
      const res = await fetchData.query.refetch();
      if (res?.data) {
        const mapped = Object.keys(res.data).map((key) => ({
          name: key,
          label: formatLabel(key), // هنا تقدر تحط ترجمة
          type: "select" as const,
          options: res.data[key].map((val: string) => ({
            label: val,
            value: val,
          })),
        }));
        setFields(mapped);
      }
      }
      catch (err) {
        console.error("Error fetching filter options:", err);
      }
    }
    fetch();
  }, [alias]);

  return fields;
}

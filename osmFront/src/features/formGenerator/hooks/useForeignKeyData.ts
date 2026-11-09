import { useEffect, useState } from "react";
import { useApiForm } from "@/src/shared/hooks/useApiForm";
import { formsConfig } from "@/src/features/formGenerator/constants/entityConfig";

export function useForeignKeyData(entityName: string, setData: any) {
    const [loading, setLoading] = useState(false);
    const alias = formsConfig[entityName]?.listAlias;
    const fetchForeignKeyData = useApiForm({ alias: alias });
    useEffect(() => {
      (async () => {
        if (alias) {
          setLoading(true);
          const res = await fetchForeignKeyData.query.refetch();
          if (res?.data?.results) {
            setData(res.data.results.reverse());
            setLoading(false);
          }
        }
      })();
    }, [entityName, alias]);
  }
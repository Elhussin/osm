import { useMemo, useEffect, useState } from "react";
import { useSearchParams, useRouter } from "next/navigation";
import { useApiForm } from "@/src/shared/hooks/useApiForm";
import { IteamInPage } from "@/src/shared/constants";

interface UseFilteredListRequestProps {
  alias: string;
  defaultPage?: number;
  defaultPageSize?: number;
  defaultAll?: boolean;
}

export function useFilteredListRequest(props: UseFilteredListRequestProps) {
  const [data, setData] = useState<any[]>([]);
  const [count, setCount] = useState(0);
  const [totalPages, setTotalPages] = useState(0);
  const { alias, defaultPage = 1, defaultPageSize = IteamInPage, defaultAll = false } = props;

  const searchParams = useSearchParams();
  const router = useRouter();

  // ✅ تحويل searchParams إلى object
  const paramsObj = useMemo(() => {
    const obj: Record<string, any> = {};
    searchParams.forEach((value, key) => {
      obj[key] = value;
    });
    return obj;
  }, [searchParams]);


  const page = parseInt(paramsObj.page || defaultPage, 10);
  const page_size = parseInt(paramsObj.page_size || defaultPageSize, 10);
  const all = paramsObj.all === "true" || defaultAll;

  // ✅ إنشاء hook الطلب وتمرير كل الفلاتر والبحث داخله
  const dataRequest = useApiForm({
    alias,
    defaultValues: {
      page,
      page_size,
      all,
      ...paramsObj, // ← نمرر جميع الفلاتر والبحث أيضًا
    },
  });

  async function fetchData() {
    const res = await dataRequest.query.refetch();
    if (res?.data) {
      setData(res.data.results || res.data || []);
      setCount(res.data.count || 0);
      setTotalPages(Math.ceil((res.data.count || 0) / page_size));
    }
  }

  useEffect(() => {
    (async () => {
      await fetchData();
    })();
  }, [page, page_size, all, JSON.stringify(paramsObj),alias]);

  const setFilters = (filters: Record<string, string>) => {
    const params = new URLSearchParams({ ...paramsObj, ...filters, page: "1" });
    router.push(`?${params.toString()}`);
  };

  const setPage = (newPage: number) => {
    const params = new URLSearchParams({ ...paramsObj, page: String(newPage) });
    router.push(`?${params.toString()}`);
  };


  const setPageSize = (newSize: number) => {
    const params = new URLSearchParams({ ...paramsObj, page_size: String(newSize), page: "1" });
    router.push(`?${params.toString()}`);
  };

  return {
    data,
    count,
    totalPages,
    page,
    page_size,
    all,
    isLoading: dataRequest.isBusy,
    // isError: dataRequest.isError,
    error: dataRequest.errors,
    refetch:fetchData,
    setFilters,
    setPage,
    setPageSize,
  };
}

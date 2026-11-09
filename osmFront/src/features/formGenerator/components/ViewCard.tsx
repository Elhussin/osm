

"use client";
import { useFilteredListRequest } from "@/src/shared/hooks/useFilteredListRequest";
import { SearchFilterForm } from "../../../shared/components/search/SearchFilterForm";
import { formsConfig } from "@/src/features/formGenerator/constants/entityConfig";
import { ActionButton } from "@/src/shared/components/ui/buttons";
import { ArrowLeft, Eye, Pencil, Plus } from "lucide-react";
import { NotFound } from '../../../shared/components/views/NotFound';
import { Loading4 } from "../../../shared/components/ui/loding";
import { useTranslations } from 'next-intl';
import { useMergedTranslations } from '@/src/shared/utils/useMergedTranslations';
import { formatRelatedValue } from "@/src/shared/utils/formatRelatedValue";
import { useFilterDataOptions } from "@/src/shared/hooks/useFilterDataOptions";
import { Pagination } from "../../../shared/components/views/Pagination";
import { useSearchButton } from "@/src/shared/contexts/SearchButtonContext";
import { useEffect } from "react";
export default function ViewCard({ entity }: { entity: string }) {
  const { filterAlias, listAlias, fields,isViweOnly } = formsConfig[entity];
  const t = useMergedTranslations(['viewCard', entity]);
  const { data, count, page, setPage, setFilters, isLoading, page_size, setPageSize } = useFilteredListRequest({ alias: listAlias || "" });
  // show search button
  const { show } = useSearchButton();

  useEffect(() => {
    show();
  }, []);
  const { fields: filterFields, isLoading: isFieldsLoading } = useFilterDataOptions(filterAlias || "", {
    enabled: !!filterAlias,
  });
  console.log(filterFields);

  const totalPages = Math.ceil(count / 10);
  if (isLoading || isFieldsLoading) return <Loading4 />
  if (isLoading || !data || isFieldsLoading) return <Loading4 />;
  return (
    <>
      <SearchFilterForm fields={filterFields} setFilters={setFilters} />
      <div className="head">
        <h2 className="title-1">{t("title")}</h2>
        <div className="flex justify-end gap-1">
        {!isViweOnly && (
          <ActionButton variant="success" icon={<Plus size={16} />} navigateTo={`/dashboard/${entity}/create`} title={`${t('createTitle')} ${entity}`} />
        )}
          <ActionButton variant="success" icon={<ArrowLeft size={16} />} navigateTo={`/dashboard/`} title={t('back')} />
        </div>
      </div>
      <div className="card-continear">
        {data?.map((item: any) => (
          <div key={item.id} className="card">
            {fields?.map((field) => {
              const value = item[field];
              return (
                <p key={field} className="card-body flex">
                  <strong className="mr-2 w-1/3 ">{t(field)} :</strong>
                  <span className="ml-2 w-2/3">{formatRelatedValue(value, field, t)}</span>
                </p>
              );
            })}
            <div className="btn-card">
              <ActionButton variant="info" navigateTo={`/dashboard/${entity}/${item.id}`} icon={<Eye size={16} />} title={`${t('view')} ${entity}`} />
              {!isViweOnly && (
                <ActionButton variant="warning" navigateTo={`/dashboard/${entity}/${item.id}/edit`} icon={<Pencil size={16} />} title={`${t('edit')} ${entity}`} />
              )}
            </div>
          </div>
        ))}

      </div>
      <Pagination
        page={page}
        totalPages={totalPages}
        pageSize={page_size}
        onPageChange={setPage}
        onPageSizeChange={setPageSize}
      />
    </>
  );
}
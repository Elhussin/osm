
import EyeRowView from "./ViewEyeRow";

import { EyeTestLabel } from "./eyeTestLabel";
import { ActionButton } from "@/src/shared/components/ui/buttons";
import { Loading4 } from "@/src/shared/components/ui/loding";
import { Pagination } from "@/src/shared/components/views/Pagination";
import { SearchFilterForm } from "@/src/shared/components/search/SearchFilterForm";
import { useFilteredListRequest } from "@/src/shared/hooks/useFilteredListRequest";
import { useFilterDataOptions } from "@/src/shared/hooks/useFilterDataOptions";
import { formsConfig } from "@/src/features/formGenerator/constants/entityConfig";
import { useSearchButton } from "@/src/shared/contexts/SearchButtonContext";


const ViewEyeTest: React.FC<{ id?: string | number, title?: string }> = ({ id, title }) => {
    const {filterAlias,listAlias} = formsConfig["prescriptions"];
    const { data, totalPages, page, setPage, setPageSize,page_size, setFilters, isLoading }  = useFilteredListRequest({alias:listAlias||""});
    const { show } = useSearchButton();
    show();
    const { fields, isLoading: isFieldsLoading } = useFilterDataOptions(filterAlias || "", {
      enabled: !!filterAlias,
    });
    if (isLoading || !data || isFieldsLoading) return <Loading4 />;
    return (
        <div>
            <SearchFilterForm fields={fields} setFilters={setFilters} />
            <h2 className="text-lg font-semibold mt-2 border-b border-gray-200 pb-2">{title}</h2>
            <div className="grid grid-cols-1  gap-2">
                {data && data.length > 0 && (
                    data.map((item: any, index: number) => (
                        <div key={index} className="grid grid-cols-1  gap-2 border-b border-gray-200 pb-2" >
                            {/* Right/Left Sph-Cyl-Axis-Add */}
                            <div className="grid grid-cols-1 gap-2">
                                <EyeTestLabel />
                                <EyeRowView side="right" data={item} />
                                <EyeRowView side="left" data={item} />
                            </div>
                            {/* PD / SG /VD / VA  */}
                            <div className="grid grid-cols-1  md:grid-cols-3 gap-2 mt-4 md:mt-0  items-center align-center">
                                <p>Customer: {item.customer_name}</p>
                                <p>Created by: {item.created_by_username}</p>
                                <p>Created at: {new Date(item.created_at).toLocaleString()}</p>
                            </div>
                            <div className="flex gap-2">
                                <ActionButton
                                    label="Edit"
                                    variant="info"
                                    title="Edit"
                                    navigateTo={`/prescription/${item.id}/edit`}
                                />
                                <ActionButton
                                    label="Delete"
                                    variant="danger"
                                    title="Delete"
                                    navigateTo={`/prescription/${item.id}/view`}
                                />
                            </div>
                        </div>



                    ))
                )}
            </div>
            <Pagination
                page={page}
                totalPages={totalPages}
                pageSize={page_size}
                onPageChange={setPage}
                onPageSizeChange={setPageSize}
            />
        </div>
    );
};

export default ViewEyeTest;

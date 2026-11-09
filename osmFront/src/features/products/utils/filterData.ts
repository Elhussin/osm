import { parsedOptions } from "@/src/features/products/utils/parsedOptions"
import { selectRelatedData } from "@/src/features/products/utils/selectRelatedData"

export const filterData = (
    data: any,
    item: any,
    selectedType: any,
    subField?: string,
    subFilter?: string
  ) => {
    const filterField = item.filter;
    const selectedData = selectRelatedData(data, filterField);
    let filteredData = selectedData;
    if (subField && subFilter && filterField === subField) {
      filteredData = selectedData?.filter(
        (v: any) => v[subFilter] === selectedType || v[subFilter] === "All"
      );
    }

    return parsedOptions(filteredData, item);
  };
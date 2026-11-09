
  
const mapOptions = (data: any[], fieldName: string) =>
  data.map((v) => ({
    label: v[fieldName] ?? "",
    value: v.id,
  }));

const filterOptions = (data: any[], fieldName: string, filter: string) =>
  data
    .filter((v) => String(v[fieldName]) === String(filter))
    .map((v) => ({
      label: v.label ?? v.value ?? v[fieldName] ?? "",
      value: v.id,
    }));

export const parsedOptions = (data: any, item: any) => {

      if (!Array.isArray(data)) return [];
    
      // flatten لو فيها nested arrays
      const flatData = data.flat?.() || data;
    
      // ✅ إزالة التكرارات حسب id
      const uniqueData = Array.from(
        new Map(flatData.map((obj) => [obj.id, obj])).values()
      );
    
      let options = [];
    
      if (item.mapOnly) {
        options = mapOptions(uniqueData, item.fieldName);
      } else {
        options = filterOptions(uniqueData, item.fieldName, item.filter);
      }
      return options;
    };
    
  
  
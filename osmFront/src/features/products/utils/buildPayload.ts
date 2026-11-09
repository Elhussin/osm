// buildPayload.ts
type BuildPayloadOptions= {
  role?: string;
  prefix?: string;
  include?: string[];
  multiple?: boolean;
};

interface BuildPayloadProps {
  config: any;
  formData: any;
  options?: BuildPayloadOptions;
}

export function buildPayload({config, formData, options = {}}: BuildPayloadProps) {
  const {
    role,
    prefix = "",
    include = [],
    multiple = false,
  } = options;

  const buildSingle = (data: any) =>
    config
      .filter((field: any) => field.role === "all" || !role || field.role === role)
      .reduce((acc: any, field: any) => {
        const name = field.name;
        acc[name] = data?.[name] ?? "";
        return acc;
      }, {});

  const addInclude = (payload: any, data: any) => {
    include.forEach((name: any) => {
      payload[name] = data?.[name] ?? "";
    });
    return payload;
  };

  // Support: formData could be an array, or an object that contains prefix array, or object for single entity
  if (multiple) {
    let dataArray: any[] = [];
    if (Array.isArray(formData)) dataArray = formData;
    else if (prefix && formData && Array.isArray(formData[prefix])) dataArray = formData[prefix];
    else if (Array.isArray(formData?.variants)) dataArray = formData.variants;
    return dataArray.map((item: any) => addInclude(buildSingle(item), item));
  }

  const targetData = prefix ? (formData?.[prefix] || {}) : formData || {};
  return addInclude(buildSingle(targetData), targetData);
}

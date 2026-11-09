export function selectRelatedData(data: any, filter?: string) {
  let relatedData = [];

  switch (filter) {
    case "categories":
      relatedData = data.categories || [];
      break;
    case "suppliers":
      relatedData = data.suppliers || [];
      break;
    case "manufacturers":
      relatedData = data.manufacturers || [];
      break;
    case "brands":
      relatedData = data.brands || [];
      break;
    default:
      relatedData = data["attribute-values"] || [];
      break;
  }
  return relatedData;
}

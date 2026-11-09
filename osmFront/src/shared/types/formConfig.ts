export interface FormConfig {
    schemaName?: string;
    createAlias?: string;
    retrieveAlias?: string;
    updateAlias?: string;
    hardDeleteAlias?: string;
    listAlias?: string;
    createSuccessMessage?: string;
    createErrorMessage?: string;
    updateSuccessMessage?: string;
    updateErrorMessage?: string;
    filterAlias?: string;
    title?: string;
    detailsTitle?: string;
    createTitle?: string;
    updateTitle?: string;
    fields: string[];
    detailsField: string[];
  
    userConfig?:object,
    showResetButton?:boolean,
    showBackButton?:boolean,
    className?:string
    isViweOnly?:boolean
  }
  
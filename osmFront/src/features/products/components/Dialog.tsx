"use client";
import DynamicFormDialog from "@/src/shared/components/ui/dialogs/DynamicFormDialog";
import { useProductFormStore } from "@/src/features/products/store/useProductFormStore";

interface Props {
  setValue: (fieldName: string, value: string,) => void;
  defaultValues?: any;
}

export const Dialog = ({ setValue,defaultValues }: Props) => {
  const { isShowModal, entityName, setShowModal, currentFieldName, setData,  } = useProductFormStore();

  return (
    <>
      {isShowModal && (

      <DynamicFormDialog
        entity={entityName}
        // defaultValues={{currentFieldName:defaultValues}}
        onClose={(newItem) => {
            if (newItem) {
              setData(entityName, newItem);
              setValue(currentFieldName, String(newItem.id));
              setShowModal(false);
            }
          }}
        title={`Add ${entityName.charAt(0).toUpperCase() + entityName.slice(1)}`}
      />

      )}
    </>
  )
}


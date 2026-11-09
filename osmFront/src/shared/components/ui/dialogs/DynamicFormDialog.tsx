"use client";

import React from "react";
import Draggable from "react-draggable";
import { useRef } from "react";
import { DynamicFormDialogProps } from "@/src/shared/types";
import { useTranslations } from "next-intl";
import dynamic from 'next/dynamic';
const DynamicFormGenerator = dynamic(
  () => import('@/src/features/formGenerator/components/DynamicFormGenerator'),
  { ssr: false }
);

const DynamicFormDialog: React.FC<DynamicFormDialogProps> = ({ onClose, entity, title ,defaultValues}) => {

  const nodeRef = useRef(null);
  const t = useTranslations(entity);
  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-surface/50 p-4">
      <Draggable handle=".modal-header" nodeRef={nodeRef}>
        <div
          ref={nodeRef}
          className="w-full max-w-2xl h-[80vh] bg-surface rounded-2xl shadow-lg flex flex-col"
        >
          {/* الهيدر draggable */}
          <div className="modal-header flex justify-between items-center p-4 border-b cursor-move bg-surface">
            <span className="font-semibold"> {t("title")||title}</span>
            <button onClick={onClose}>X</button>
          </div>

          {/* المحتوى */}
          <div className="flex-1 overflow-y-auto p-6">
            <DynamicFormGenerator
              entity={entity}
              setData={(data:any) => onClose(data)}
              defaultValues={defaultValues!}
            />
          </div>
        </div>
      </Draggable>
    </div>
  );
}



export default DynamicFormDialog;
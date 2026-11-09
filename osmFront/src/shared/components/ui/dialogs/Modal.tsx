"use client";

import React from "react";
import {ActionButton} from "@/src/shared/components/ui/buttons";
import {X} from "lucide-react";
export default function Modal({ url, onClose }: { url: string; onClose: (e: any) => void }) {
  
  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4">
      <div className="relative w-full max-w-2xl h-[80vh] bg-white rounded-2xl shadow-lg overflow-hidden">
        <ActionButton
          onClick={onClose}
          icon={<X size={16} />}
          variant="close"
          title="Close"
          label=""
        />
        <iframe
          src={url}
          className="w-full h-full border-none rounded-b-2xl"
        />
      </div>
    </div>
  );
}

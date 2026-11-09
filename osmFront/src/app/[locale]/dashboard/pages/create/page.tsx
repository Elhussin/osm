'use client';

import MultilingualPageEditor from '@/src/features/pages/components/MultilingualPageEditor';
import {useSearchParams } from "next/navigation";
export default function EditPagePage() {
  const searchParams = useSearchParams();
    const defaultData = searchParams.get("default");
    if(!defaultData){
        return <MultilingualPageEditor />;
    }
    return <MultilingualPageEditor defaultPage={defaultData} />;
  }


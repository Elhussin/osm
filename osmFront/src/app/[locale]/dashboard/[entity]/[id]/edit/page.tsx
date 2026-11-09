// app/[entity]/[id]/edit/page.tsx
'use client';
import { formsConfig } from '@/src/features/formGenerator/constants/entityConfig';
import { useParams } from 'next/navigation';
import {NotFound} from '@/src/shared/components/views/NotFound'
import dynamic from 'next/dynamic';
const DynamicFormGenerator = dynamic(
  () => import('@/src/features/formGenerator/components/DynamicFormGenerator'),
  { ssr: false }
);
export default function EntityEditPage() {
    const params = useParams();
   const entity = params.entity as string || '';
  const id = params.id as string || '';

  if (!(entity in formsConfig)) {
    return <NotFound error="Invalid entity" />;
  }

  return <DynamicFormGenerator entity={entity} id={id} />;
}

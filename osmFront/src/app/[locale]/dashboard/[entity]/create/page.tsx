'use client';
import { useParams } from 'next/navigation';
import { formsConfig } from '@/src/features/formGenerator/constants/entityConfig';
import {NotFound} from '@/src/shared/components/views/NotFound'
import dynamic from 'next/dynamic';
const DynamicFormGenerator = dynamic(
  () => import('@/src/features/formGenerator/components/DynamicFormGenerator'),
  { ssr: false }
);
export default function EntityCreatePage() {
  const params = useParams();
  const entity = params.entity as string || '';


  if (!(entity in formsConfig)) {
    return <NotFound error="Invalid entity" />;
  }

  return <DynamicFormGenerator entity={entity} />;
}

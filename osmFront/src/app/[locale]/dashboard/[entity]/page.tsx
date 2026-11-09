// app/[entity]/page.tsx
'use client';
import { useParams } from 'next/navigation';
import { formsConfig } from '@/src/features/formGenerator/constants/entityConfig';

import ViewCard from '@/src/features/formGenerator/components/ViewCard';
import {NotFound} from '@/src/shared/components/views/NotFound';

export default function EntityPage() {
  const params = useParams();
  const entity = params.entity as string || '';
  if (!(entity in formsConfig)) {
    return <NotFound error="Invalid entity" />;
  }

  return <ViewCard entity={entity} />;
}

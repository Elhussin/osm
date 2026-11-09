

"use client";
import React, { Suspense } from 'react';
import {LoadingSpinner} from '@/src/shared/components/ui/loding';
const EyeTest = React.lazy(() => import('@/src/features/prescription/components/EyeTest'));

export default function CreatePrescriptionPage() {

  return (
        <Suspense fallback={<div><LoadingSpinner /></div>}>

       <EyeTest
            alias="prescriptions_prescription_create"
            // className="container"
            title="create Prescription"
            message="Sucussfully created Prescription"
            submitText="Save Prescription"
          />
          </Suspense>


  );
}




"use client";
import { useParams } from "next/navigation";
import EyeTest from '@/src/features/prescription/components/EyeTest';
export default function EditPrescription() {
  const params = useParams();
  const pageId = params?.id as string;
  return (
          <EyeTest
            alias="prescriptions_prescription_update"
            className="container"
            title="Edit Prescription"
            message="Sucussfully edited Prescription"
            submitText="Edit Prescription"
            id={pageId}
          />
  );
}

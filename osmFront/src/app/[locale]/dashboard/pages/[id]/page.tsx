'use client';
import { PageDetail } from "@/src/features/pages/components/PageDetail"
import { useParams } from "next/navigation";
export default function EditPagePage() {

  const params = useParams();
  const pageId = params?.id as string;
  return <PageDetail pageId={pageId} />;

}

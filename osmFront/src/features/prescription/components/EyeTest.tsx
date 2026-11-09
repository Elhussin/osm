"use client";
import React, { useEffect, useState } from "react";
import { useApiForm } from "@/src/shared/hooks/useApiForm";
import { PrescriptionFormProps } from "../types";
import { safeToast } from "@/src/shared/utils/safeToast";
import DynamicFormDialog from "@/src/shared/components/ui/dialogs/DynamicFormDialog";
import { ActionButton } from "@/src/shared/components/ui/buttons";
import { CirclePlus } from "lucide-react";
import EyeRow from "./EyeRow";
import EyeExtraRow from "./EyeExtraRow";
import { EyeTestLabel, EyeTestLabelProps } from "./eyeTestLabel";
import {
  validateEyeTest,
  validateContactLens,
} from "../utils/handleEyeTestFormat";
import { OtherEyeTestFailed } from "./OtherEyeTestFailed";
import ContactLensViewer from "./ContactLensViewer";

export default function EyeTest(props: PrescriptionFormProps) {
  const [customers, setCustomers] = useState<any[]>([]);
  const [showModal, setShowModal] = useState(false);
  const { alias, title, message, submitText, id, isView = false } = props;
  const [fieldErrors, setFieldErrors] = useState<Record<string, boolean>>({});
  const [contactLensData, setContactLensData] = useState<any>({});

  // API hooks
  const customersApi = useApiForm({ alias: "crm_customers_list" });
  const prescriptionApi = useApiForm({
    alias: "prescriptions_prescription_retrieve",
    defaultValues: { id: Number(id) },
  });

  const updatePrescriptionApi = useApiForm({
    alias: "prescriptions_prescription_update",
  });
  const {
    register,
    handleSubmit,
    setValue,
    getValues,
    submitForm,
    errors,
    isBusy,
    reset,
  } = useApiForm({ alias: alias });

  useEffect(() => {
    if (!id) return;
    async function fetchData() {
      const prescriptionData = await prescriptionApi.query.refetch();
      if (prescriptionData?.data) {
        reset(prescriptionData.data);
      }
      const customer: any = prescriptionData?.data?.customer;

      if (customer) {
        setValue(
          "customer",
          String(typeof customer === "object" ? customer.id : customer)
        );
      }
    }
    fetchData();
  }, [id]);

  // Fetch customers
  useEffect(() => {
    customersApi.query.refetch().then((res: any) => {
      if (res?.data?.results) {
        setCustomers(res.data.results.reverse());
        if (!id && res.data.results.length > 0) {
          setValue("customer", String(res.data.results[0].id));
        }
      }
    });
  }, [showModal]);

  // Submit Handler
  const onSubmit = async (data: any) => {
    validateEyeTest(data);
    const eyeTest = validateEyeTest(data);
    if (!eyeTest) {
      return;
    }

    const contactLens = validateContactLens(data);
    setContactLensData(contactLens);
    try {
      let result;
      if (id) {
        result = await updatePrescriptionApi.mutation.mutateAsync(data);
      } else {
        result = await submitForm(data);
      }

      if (result?.success) {
        reset();

        safeToast(message || "Saved successfully", { type: "success" });
        reset(result.data);
      }
    } catch (err: any) {
      safeToast(err.message || "Server error", { type: "error" });
    }
  };

  return (
    <>
      <form onSubmit={handleSubmit(onSubmit)} className="space-y-6" dir="ltr">
        {/* Eyes Block */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-2">
          <div className="grid grid-cols-1 gap-2">
            <EyeTestLabel />
            <EyeRow
              side="right"
              {...{
                register,
                isView,
                setValue,
                getValues,
                fieldErrors,
                setFieldErrors,
              }}
            />
            <EyeRow
              side="left"
              {...{
                register,
                isView,
                setValue,
                getValues,
                fieldErrors,
                setFieldErrors,
              }}
            />
          </div>
          <div className="grid grid-cols-1 gap-2 mt-4 md:mt-0">
            <EyeTestLabelProps />
            <EyeExtraRow
              side="right"
              {...{
                register,
                isView,
                setValue,
                getValues,
                fieldErrors,
                setFieldErrors,
              }}
            />
            <EyeExtraRow
              side="left"
              {...{
                register,
                isView,
                setValue,
                getValues,
                fieldErrors,
                setFieldErrors,
              }}
            />
          </div>
        </div>

        <OtherEyeTestFailed
          {...{ register, customers, setShowModal, errors, isView }}
        />

        <div className="flex gap-3 pt-4">
          <ActionButton
            onClick={handleSubmit(onSubmit)}
            label={isBusy ? title + "..." : title}
            disabled={isBusy}
            variant="info"
            title={submitText || "Save"}
            icon={<CirclePlus size={16} />}
          />
        </div>
      </form>

      {contactLensData && Object.keys(contactLensData).length > 0 && (
        <ContactLensViewer
          rightSphere={contactLensData.rightSphere}
          leftSphere={contactLensData.leftSphere}
          rightToric={contactLensData.rightToric}
          leftToric={contactLensData.leftToric}
        />
      )}
      {showModal && (
        <DynamicFormDialog
          entity="customer"
          onClose={(newCustomer: any) => {
            setShowModal(false);
            if (newCustomer) {
              setCustomers((prev) => [newCustomer, ...prev]);
              setValue("customer", String(newCustomer.id));
            }
          }}
          title="Add Customer"
        />
      )}
    </>
  );
}

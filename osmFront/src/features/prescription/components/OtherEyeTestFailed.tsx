import { OtherFailedProps } from "../types";

import { ActionButton } from "@/src/shared/components/ui/buttons";
import { CirclePlus } from "lucide-react";
export const OtherEyeTestFailed = (props: OtherFailedProps) => {

  const { register, customers, setShowModal, errors, isView } = props;

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 gap-2">
      {/* Notes */}
      <div className="grid grid-cols-[80px_repeat(4,1fr)] gap-2 mt-4 items-start">
        <div className="flex items-center">
          <label className="">Notes</label>
        </div>
        <div className="col-span-4 md:col-span-4">
          <textarea

            {...register("notes")}
            className="input-text p-0 "
            rows={1}
            placeholder="Notes..."
            title="Notes"
            disabled={isView}
          />
        </div>
      </div>

      {/* Customer */}
      <div className="grid grid-cols-[80px_repeat(4,1fr)] gap-2 mt-4 items-start">
        <div className=" items-center col-span-1">
          <label>
            Customer<span className="text-red-500">*</span>
          </label>
        </div>
        <div className="col-span-4 md:col-span-3 flex">

          <select
            // {...register("customer")}
            {...register("customer", { required: "Customer is required" })}
            title="Customer (Required)"
            disabled={isView}
            className="select"
          >
            <option className="" value="">Select Customer</option>
            {customers?.map((customer) => (
              <option key={customer.id} value={String(customer.id)} className="option">
                {customer.first_name} {customer.last_name}
              </option>
            ))}
          </select>

          {!isView && <ActionButton
            onClick={() => setShowModal(true)}
            variant="outline"
            icon={<CirclePlus size={18} color="green" />}
            title="Add"
          />
          }
        </div>

      </div>
      {errors?.customer && <p className="text-red-500 mt-1">{errors.customer.message}</p>}
    </div>
  )
}


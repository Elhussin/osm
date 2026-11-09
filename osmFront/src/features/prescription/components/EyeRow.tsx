import { EyeRowProps,errorInputClass,normalInputClass } from "../types";
import { handleEyeTestFormat } from "../utils/handleEyeTestFormat";
const EyeRow: React.FC<EyeRowProps> = (props) => {
  const { side, register, isView, fieldErrors,setFieldErrors,setValue,getValues } = props;
  const prefix = side === "right" ? "R" : "L";
  return (
    <div className="grid grid-cols-[80px_repeat(4,1fr)] gap-2">
      <div className="flex items-center">
        <h3 className="text-lg font-semibold">{prefix}</h3>
      </div>

      {/* SPH */}
      <div>
        <input
          type="text"
          {...register(`${side}_sphere`)}
          onBlur={(e) => handleEyeTestFormat({field: `${side}_sphere`, value: e.target.value,setFieldErrors,setValue,getValues})}
          className={`input-text ${fieldErrors[`${side}_sphere`] ? errorInputClass : normalInputClass}`}
          placeholder="-00.00"
          min="-60"
          max="60"
          step="0.25"
          disabled={isView}
          title="Sphere (SPH)"
        />
      </div>

      {/* CYL */}
      <div>
        <input
          type="text"
          {...register(`${side}_cylinder`)}
          onBlur={(e) => handleEyeTestFormat({field: `${side}_cylinder`, value: e.target.value,setFieldErrors,setValue,getValues})}
          className={`input-text ${fieldErrors[`${side}_cylinder`] ? errorInputClass : normalInputClass}`}
          placeholder="-00.00"
          min="-15"
          max="15"
          step="0.25"
          disabled={isView}
          title="Cylinder (CYL)"
        />
      </div>

      {/* AXIS */}
      <div>
        <input
          type="number"
          {...register(`${side}_axis`)}
          onBlur={(e) => handleEyeTestFormat({field: `${side}_axis`, value: e.target.value,setFieldErrors,setValue,getValues})}
          className={`input-text ${fieldErrors[`${side}_axis`] ? errorInputClass : normalInputClass}`}
          placeholder="000"
          min="1"
          max="180"
          step="1"
          disabled={isView}
          title="Axis (AXIS)"
        />
      </div>

      {/* ADD */}
      <div>
        <input
          type="text"
          {...register(`${side}_reading_add`)}
          onBlur={(e) => handleEyeTestFormat({field: `${side}_reading_add`, value: e.target.value,setFieldErrors,setValue,getValues})}
          className={`input-text ${fieldErrors[`${side}_reading_add`] ? errorInputClass : normalInputClass}`}
          placeholder="+00.00"
          min="0.25"
          max="4"
          step="0.25"
          disabled={isView}
          title="Reading Add (ADD)"
        />
      </div>
    </div>
  );
};

export default EyeRow;
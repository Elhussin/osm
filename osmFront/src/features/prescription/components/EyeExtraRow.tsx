import { errorInputClass, normalInputClass,EyeRowProps } from "../types";
import { handleEyeTestFormat } from "../utils/handleEyeTestFormat";

const EyeExtraRow: React.FC<EyeRowProps> = (props) => {

  const { side, register, isView, fieldErrors,setFieldErrors,setValue,getValues }=props
  return (
    <div className="grid grid-cols-[80px_repeat(4,1fr)] md:grid-cols-5 gap-2">
      <div className="flex items-center md:hidden">
        <h3 className="text-lg font-semibold">{side === "right" ? "R" : "L"}</h3>
      </div>

      {/* PD */}
      <div>
        <input
          type="number"
          {...register(`${side}_pupillary_distance`)}
          onBlur={(e) => handleEyeTestFormat({field: `${side}_pupillary_distance`, value: e.target.value,setFieldErrors,setValue,getValues})}
          className={`input-text ${fieldErrors[`${side}_pupillary_distance`] ? errorInputClass : normalInputClass}`}
          placeholder="00"
          min="19"
          max="85"
          step="0.25"
          disabled={isView}
          title="Pupillary distance (mm)"
        />
      </div>

      {/* SG */}
      <div>
        <input
          type="number"
          {...register(`sigmant_${side}`)}
          onBlur={(e) => handleEyeTestFormat({field: `sigmant_${side}`, value: e.target.value,setFieldErrors,setValue,getValues})}
          className={`input-text ${fieldErrors[`sigmant_${side}`] ? errorInputClass : normalInputClass}`}
          placeholder="00"
          min={7}
          max={55}
          step={1}
          disabled={isView}
          title="Sagmant (mm)"
        />
      </div>

      {/* Vertical Distance */}
      <div>
                <input
          type="number"
          {...register(`vertical_distance_${side}`)}
          onBlur={(e) => handleEyeTestFormat({field: `vertical_distance_${side}`, value: e.target.value,setFieldErrors,setValue,getValues})}
          className={`input-text ${fieldErrors[`vertical_distance_${side}`] ? errorInputClass : normalInputClass}`}
          placeholder="00"
          disabled={isView}
          min={10}
          max={15}
          step={1}
          title="Vertical distance (mm)"
        />

      </div>

      {/* VA */}
      <div>
        <input
          type="text"
          {...register(`a_v_${side}`)}
          className={`input-text ${fieldErrors[`a_v_${side}`] ? errorInputClass : normalInputClass}`}
          placeholder="V/A"
          disabled={isView}
          title="Vision acuity"
        />
      </div>

    </div>
  );
};
export default EyeExtraRow;

import { EyeTestValidator } from "./EyeTestValidator";
import { ContactLensValidator } from "./ContactLensValidator";
import { safeToast } from "@/src/shared/utils/safeToast";
interface HandleEyeTestFormatProps {
  field: string;
  value: string;
  setFieldErrors: any;
  setValue: any;
  getValues: any;

}

const validator = new EyeTestValidator();
const contactLensValidator = new ContactLensValidator();
const validatorMap: Record<string, (n: number) => number | string | null> = {
  sphere: (n: number) => validator.validateSPH(n),
  cylinder: (n: number) => validator.validateCYL(n),
  axis: (n: number) => validator.validateAxis(n),
  add: (n: number) => validator.validateADD(n),
  pupillary_distance: (n: number) => validator.validatePD(n),
  sigmant: (n: number) => validator.validateSG(n),
  vertical_distance: (n: number) => validator.validateVertexDistance(n),
};


export const handleEyeTestFormat = (props: HandleEyeTestFormatProps) => {
  const { field, value, setFieldErrors, setValue, getValues } = props

  if (isNaN(Number(value))) {
    setFieldErrors((prev: any) => ({ ...prev, [field]: true }));
    return;
  } else if (!value) {
    setFieldErrors((prev: any) => ({ ...prev, [field]: false }));
    return;
  }
  const num = Number(value);
  const validatorKey = Object.keys(validatorMap).find((k) => field.includes(k));
  console.log(validatorKey, num);

  if (!validatorKey) return;

  const formatted = validatorMap[validatorKey](num);

  const applyValue = (targetField: string, val: string | number) => {
    setValue(targetField, val);
    setFieldErrors((prev: any) => ({ ...prev, [targetField]: false }));
  };

  if (formatted !== null) {
    const mirrorFields: Record<string, string> = {
      right_pupillary_distance: "left_pupillary_distance",
      right_reading_add: "left_reading_add",
      sigmant_right: "sigmant_left",
    };

    if (field in mirrorFields) {
      let val = formatted as number;
      if (field === "right_pupillary_distance" && val >= 45) val = val / 2;
      applyValue(field, val);
      applyValue(mirrorFields[field], val);
    } else {
      applyValue(field, formatted);
    }

    if (
      field.includes("sphere") ||
      field.includes("cylinder") ||
      field.includes("axis")
    ) {

      const side = field.startsWith("right") ? "right" : "left";
      const sph = parseFloat(getValues(`${side}_sphere`));
      const cyl = parseFloat(getValues(`${side}_cylinder`));
      const axis = parseFloat(getValues(`${side}_axis`));

      if (!isNaN(sph) && !isNaN(cyl) && !isNaN(axis)) {
        const transformed = validator.transformSphCylAxis(sph, cyl, axis);
        if (transformed) {
          applyValue(`${side}_sphere`, transformed.sph);
          applyValue(`${side}_cylinder`, transformed.cyl);
          applyValue(`${side}_axis`, transformed.axis);
        }
      }
    }
  } else {

    setFieldErrors((prev: any) => ({ ...prev, [field]: true }));
  }
};


export const validateEyeTest = (data: any) => {

  // validate both eyes
  const right = validator.validatePrescription({
    sphere: data.right_sphere,
    cylinder: data.right_cylinder,
    axis: data.right_axis,
    add: data.right_reading_add,
    pd: data.right_pupillary_distance,
    sg: data.sigmant_right,
  });


  if (!right.valid) {
    right.errors.forEach((err) => safeToast("Right eye: " + err, { type: "error" }));
    return false;
  }


  const left = validator.validatePrescription({
    sphere: data.left_sphere,
    cylinder: data.left_cylinder,
    axis: data.left_axis,
    add: data.left_reading_add,
    pd: data.left_pupillary_distance,
    sg: data.sigmant_left,
  });

  if (!left.valid) {
    left.errors.forEach((err) => safeToast("Left eye: " + err, { type: "error" }));
    return false;
  }
  return true;
}


export const validateContactLens = (data: any) => {

  console.log("data", data);
  const rightSphere = contactLensValidator.convertToSpheric({ SPH: data.right_sphere, CY: data.right_cylinder, AX: data.right_axis, BV: data.vertical_distance_right, ADD: data.right_reading_add });

  const leftSphere = contactLensValidator.convertToSpheric({ SPH: data.left_sphere, CY: data.left_cylinder, AX: data.left_axis, BV: data.vertical_distance_left, ADD: data.left_reading_add });

  const rightToric = contactLensValidator.convertToToric({ SPH: data.right_sphere, CY: data.right_cylinder, AX: data.right_axis, BV: data.vertical_distance_right, ADD: data.right_reading_add });

  const leftToric = contactLensValidator.convertToToric({ SPH: data.left_sphere, CY: data.left_cylinder, AX: data.left_axis, BV: data.vertical_distance_left, ADD: data.left_reading_add });

  return {
    rightSphere,
    leftSphere,
    rightToric,
    leftToric
  }
}
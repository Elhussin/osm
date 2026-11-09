export class ContactLensValidator {
    /**
     * This class is used to validate and convert eyeglass prescriptions
     * from a spherical format to a toric contact lens format.
     * 
     * The class contains two main methods:
     * - convertToSpheric: takes an eyeglass prescription in a spherical format
     *   and returns a contact lens prescription in the same format.
     * - convertToToric: takes an eyeglass prescription in a spherical format
     *   and returns a contact lens prescription in a toric format.
     * 
     * The class also contains several helper methods:
     * - sphericalEquivalent: calculates the spherical equivalent of a given sphere and cylinder.
     * - sphericWithoutVertexDistance: calculates the sphere without the vertex distance.
     * - roundToNearestQuarter: rounds a number to the nearest quarter.
     * - formatResultToQuarter: formats the result of the conversion to a quarter.
     * - formatNumberCustom: formats a number to a string with two decimal places.
     * - isMultipleOfQuarter: checks if a number is a multiple of 0.25.
     * 
     * Example of usage:
     * const validator = new ContactLensValidator();
     * 
     * console.log(
     *   validator.convertToSpheric({ SPH: "-5.25", CY: "-1.00", AX: "90", BV: "12", ADD: "2.00" })
     * );
     * 
     * console.log(
     *   validator.convertToToric({ SPH: "-5.25", CY: "-1.00", AX: "90", BV: "12", ADD: "2.00" })
     * );
     */

    convertToSpheric(data: Record<string, string | number>): Record<string, string | number> {
      const sphere = String(data["SPH"] ?? "0").trim();
      const cylinder = String(data["CY"] ?? "0").trim();
      const axis = String(data["AX"] ?? "0").trim();
      const vertexDistance = String(data["BV"] ?? "12").trim();
      const add = String(data["ADD"] ?? "0").trim();
  
      const sph = sphere ? parseFloat(sphere) : 0;
      const cyl = cylinder ? parseFloat(cylinder) : 0;
      const ax = axis ? parseFloat(axis) : 0;
      const bv = vertexDistance ? parseFloat(vertexDistance) : 12;
      const addValue = add ? parseFloat(add) : 0;
       console.log(sph,cyl,ax,bv,addValue,vertexDistance,data["BV"]);
  
      const totalSphere = Math.abs(cyl) !== 0 ? this.sphericalEquivalent(sph, cyl) : sph;
  
      const sphereContactLens =
        Math.abs(totalSphere) > 4
          ? this.sphericWithoutVertexDistance(totalSphere, bv)
          : totalSphere;
  
      const nearestValue = this.roundToNearestQuarter(sphereContactLens);
  
      let value: Record<string, string | number> = {
        SPH: nearestValue,
        ADD: addValue,
      };
  
      value = this.formatResultToQuarter(value);
      value["Exact SPH"] = `${sphereContactLens >= 0 ? "+" : ""}${sphereContactLens.toFixed(2)}`;
      value["AX"] = "";
      value["BV"] = bv;
  
      return value;
    }
  
    /**
     * Convert an eyeglass prescription to a toric contact lens prescription.
     */
    convertToToric(data: Record<string, string | number>): Record<string, string | number> {
      const sphere = String(data["SPH"] ?? "0").trim();
      const cylinder = String(data["CY"] ?? "0").trim();
      const axis = String(data["AX"] ?? "0").trim();
      const vertexDistance = String(data["BV"] ?? "12").trim();
      const add = String(data["ADD"] ?? "0").trim();
  
      const sph = sphere ? parseFloat(sphere) : 0;
      const cyl = cylinder ? parseFloat(cylinder) : 0;
      const ax = axis ? parseFloat(axis) : 0;
      const bv = vertexDistance ? parseFloat(vertexDistance) : 12;
      const addValue = add ? parseFloat(add) : 0;
  
      const spherPower = this.sphericWithoutVertexDistance(sph, bv);
      const cylinderPower =
        this.sphericWithoutVertexDistance(sph + cyl, bv) - spherPower;
  
      const nearestCylinder = this.roundToNearestQuarter(cylinderPower);
      const nearestSphere = this.roundToNearestQuarter(spherPower);
  
      let value: Record<string, string | number> = {
        SPH: nearestSphere,
        CY: nearestCylinder,
        ADD: addValue,
      };
  
      value = this.formatResultToQuarter(value);
      value["Exact SPH"] = `${spherPower >= 0 ? "+" : ""}${spherPower.toFixed(2)}`;
      value["Exact CY"] = `${cylinderPower >= 0 ? "+" : ""}${cylinderPower.toFixed(2)}`;
      value["AX"] = `${ax.toFixed(0)}`;
      value["BV"] = bv;
  
      return value;
    }
  
    private formatResultToQuarter(value: Record<string, string | number>): Record<string, string | number> {
      
      for (const key in value) {
        value[key] = this.formatNumberCustom(value[key]);
      }
      return value;
    }
  
    private sphericWithoutVertexDistance(sphere: number, vertexDistance: number): number {
      return sphere / (1 - (vertexDistance / 1000) * sphere);
    }
  
    private sphericalEquivalent(sphere: number, cylinder: number): number {
      return parseFloat((sphere + cylinder / 2).toFixed(2));
    }
  
    private roundToNearestQuarter(num: number): number {
      return Math.round(num * 4) / 4;
    }
  
    private formatNumberCustom(value: string | number) :any {
      const num = typeof value === "number" ? value : parseFloat(String(value));
      if (this.isMultipleOfQuarter(num)) {
        return `${num >= 0 ? "+" : ""}${num.toFixed(2)}`;
      }
    
    }
  
    private isMultipleOfQuarter(value: number): boolean {
      return value % 0.25 === 0;
    }
  }
  
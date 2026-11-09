type LensOption = {
    value: string;
    label: string;
  };
  
  export function generateLensOptions(min: number, max: number, step: number = 0.25, sign:boolean=true): LensOption[] {
    const options: LensOption[] = [];
    let valueNum = 0;
    let signValue = '';
    let formatted = '';
    let absValue = '';
    for (let i = min; i <= max; i += step) {

 
      if(sign){
        valueNum = Number(i.toFixed(2)); // لتجنب أخطاء float
        signValue = valueNum >= 0 ? '+' : '-';
        absValue = Math.abs(valueNum).toFixed(2).padStart(5, '0');
        formatted = `${signValue}${absValue}`;
    
      }
      else{
        formatted = `${i}`;
      }

      options.push({
        value: formatted,
        label: formatted
      });
    }
  
    return options;
  }
  
//   // مثال على الاستخدام:
//   const lensOptions = generateLensOptions(-30, 10);
//   console.log(lensOptions);
  
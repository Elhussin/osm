import {onSubmit} from "./onsbmit";
import { buildPayload } from "@/src/features/products/utils/buildPayload";

export const handleSave = (form: any, variants: any,config:any,id?:string) => {
    console.log("variants",variants)
    
    form.handleSubmit((formValues: any) => {
        const variantsPayload = buildPayload({
            config: config,
            formData: variants,
            options: { multiple: true, include: ["product"], prefix: "variants" },
        });


        const finalPayload = {
            ...formValues,
            variants: variantsPayload,
        };
        console.log("finalPayload",finalPayload)
        onSubmit(finalPayload,form,id);
    })();
};
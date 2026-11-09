

"use client";
import LoginForm from "@/src/features/auth/components/LoginForm";
import { getSubdomain} from "@/src/shared/utils/getSubdomain";
import {useTranslations} from 'next-intl';
import {formRequestProps} from "@/src/shared/types";


export default  function RegisterPage(){
const t = useTranslations('register');
const t2 = useTranslations('tenants');
const subdomain = getSubdomain();

  const props: formRequestProps = {
    alias: "users_register_create",
    submitText: t("button"),
    mode: "create",
    title: t("title"),
    message: t("message"),
    istenant: false,
  };

  if (!subdomain) {
    props.alias = "tenants_register_create";
    props.message = t2("message");
    props.istenant = true;
    props.title = t2("title");
    props.submitText = t2("button");
  }

  return (
    <LoginForm 
      istenant={props.istenant}
      alias={props.alias}
      submitText={props.submitText}
      mode="create"
      title={props.title}
      message={props.message}     
    />
  );
}
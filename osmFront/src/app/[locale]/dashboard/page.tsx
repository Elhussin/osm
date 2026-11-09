"use client";
import { useTranslations } from "next-intl";

import {Link} from "@/src/app/i18n/navigation";
import { useUser } from "@/src/features/auth/hooks/UserContext";

export default function DashboardLinks() {
  const {user} =useUser()
  // console.log(user)
  // load the form config for each link translated
  const t = useTranslations("formsConfig");
  const links = [
    // Tenant
    { href: "clients", roles: ["OWNER"], group: "Tenant" },
    { href: "register-tenants", roles: ["OWNER"], group: "Tenant" },
    { href: "domains", roles: ["OWNER"], group: "Tenant" },
    { href: "payments", roles: ["OWNER"], group: "Billing" },
    { href: "subscription-plans", roles: ["OWNER"], group: "Billing" },
    // Users
    { href: "roles", roles: ["OWNER"], group: "Access Control" },
    { href: "users", roles: ["OWNER"], group: "Access Control" },
    { href: "permissions", roles: ["OWNER"], group: "Access Control" },
    { href: "role-permissions", roles: ["OWNER"], group: "Access Control" },
    { href: "contact-us", roles: ["OWNER"], group: "Support" },
    { href: "tenant-settings", roles: ["OWNER"], group: "Settings" },
    { href: "departments", roles: ["OWNER"], group: "Settings" },
    { href: "employees", roles: ["OWNER"], group: "Branch" },
    { href: "customers", roles: ["OWNER"], group: "Customer" },
    { href: "prescriptions", roles: ["OWNER"], group: "Prescriptions" },
    { href: "branch-users", roles: ["OWNER"], group: "Branch" },
    { href: "branches", roles: ["OWNER"], group: "Branch" },
    { href: "attributes", roles: ["OWNER"], group: "Product" },
    { href: "attribute-values", roles: ["OWNER"], group: "Product" },
    { href: "suppliers", roles: ["OWNER"], group: "Product" },
    { href: "manufacturers", roles: ["OWNER"], group: "Product" },
    { href: "brands", roles: ["OWNER"], group: "Product" },
    { href: "categories", roles: ["OWNER"], group: "Product" },
    { href: "lens-coatings", roles: ["OWNER"], group: "Product" },
    { href: "products", roles: ["OWNER"], group: "Product" },
    { href: "product-variants", roles: ["OWNER"], group: "Product" },
    { href: "product-images", roles: ["OWNER"], group: "Product" },
    { href: "flexible-prices", roles: ["OWNER"], group: "Product" },
  ];
  
  const userRole = user?.role?.name?.toUpperCase(); // "OWNER"

  const allowedLinks = links.filter(link => link.roles.includes(userRole));
  

  const groupedLinks = allowedLinks.reduce((acc, link) => {
    if (!acc[link.group]) acc[link.group] = [];
    acc[link.group].push(link);
    return acc;
  }, {} as Record<string, typeof links>);
  
  return (
    <div className="space-y-6">
      {Object.entries(groupedLinks).map(([group, links]) => (
        <div key={group}>
          <h2 className="text-lg font-bold mb-2">{group}</h2>
          <div className="grid gap-4 grid-cols-2 md:grid-cols-3 lg:grid-cols-4">
            {links.map(({ href }) => (
              <Link href={`/dashboard/${href}/`} key={href} className="card ">
                {t(href)}
              </Link>
            ))}
          </div>
        </div>
      ))}
    </div>
  );
  
}


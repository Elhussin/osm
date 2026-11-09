import { NextResponse, NextRequest } from "next/server";

export function getRequiredPermission(pathname: string): string | null {
  // Clean the path by removing the language prefix
  const cleanPath = pathname.replace(/^\/(ar|en)/, "") || "/";

  // The root path does not require permission
  if (cleanPath === "/") return null;

  // Public paths that do not require special permissions
  const publicPaths = [
    "/about",
    "/contact",
    "/services",
    "/pricing",
    "/faq",
    "/terms",
    "/views",
    "/privacy",
    "/support",
    "/careers",
    "/blog",
    "/unauthorized",
    "/auth/login",
    "/auth/register",
    "/auth/activate",
    "/auth/forgot-password",
    "/auth/reset-password",
  ];

  if (publicPaths.includes(cleanPath)) return null;
  if (cleanPath === "/dashboard") {
    return "authenticated_user";
  }
  // 🔹 Map مجموعات المسارات لصلاحية واحدة
  const groupPermissions: [RegExp, string][] = [
    // Admin panel كله يحتاج "admin_access"
    [/^\/admin(\/|$)/, "admin_access"],
    // Dashboard كله يحتاج "view_dashboard"
    // [/^\/dashboard(\/|$)/, "view_dashboard"],
    [/^\/dashboard\/users/, "view_users"],
    [/^\/dashboard\/roles/, "view_roles"],
    [/^\/dashboard\/permissions/, "view_permissions"],
    [/^\/dashboard\/reports/, "view_reports"],
    [/^\/dashboard\/payments/, "view_payments"],

    // Reports كله يحتاج "view_reports"
    [/^\/reports(\/|$)/, "view_reports"],

    // Users كله يحتاج "view_users"
    [/^\/users(\/|$)/, "view_users"],

    // Prescriptions
    [/^\/prescriptions\/(create|new)/, "create_prescription"],
    [/^\/prescriptions\/edit/, "edit_prescription"],
    [/^\/prescriptions(\/|$)/, "view_prescriptions"],

    // Invoices
    [/^\/invoices\/(create|new)/, "create_invoice"],
    [/^\/invoices\/edit/, "edit_invoice"],
    [/^\/invoices(\/|$)/, "view_invoices"],
  ];

  for (const [regex, permission] of groupPermissions) {
    if (regex.test(cleanPath)) return permission;
  }
  // By default, unknown paths require login but without special permissions
  return "authenticated_user";
}

export function unauthorizedResponse(
  request: NextRequest,
  target: string,
  message: string
) {
  // Using the request to get the correct URL
  const redirectUrl = new URL(target, request.url);

  // Add redirect information
  redirectUrl.searchParams.set("redirect", request.nextUrl.pathname);
  // redirectUrl.searchParams.set('message', encodeURIComponent(message));

  const response = NextResponse.redirect(redirectUrl);

  // Set cookies with better options
  response.cookies.set("alert_message", message, {
    path: "/",
    maxAge: 30, // 30 seconds
    httpOnly: false, // allow JavaScript to read it
    secure: process.env.NODE_ENV === "production",
  });

  response.cookies.set("alert_type", "error", {
    path: "/",
    maxAge: 30,
    httpOnly: false,
    secure: process.env.NODE_ENV === "production",
  });

  return response;
}




export const dashboardPermissions: Record<string, string[]> = {
  "/dashboard": ["authenticated_user"],

  // Owner
  "/dashboard/subscription": ["manage_subscription"],
  "/dashboard/billing": ["manage_billing"],
  "/dashboard/domain": ["manage_domain"],

  // Owner + Admin
  "/dashboard/users": ["view_users"],
  "/dashboard/roles": ["manage_roles"],
  "/dashboard/permissions": ["manage_permissions"],
  "/dashboard/reports": ["view_reports"],

  // Staff
  "/dashboard/prescriptions": ["view_prescriptions"],
  "/dashboard/prescriptions/create": ["create_prescription"],
  "/dashboard/invoices": ["view_invoices"],
  "/dashboard/invoices/create": ["create_invoice"],

  // Super Admin
  "/super-admin/tenants": ["manage_all_tenants"],
  "/super-admin/users": ["manage_all_users"],
  "/super-admin/reports": ["view_all_reports"],
};

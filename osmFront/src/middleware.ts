import { NextRequest, NextResponse } from "next/server";
import { jwtVerify } from "jose";
import createIntlMiddleware from "next-intl/middleware";
import { routing } from "./app/i18n/routing";
import {
  getRequiredPermission,
  unauthorizedResponse,
} from "./shared/utils/middlewareHelper";

const DEFAULT_LOCALE = "en";
const PUBLIC_SUBDOMAIN = "public";

export const config = {
  // Matches all paths except api, static files, images, etc.
  matcher: ["/((?!api|trpc|_next|_vercel|.*\\..*).*)"],
};

const intl = createIntlMiddleware(routing);

// Helper to get locale from path
function extractLocale(pathname: string): string | null {
  const match = pathname.match(/^\/(ar|en)(?=\/|$)/);
  return match ? match[1] : null;
}

export async function middleware(request: NextRequest) {
  const { pathname } = request.nextUrl;

  // -----------------------------------------------------------------------------
  // 1. Tenant Resolution
  // -----------------------------------------------------------------------------
  const host = request.headers.get("host") || "";
  let subdomain = host.split(".")[0];
  if (subdomain.startsWith("localhost")) subdomain = PUBLIC_SUBDOMAIN;

  // -----------------------------------------------------------------------------
  // 2. Auth & Locale Discovery
  // -----------------------------------------------------------------------------
  const token = request.cookies.get("access_token")?.value;
  const locale = extractLocale(pathname) || DEFAULT_LOCALE;

  // -----------------------------------------------------------------------------
  // 3. Guest Optimization (Skip Auth Pages if Logged In)
  // -----------------------------------------------------------------------------
  // Regex ensures we only match /auth/login, /auth/register, not /author
  const isAuthPage = new RegExp(`^/(${locale}/)?auth/`).test(pathname);

  if (token && isAuthPage) {
    const homeUrl = new URL(`/${locale}`, request.url);
    const response = NextResponse.redirect(homeUrl);
    response.cookies.set("tenant", subdomain, { path: "/" });
    return response;
  }

  // -----------------------------------------------------------------------------
  // 4. Authorization & Security Checks
  // -----------------------------------------------------------------------------
  const requiredPermission = getRequiredPermission(pathname);

  if (requiredPermission) {
    // A. Check for Token Presence
    if (!token) {
      const loginPath = `/${locale}/auth/login`;
      const msg = locale === "ar"
        ? "تحتاج لتسجيل الدخول للوصول لهذه الصفحة"
        : "You need to login to access this page";
      return unauthorizedResponse(request, loginPath, msg);
    }

    // B. Verify Token & Claims
    try {
      const secret = process.env.JWT_SECRET;
      if (!secret) throw new Error("JWT_SECRET is not defined");

      const { payload } = await jwtVerify(token, new TextEncoder().encode(secret));
      const userTenant = payload.tenant as string;
      const permissions = (payload.permissions as string[]) || [];

      // Guard: Tenant Isolation
      if (userTenant !== subdomain) {
        throw new Error("Tenant mismatch");
      }

      // Guard: Permissions
      const hasPermission =
        permissions.includes("__all__") ||
        permissions.includes(requiredPermission) ||
        requiredPermission === "authenticated_user";

      if (!hasPermission) {
        throw new Error("Insufficient permissions");
      }

    } catch (error: any) {
      const isMismatch = error.message === "Tenant mismatch" || error.message === "Insufficient permissions";
      const unauthorizedPath = `/${locale}/unauthorized`;

      const msg = locale === "ar"
        ? (isMismatch ? "تم انتقالك لصفحة غير مصرح بها" : "فشل تسجيل الدخول أو انتهاء الجلسة")
        : (isMismatch ? "Access denied" : "Login failed or session expired");

      const res = unauthorizedResponse(
        request,
        isMismatch ? unauthorizedPath : `/${locale}/auth/login`,
        msg
      );

      // Only clear token if it wasn't a logic mismatch (i.e., only clear if token is invalid/expired)
      if (!isMismatch) {
        res.cookies.delete("access_token");
      }
      return res;
    }
  }

  // -----------------------------------------------------------------------------
  // 5. Final Response Handling (i18n + Cookies)
  // -----------------------------------------------------------------------------
  const response = intl(request);

  response.cookies.set({
    name: "tenant",
    value: subdomain,
    path: "/",
    httpOnly: false,
    secure: process.env.NODE_ENV === "production",
    sameSite: "lax",
    maxAge: 60 * 60 * 24 * 30, // 30 Days
  });

  return response;
}

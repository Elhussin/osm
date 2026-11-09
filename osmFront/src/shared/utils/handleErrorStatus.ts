import {translate} from "./translate";
import type { NormalizedError } from "../types";

/**
 * Handle server errors and return a normalized error object.
 *
 * @param error - The error object to handle.
 * @param t - Optional translation function.
 * @returns A normalized error object.
 */

export function handleErrorStatus(error: any, t?: (key: string) => string): NormalizedError {
  if (!error || typeof error !== "object") {
    return { message: translate("error.unknown", t) || "Unknown error occurred" };
  }

  if (!error.response) {
    return {
      message: translate("error.network", t) || "Network error. Please check your internet connection.",
      code: "NETWORK_ERROR",
    };
  }

  const status = error.response.status || error.status;
  const detail = error.response.data?.detail || error.message;

  const statusMessages: Record<number, string> = {
    400: translate("error.validation", t) || "Validation error occurred",
    401: translate("error.unauthorized", t) || "Unauthorized access",
    403: translate("error.forbidden", t) || "Forbidden access",
    404: translate("error.notFound", t) || "Resource not found",
    408: translate("error.timeout", t) || "Request timeout, please try again",
    422: translate("error.unprocessable", t) || "Unprocessable entity",
    429: translate("error.tooManyRequests", t) || "Too many requests, please try again later",
    500: translate("error.internalServer", t) || "Internal server error",
    503: translate("error.serviceUnavailable", t) || "Service unavailable",
  };

  return {
    message: detail || statusMessages[status] || translate("error.unexpected", t) || "An unexpected error occurred.",
    code: status,
    details: error.response.data,
  };
}
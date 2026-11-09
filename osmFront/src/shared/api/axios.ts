// lib/axios.ts
'use client';
import axios, { AxiosError, InternalAxiosRequestConfig } from "axios";
import { endpoints } from "./schemas";

// import dynamic from 'next/dynamic';

// const endpoints = dynamic(
//   () => import('./schemas'),
//   { ssr: false }
// );

import { getBaseUrl } from "@/src/shared/utils/getBaseUrl";
import { Zodios, type ZodiosInstance } from "@zodios/core";
import { parseCookies } from "nookies"; // مكتبة صغيرة لقراءة الكوكيز في server/client

interface CustomZodiosInstance extends ZodiosInstance<typeof endpoints> {
  customRequest: (alias: string, data?: any) => Promise<any>;
}

const axiosInstance = axios.create({
  withCredentials: true,
  timeout: 30000,
  headers: {
    "Content-Type": "application/json",
  },
});

const setHeader = (
  config: InternalAxiosRequestConfig,
  key: string,
  value?: string
) => {
  if (value) {
    config.headers = config.headers || {};
    config.headers[key] = value;
  }
};

axiosInstance.interceptors.request.use((config: InternalAxiosRequestConfig) => {
  const cookies = parseCookies();

  const csrfToken = cookies["optics_tenant_csrftoken"];
  const tenant = cookies["tenant"] || "public";
  const language = cookies["language"] || process.env.DEFAULT_LANGUAGE;
  const country = cookies["country"] || process.env.DEFAULT_COUNTRY;
  const currency = cookies["currency"] || process.env.DEFAULT_CURRENCY;

  config.baseURL = getBaseUrl(undefined, false);

  // ضبط الهيدرز
  setHeader(config, "X-OPTICS-TENANT-CSRFToken", csrfToken);
  setHeader(config, "X-Tenant", tenant);
  setHeader(config, "Accept-Language", language);
  setHeader(config, "Accept-Country", country);
  setHeader(config, "Accept-Currency", currency);


  return config;
});

let refreshTokenPromise: Promise<any> | null = null;

axiosInstance.interceptors.response.use(
  (response) => response,
  async (error: AxiosError) => {
    const originalRequest = error.config as InternalAxiosRequestConfig & {
      _retry?: boolean;
    };

    if (error.response?.status !== 401 || originalRequest._retry) {
      return Promise.reject(error);
    }

    originalRequest._retry = true;

    try {
      if (refreshTokenPromise) {
        await refreshTokenPromise;
      } else {
        refreshTokenPromise = axiosInstance.post("/api/users/token/refresh/");
        await refreshTokenPromise;
        refreshTokenPromise = null;
      }

      return axiosInstance(originalRequest);
    } catch (refreshError) {
      refreshTokenPromise = null;
      // window.location.href = '/auth/login';
      return Promise.reject(refreshError);
    }
  }
);

export const api: CustomZodiosInstance = new Zodios(endpoints, {
  axiosInstance,
}) as CustomZodiosInstance;

function replacePathParams(url: string, params: Record<string, any>): string {
  let processedUrl = url;
  Object.entries(params).forEach(([key, value]) => {
    processedUrl = processedUrl.replace(`:${key}`, encodeURIComponent(value));
  });
  return processedUrl;
}

// function replacePathParams(url: string, params: Record<string, any>) {
//   return url.replace(/:([a-zA-Z_][a-zA-Z0-9_]*)/g, (_, key) => {
//     if (params[key] === undefined) {
//       throw new Error(`Missing path parameter: ${key}`);
//     }
//     return encodeURIComponent(params[key]);
//   });
// }


api.customRequest = async function (alias: string, data: any = {}) {
  const endpoint: any = endpoints.find((e) => e.alias === alias);
  if (!endpoint) {
    throw new Error(`Endpoint with alias "${alias}" not found.`);
  }

  const method = endpoint.method.toUpperCase();
  let url: string = endpoint.path;
  const pathParams: Record<string, any> = {};
  const otherParams: Record<string, any> = {};

  const pathParamPattern: RegExp = /:([a-zA-Z_][a-zA-Z0-9_]*)/g;
  const pathParamNames: any[] = [];
  let match: any;

  while ((match = pathParamPattern.exec(url)) !== null) {
    pathParamNames.push(match[1]);
  }

  if (data && typeof data === "object") {

    Object.entries(data).forEach(([key, value]) => {
      if (value === undefined || value === null) return; // ✅ تجاهل القيم غير المعرفة
      if (pathParamNames.includes(key)) {
        pathParams[key] = value;
      } else {
        otherParams[key] = value;
      }
    });
    
    // Object.entries(data).forEach(([key, value]) => {
    //   if (pathParamNames.includes(key)) {
    //     pathParams[key] = value;
    //   } else {
    //     otherParams[key] = value;
    //   }
    // });
  }

  url = replacePathParams(url, pathParams);

  const config: any = {
    method: method,
    url: url,
  };

  if (method === "GET" || method === "DELETE") {
    if (Object.keys(otherParams).length > 0) {
      config.params = otherParams;
    }
  } else {
    config.data = otherParams;
  }

  try {
    const response = await axiosInstance(config);
    return response.data;
  } catch (error) {
    throw error;
  }
};

declare module "@zodios/core" {
  interface ZodiosInstanceN {
    customRequest: (alias: string, data?: any) => Promise<any>;
  }
}

export default api;

export { axiosInstance };

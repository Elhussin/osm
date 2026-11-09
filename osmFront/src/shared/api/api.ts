
import { axiosInstance } from "./axios";
import { apiConfig } from "./apiConfig";
import { getBaseUrl } from "@/src/shared/utils/getBaseUrl";



interface FetchDataProps {
  ignoreSubdomain?: boolean;
  url?: string;
}

export const FetchData = async ({ ignoreSubdomain , url }: FetchDataProps) => {
  try {
    apiConfig.ignoreSubdomain = ignoreSubdomain || true;
    const baseUrl = getBaseUrl(undefined, apiConfig.ignoreSubdomain);
    const res = await axiosInstance.get(`${baseUrl}${url}`);
    return res.data;
  } catch (error) {
    console.error("Error fetching client data:", error);
    return null;
  }
};
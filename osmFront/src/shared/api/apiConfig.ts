
export const apiConfig = {
    ignoreSubdomain: false // 🔄 غيرها إلى true لتجاهل الـ subdomain
  };
  
  const baseUrl = process.env.NEXT_PUBLIC_API_BASE;
  const port = process.env.NEXT_PUBLIC_PORT;
  const PROTOCOL = process.env.NEXT_PUBLIC_PROTOCOL;
  let url : string;
  if (!port) {
      url = `${PROTOCOL}://${baseUrl}`;
  }else{
     url = `${PROTOCOL}://${baseUrl}:${port}`;
  }

export default url;



import { headers } from 'next/headers';

export async function getSubdomainServer(): Promise<string | null> {
  const host = (await headers()).get('host') ?? '';
  const hostname = host.split(':')[0];

  // استثناء localhost
  if (!hostname || hostname === 'localhost') {
    return null;
  }

  // دعم subdomain.localhost
  if (hostname.endsWith('.localhost')) {
    const parts = hostname.split('.');
    return parts.length === 2 ? parts[0] : null;
  }

  // حالات production (مثال: store1.example.com)
  const parts = hostname.split('.');
  return parts.length > 2 ? parts[0] : null;
}

/**
 * Centralized API Base URL helper for Homelab Frontend.
 *
 * If NEXT_PUBLIC_API_URL is provided, it uses that explicit URL.
 * Otherwise, it defaults to an empty string "", producing relative requests (e.g. /api/v1/...).
 * Relative requests are automatically proxied by Next.js (configured via rewrites in next.config.js)
 * to http://backend:8000 inside the Docker network.
 *
 * This allows the entire platform (Frontend + Backend APIs) to work securely behind
 * a single port / Cloudflare Tunnel without exposing the backend port (8000) publicly.
 */
export const getApiBaseUrl = (): string => {
  if (typeof window !== "undefined") {
    return process.env.NEXT_PUBLIC_API_URL || "";
  }
  return process.env.BACKEND_INTERNAL_URL || "http://backend:8000";
};

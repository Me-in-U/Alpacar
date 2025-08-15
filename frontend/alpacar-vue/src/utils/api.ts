// src/utils/api.ts
// BASE URL 정규화 + 리프레시 토큰 갱신 유틸
import { SecureTokenManager } from "@/utils/security";

// 환경변수에 슬래시가 붙어있어도 문제 없도록 마지막 슬래시 제거
export const BACKEND_BASE_URL: string = (
  import.meta.env.VITE_BACKEND_BASE_URL || "https://i13e102.p.ssafy.io/api"
).replace(/\/+$/, "");

export const FRONTEND_BASE_URL: string = (
  import.meta.env.VITE_FRONTEND_BASE_URL || "https://i13e102.p.ssafy.io"
).replace(/\/+$/, "");

// 프로젝트에서 사용할 수 있는 refresh 엔드포인트 후보들
const REFRESH_ENDPOINTS = [
  "/auth/token/refresh/",
  "/api/token/refresh/",
] as const;

/**
 * 리프레시 토큰으로 액세스 토큰 재발급 시도
 * - 성공 시: 새 access(및 회전된 refresh가 있으면 저장) 후 access 문자열 반환
 * - 실패 시: null 반환
 */
export async function tryRefreshToken(): Promise<string | null> {
  const refresh = SecureTokenManager.getSecureToken("refresh_token");
  if (!refresh) return null;

  for (const ep of REFRESH_ENDPOINTS) {
    try {
      const resp = await fetch(`${BACKEND_BASE_URL}${ep}`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Accept: "application/json",
        },
        credentials: "include", // 배포 환경(HTTPS/CORS) 호환성 ↑
        body: JSON.stringify({ refresh }),
        cache: "no-cache",
        keepalive: true,
      });

      if (!resp.ok) continue;

      const data = await resp.json().catch(() => ({} as any));
      const newAccess = data?.access as string | undefined;
      const newRefresh = data?.refresh as string | undefined; // 회전 사용 시 도착

      if (newAccess) {
        // access는 세션 기반 보관(브라우저 종료 시 사라짐)
        SecureTokenManager.setSecureToken("access_token", newAccess, true);
      }
      if (newRefresh) {
        // refresh 회전 시 새 토큰은 영구 보관
        SecureTokenManager.setSecureToken("refresh_token", newRefresh, false);
      }

      return newAccess ?? null;
    } catch {
      // 다음 후보 엔드포인트로 계속 시도
    }
  }

  return null;
}

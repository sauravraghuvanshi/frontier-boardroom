const API = import.meta.env.VITE_API_BASE || "http://localhost:8000";

export const ENTRA_AUTH_ENABLED =
  import.meta.env.VITE_ENTRA_AUTH_ENABLED === "true";

function loginUrl(): string {
  const login = new URL("/.auth/login/aad", window.location.origin);
  login.searchParams.set("post_login_redirect_uri", window.location.href);
  return login.toString();
}

async function redirectToLogin(): Promise<never> {
  window.location.assign(loginUrl());
  return new Promise<never>(() => undefined);
}

export async function backendFetch(
  input: RequestInfo | URL,
  init: RequestInit = {},
): Promise<Response> {
  try {
    const response = await fetch(input, { ...init, credentials: "same-origin" });
    if (response.status === 401 && ENTRA_AUTH_ENABLED) {
      await redirectToLogin();
    }
    return response;
  } catch (error) {
    if (ENTRA_AUTH_ENABLED) {
      await redirectToLogin();
    }
    throw error;
  }
}

export function signOut(): void {
  if (!ENTRA_AUTH_ENABLED) return;

  const logout = new URL("/.auth/logout", window.location.origin);
  logout.searchParams.set("post_logout_redirect_uri", window.location.origin);
  window.location.assign(logout.toString());
}

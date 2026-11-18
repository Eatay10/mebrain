/**
 * Sözleşmeden üretilmiş tipli API client'ı (R-API-06). Web uygulaması API'ye SADECE bunun üzerinden erişir.
 * Cookie oturumu kullanılır; durum değiştiren isteklere CSRF token'ı otomatik eklenir.
 */
import createClient, { type Middleware } from "openapi-fetch";
import type { components, paths } from "./schema";

export type { components, paths };
export type Schemas = components["schemas"];

const UNSAFE = new Set(["POST", "PUT", "PATCH", "DELETE"]);

function readCookie(name: string): string | undefined {
  return document.cookie
    .split("; ")
    .find((c) => c.startsWith(`${name}=`))
    ?.slice(name.length + 1);
}

const csrf: Middleware = {
  onRequest({ request }) {
    if (UNSAFE.has(request.method)) {
      const token = readCookie("cth_csrf");
      if (token) request.headers.set("X-CSRF-Token", decodeURIComponent(token));
    }
    return request;
  },
};

export class ApiError extends Error {
  constructor(
    public status: number,
    public problem: Schemas["Problem"] | undefined,
  ) {
    super(problem?.detail ?? problem?.title ?? `HTTP ${status}`);
  }
}

export function createApi(baseUrl = "/api/v1") {
  const client = createClient<paths>({ baseUrl, credentials: "same-origin" });
  client.use(csrf);
  return client;
}

/** openapi-fetch sonucunu açar: hata varsa ApiError fırlatır. */
export async function unwrap<T>(p: Promise<{ data?: T; error?: unknown; response: Response }>): Promise<T> {
  const { data, error, response } = await p;
  if (!response.ok) throw new ApiError(response.status, error as Schemas["Problem"] | undefined);
  return data as T;
}

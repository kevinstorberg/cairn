import { resolveRuntimeConfig } from "../config";

export const REQUEST_ID_HEADER = "x-request-id";

export interface ErrorDetail {
  field?: string;
  message: string;
  type: string;
}

export interface ErrorBody {
  code: string;
  message: string;
  details: ErrorDetail[];
  request_id: string;
}

export interface ErrorEnvelope {
  error: ErrorBody;
}

export interface ApiResult<T> {
  data: T;
  requestId?: string;
  response: Response;
}

export interface ApiClient {
  request<T>(path: string, options?: RequestInit): Promise<ApiResult<T>>;
  get<T>(path: string, options?: RequestInit): Promise<ApiResult<T>>;
  post<T>(path: string, body: unknown, options?: RequestInit): Promise<ApiResult<T>>;
  patch<T>(path: string, body: unknown, options?: RequestInit): Promise<ApiResult<T>>;
  delete<T>(path: string, options?: RequestInit): Promise<ApiResult<T>>;
}

export interface ApiClientOptions {
  baseUrl?: string;
  fetch?: typeof fetch;
  getToken?: () => string | null | undefined;
}

export class ApiClientError extends Error {
  readonly status: number;
  readonly code: string;
  readonly details: ErrorDetail[];
  readonly requestId?: string;

  constructor(
    message: string,
    options: { status: number; code: string; details: ErrorDetail[]; requestId?: string },
  ) {
    super(message);
    this.name = "ApiClientError";
    this.status = options.status;
    this.code = options.code;
    this.details = options.details;
    this.requestId = options.requestId;
  }
}

export function createApiClient(options: ApiClientOptions = {}): ApiClient {
  const runtime = resolveRuntimeConfig();
  const baseUrl = (options.baseUrl || runtime.apiBaseUrl).replace(/\/$/, "");
  const fetchImpl = options.fetch || fetch;

  async function request<T>(path: string, requestOptions: RequestInit = {}): Promise<ApiResult<T>> {
    if (!path.startsWith("/")) {
      throw new Error(`API paths must start with '/': ${path}`);
    }

    const response = await fetchImpl(`${baseUrl}${path}`, withDefaultHeaders(requestOptions, options.getToken));
    const requestId = response.headers.get(REQUEST_ID_HEADER) ?? undefined;
    const payload = await readPayload(response);

    if (response.ok) {
      return { data: payload as T, requestId, response };
    }

    throw errorFromResponse(response, payload, requestId);
  }

  return {
    request,
    get: (path, requestOptions) => request(path, { ...requestOptions, method: "GET" }),
    post: (path, body, requestOptions) => request(path, jsonRequest("POST", body, requestOptions)),
    patch: (path, body, requestOptions) => request(path, jsonRequest("PATCH", body, requestOptions)),
    delete: (path, requestOptions) => request(path, { ...requestOptions, method: "DELETE" }),
  };
}

function withDefaultHeaders(options: RequestInit, getToken?: ApiClientOptions["getToken"]): RequestInit {
  const headers = new Headers(options.headers);
  if (!headers.has("Accept")) {
    headers.set("Accept", "application/json");
  }
  const token = getToken?.();
  if (token) {
    headers.set("Authorization", `Bearer ${token}`);
  }
  return { ...options, headers };
}

function jsonRequest(method: string, body: unknown, options: RequestInit = {}): RequestInit {
  const headers = new Headers(options.headers);
  if (!headers.has("Content-Type")) {
    headers.set("Content-Type", "application/json");
  }
  return {
    ...options,
    body: JSON.stringify(body),
    headers,
    method,
  };
}

async function readPayload(response: Response): Promise<unknown> {
  const contentType = response.headers.get("content-type") || "";
  if (contentType.includes("application/json")) {
    return response.json();
  }
  return response.text();
}

function errorFromResponse(response: Response, payload: unknown, requestId?: string): ApiClientError {
  if (isErrorEnvelope(payload)) {
    return new ApiClientError(payload.error.message, {
      status: response.status,
      code: payload.error.code,
      details: payload.error.details,
      requestId: payload.error.request_id || requestId,
    });
  }

  if (typeof payload === "string" && payload.trim()) {
    return new ApiClientError(payload, {
      status: response.status,
      code: "http_error",
      details: [],
      requestId,
    });
  }

  return new ApiClientError(response.statusText || "Request failed", {
    status: response.status,
    code: "http_error",
    details: [],
    requestId,
  });
}

function isErrorEnvelope(value: unknown): value is ErrorEnvelope {
  if (!isRecord(value) || !isRecord(value.error)) {
    return false;
  }
  const error = value.error;
  return (
    typeof error.code === "string" &&
    typeof error.message === "string" &&
    Array.isArray(error.details) &&
    typeof error.request_id === "string"
  );
}

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null;
}

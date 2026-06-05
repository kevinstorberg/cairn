export interface RuntimeConfig {
  apiBaseUrl: string;
  appName: string;
  basePath: string;
  webSocketBaseUrl: string;
}

type RuntimeEnv = {
  DEV?: boolean;
  VITE_API_BASE_URL?: unknown;
  VITE_APP_NAME?: unknown;
  VITE_BASE_PATH?: unknown;
};

const DEFAULT_APP_NAME = "Cairn";
const DEFAULT_DEV_API_BASE_URL = "http://127.0.0.1:8000";
const DEFAULT_BASE_PATH = "/ui/";

export function resolveRuntimeConfig(
  env: RuntimeEnv = import.meta.env,
  location: Location | Pick<Location, "origin"> = window.location,
): RuntimeConfig {
  const apiBaseUrl = normalizeBaseUrl(readEnvString(env.VITE_API_BASE_URL) || defaultApiBaseUrl(env, location));
  const appName = readEnvString(env.VITE_APP_NAME);
  return {
    apiBaseUrl,
    appName: appName?.trim() || DEFAULT_APP_NAME,
    basePath: normalizeBasePath(readEnvString(env.VITE_BASE_PATH) || DEFAULT_BASE_PATH),
    webSocketBaseUrl: webSocketBaseUrlFor(apiBaseUrl),
  };
}

export function normalizeBaseUrl(value: string): string {
  const trimmed = value.trim();
  if (!trimmed) {
    throw new Error("VITE_API_BASE_URL must not be blank when provided");
  }

  let url: URL;
  try {
    url = new URL(trimmed);
  } catch (error) {
    throw new Error(`Invalid VITE_API_BASE_URL: ${value}`, fromError(error));
  }

  if (!["http:", "https:"].includes(url.protocol)) {
    throw new Error(`VITE_API_BASE_URL must use http or https: ${value}`);
  }

  return url.toString().replace(/\/$/, "");
}

export function normalizeBasePath(value: string): string {
  const trimmed = value.trim();
  if (!trimmed || !trimmed.startsWith("/")) {
    throw new Error(`VITE_BASE_PATH must start with '/': ${value}`);
  }
  return trimmed.endsWith("/") ? trimmed : `${trimmed}/`;
}

export function webSocketBaseUrlFor(apiBaseUrl: string): string {
  const url = new URL(apiBaseUrl);
  url.protocol = url.protocol === "https:" ? "wss:" : "ws:";
  return url.toString().replace(/\/$/, "");
}

function defaultApiBaseUrl(env: RuntimeEnv, location: Location | Pick<Location, "origin">): string {
  return env.DEV ? DEFAULT_DEV_API_BASE_URL : location.origin;
}

function readEnvString(value: unknown): string | undefined {
  return typeof value === "string" ? value : undefined;
}

function fromError(error: unknown): ErrorOptions {
  return error instanceof Error ? { cause: error } : {};
}

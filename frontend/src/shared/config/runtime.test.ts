import { describe, expect, it } from "vitest";

import { normalizeBasePath, normalizeBaseUrl, resolveRuntimeConfig, webSocketBaseUrlFor } from "./runtime";

describe("runtime config", () => {
  it("uses the local backend URL during development", () => {
    const config = resolveRuntimeConfig({ DEV: true }, { origin: "https://app.example" });

    expect(config.apiBaseUrl).toBe("http://127.0.0.1:8000");
    expect(config.basePath).toBe("/ui/");
    expect(config.webSocketBaseUrl).toBe("ws://127.0.0.1:8000");
  });

  it("uses same-origin API URLs outside development", () => {
    const config = resolveRuntimeConfig({}, { origin: "https://app.example" });

    expect(config.apiBaseUrl).toBe("https://app.example");
    expect(config.webSocketBaseUrl).toBe("wss://app.example");
  });

  it("normalizes explicit base URLs and paths", () => {
    expect(normalizeBaseUrl("https://api.example/")).toBe("https://api.example");
    expect(normalizeBasePath("/console")).toBe("/console/");
    expect(webSocketBaseUrlFor("https://api.example")).toBe("wss://api.example");
  });

  it("rejects malformed base URLs and paths", () => {
    expect(() => normalizeBaseUrl("not a url")).toThrow("Invalid VITE_API_BASE_URL");
    expect(() => normalizeBaseUrl("ftp://api.example")).toThrow("must use http or https");
    expect(() => normalizeBasePath("console")).toThrow("must start with '/'");
  });
});

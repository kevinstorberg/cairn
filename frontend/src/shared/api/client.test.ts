import { describe, expect, it, vi } from "vitest";

import { ApiClientError, createApiClient } from "./client";

function jsonResponse(body: unknown, init: ResponseInit = {}) {
  return new Response(JSON.stringify(body), {
    ...init,
    headers: {
      "content-type": "application/json",
      ...init.headers,
    },
  });
}

describe("api client", () => {
  it("returns parsed JSON and request IDs", async () => {
    const calls: Array<{ input: RequestInfo | URL; init?: RequestInit }> = [];
    const fetchImpl: typeof fetch = (input, init) => {
      calls.push({ input, init });
      return Promise.resolve(jsonResponse({ status: "ok" }, { headers: { "x-request-id": "request-1" } }));
    };
    const client = createApiClient({ baseUrl: "http://api.test", fetch: fetchImpl });

    const result = await client.get<{ status: string }>("/health");

    expect(result.data.status).toBe("ok");
    expect(result.requestId).toBe("request-1");
    expect(calls[0]?.input).toBe("http://api.test/health");
  });

  it("injects bearer tokens when provided", async () => {
    const calls: RequestInit[] = [];
    const fetchImpl: typeof fetch = (_input, init) => {
      calls.push(init || {});
      return Promise.resolve(jsonResponse({ ok: true }));
    };
    const client = createApiClient({
      baseUrl: "http://api.test",
      fetch: fetchImpl,
      getToken: () => "token-123",
    });

    await client.post("/items", { name: "example" });
    const headers = new Headers(calls[0]?.headers);

    expect(headers.get("authorization")).toBe("Bearer token-123");
    expect(headers.get("content-type")).toBe("application/json");
  });

  it("throws Cairn error envelopes with details", async () => {
    const fetchImpl = vi.fn(() =>
      Promise.resolve(
        jsonResponse(
        {
          error: {
            code: "validation_error",
            message: "Request validation failed",
            details: [{ field: "body.name", message: "Required", type: "missing" }],
            request_id: "request-422",
          },
        },
        { status: 422 },
      ),
      ),
    );
    const client = createApiClient({ baseUrl: "http://api.test", fetch: fetchImpl });

    await expect(client.get("/items")).rejects.toMatchObject({
      code: "validation_error",
      details: [{ field: "body.name", message: "Required", type: "missing" }],
      requestId: "request-422",
      status: 422,
    } satisfies Partial<ApiClientError>);
  });

  it("separates non-JSON failures from error envelopes", async () => {
    const fetchImpl = vi.fn(() => Promise.resolve(new Response("gateway unavailable", { status: 502 })));
    const client = createApiClient({ baseUrl: "http://api.test", fetch: fetchImpl });

    await expect(client.get("/health")).rejects.toMatchObject({
      code: "http_error",
      message: "gateway unavailable",
      status: 502,
    } satisfies Partial<ApiClientError>);
  });

  it("fails early for invalid paths", async () => {
    const fetchImpl: typeof fetch = () => Promise.reject(new Error("fetch should not be called"));
    const client = createApiClient({ baseUrl: "http://api.test", fetch: fetchImpl });

    await expect(client.get("health")).rejects.toThrow("API paths must start with '/'");
  });
});

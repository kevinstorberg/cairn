import { render, screen } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { describe, expect, it, vi } from "vitest";

import { App } from "./App";
import { ApiClientError, type ApiClient, type ApiResult } from "./shared/api";
import type { RuntimeConfig } from "./shared/config";

const runtimeConfig: RuntimeConfig = {
  apiBaseUrl: "http://api.test",
  appName: "Template Lab",
  basePath: "/ui/",
  webSocketBaseUrl: "ws://api.test",
};

function clientWithGet(result: ApiResult<unknown> | ApiClientError): ApiClient {
  const get: ApiClient["get"] = <T,>() => {
    if (result instanceof ApiClientError) {
      return Promise.reject(result);
    }
    return Promise.resolve(result as ApiResult<T>);
  };

  return {
    delete: vi.fn(),
    get,
    patch: vi.fn(),
    post: vi.fn(),
    request: vi.fn(),
  };
}

describe("app shell", () => {
  it("renders backend health success", async () => {
    const apiClient = clientWithGet({
        data: { app: "cairn", status: "ok", version: "0.1.0" },
        requestId: "request-1",
        response: new Response(),
      });

    render(
      <MemoryRouter>
        <App apiClient={apiClient} runtimeConfig={runtimeConfig} />
      </MemoryRouter>,
    );

    expect(await screen.findByText("ok")).toBeInTheDocument();
    expect(screen.getByText("request-1")).toBeInTheDocument();
    expect(screen.getByText("Template Lab")).toBeInTheDocument();
  });

  it("renders Cairn error envelope failures", async () => {
    const apiClient = clientWithGet(
      new ApiClientError("Request validation failed", {
        code: "validation_error",
        details: [{ field: "body.name", message: "Required", type: "missing" }],
        requestId: "request-422",
        status: 422,
      }),
    );

    render(
      <MemoryRouter>
        <App apiClient={apiClient} runtimeConfig={runtimeConfig} />
      </MemoryRouter>,
    );

    expect(await screen.findByText("validation_error")).toBeInTheDocument();
    expect(screen.getByText("Request validation failed")).toBeInTheDocument();
    expect(screen.getByText("Request ID: request-422")).toBeInTheDocument();
  });
});

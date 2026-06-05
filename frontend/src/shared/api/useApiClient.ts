import { useContext } from "react";

import { ApiClientContext } from "./clientContext";
import type { ApiClient } from "./client";

export function useApiClient(): ApiClient {
  const client = useContext(ApiClientContext);
  if (!client) {
    throw new Error("useApiClient must be used inside ApiClientProvider");
  }
  return client;
}

import type { ReactNode } from "react";

import type { ApiClient } from "./client";
import { ApiClientContext } from "./clientContext";

interface ApiClientProviderProps {
  children: ReactNode;
  client: ApiClient;
}

export function ApiClientProvider({ children, client }: ApiClientProviderProps) {
  return <ApiClientContext.Provider value={client}>{children}</ApiClientContext.Provider>;
}

import { createContext } from "react";

import type { ApiClient } from "./client";

export const ApiClientContext = createContext<ApiClient | null>(null);

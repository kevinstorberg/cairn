import { Activity, KeyRound } from "lucide-react";
import { lazy, Suspense, useMemo, useState } from "react";
import { NavLink, Route, Routes } from "react-router-dom";

import { features } from "./features/registry";
import { ApiClientProvider, createApiClient, type ApiClient } from "./shared/api";
import { resolveRuntimeConfig, type RuntimeConfig } from "./shared/config";
import { Button } from "./shared/ui";

const Dashboard = lazy(() => import("./Dashboard").then((module) => ({ default: module.Dashboard })));

interface AppProps {
  apiClient?: ApiClient;
  runtimeConfig?: RuntimeConfig;
}

export function App({ apiClient, runtimeConfig = resolveRuntimeConfig() }: AppProps) {
  const [token, setToken] = useState(() => localStorage.getItem("cairn.authToken") || "");
  const client = useMemo(
    () =>
      apiClient ||
      createApiClient({
        baseUrl: runtimeConfig.apiBaseUrl,
        getToken: () => token || null,
      }),
    [apiClient, runtimeConfig.apiBaseUrl, token],
  );

  function saveToken(value: string) {
    setToken(value);
    if (value) {
      localStorage.setItem("cairn.authToken", value);
    } else {
      localStorage.removeItem("cairn.authToken");
    }
  }

  return (
    <div className="app-shell">
      <aside className="sidebar">
        <div className="brand">
          <Activity aria-hidden="true" size={22} />
          <span>{runtimeConfig.appName}</span>
        </div>
        <nav className="nav-list" aria-label="Application">
          <NavLink className="nav-link" to="/">
            Dashboard
          </NavLink>
          {features.map((feature) => (
            <NavLink className="nav-link" key={feature.name} to={feature.path}>
              {feature.label}
            </NavLink>
          ))}
        </nav>
      </aside>
      <main className="main-surface">
        <header className="topbar">
          <label className="token-field">
            <span>Bearer token</span>
            <input
              onChange={(event) => saveToken(event.target.value.trim())}
              placeholder="paste token"
              type="password"
              value={token}
            />
          </label>
          <Button icon={<KeyRound size={16} />} onClick={() => saveToken("")} variant="ghost">
            Clear
          </Button>
        </header>
        <ApiClientProvider client={client}>
          <Suspense fallback={<div className="loading-state">Loading...</div>}>
            <Routes>
              <Route element={<Dashboard apiClient={client} />} path="/" />
              {features.map((feature) => (
                <Route element={<feature.Component />} key={feature.name} path={feature.path} />
              ))}
            </Routes>
          </Suspense>
        </ApiClientProvider>
      </main>
    </div>
  );
}

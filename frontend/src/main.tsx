import { StrictMode } from "react";
import { createRoot } from "react-dom/client";
import { BrowserRouter } from "react-router-dom";

import { App } from "./App";
import { resolveRuntimeConfig } from "./shared/config";
import "./styles/main.css";

const runtimeConfig = resolveRuntimeConfig();
const basename = runtimeConfig.basePath === "/" ? undefined : runtimeConfig.basePath.replace(/\/$/, "");

createRoot(document.getElementById("root") as HTMLElement).render(
  <StrictMode>
    <BrowserRouter basename={basename}>
      <App runtimeConfig={runtimeConfig} />
    </BrowserRouter>
  </StrictMode>,
);

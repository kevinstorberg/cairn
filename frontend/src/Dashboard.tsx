import { AlertCircle, CheckCircle2, RefreshCw } from "lucide-react";
import { useCallback, useEffect, useState } from "react";

import { ApiClientError, type ApiClient, type ApiResult } from "./shared/api";
import { Button, Panel, StatusBadge } from "./shared/ui";

interface HealthResponse {
  status: string;
  app: string;
  version: string;
}

type HealthState =
  | { status: "loading" }
  | { status: "ready"; result: ApiResult<HealthResponse> }
  | { status: "error"; error: ApiClientError | Error };

interface DashboardProps {
  apiClient: ApiClient;
}

export function Dashboard({ apiClient }: DashboardProps) {
  const [health, setHealth] = useState<HealthState>({ status: "loading" });

  const loadHealth = useCallback(async () => {
    setHealth({ status: "loading" });
    try {
      setHealth({ status: "ready", result: await apiClient.get<HealthResponse>("/health") });
    } catch (error) {
      setHealth({ status: "error", error: error instanceof Error ? error : new Error("Unknown error") });
    }
  }, [apiClient]);

  useEffect(() => {
    void loadHealth();
  }, [loadHealth]);

  return (
    <div className="dashboard">
      <Panel
        actions={
          <Button icon={<RefreshCw size={16} />} onClick={() => void loadHealth()} variant="ghost">
            Refresh
          </Button>
        }
        title="Backend health"
      >
        <HealthContent health={health} />
      </Panel>
    </div>
  );
}

function HealthContent({ health }: { health: HealthState }) {
  if (health.status === "loading") {
    return <StatusBadge tone="neutral">Checking</StatusBadge>;
  }

  if (health.status === "ready") {
    return (
      <div className="health-result">
        <CheckCircle2 aria-hidden="true" className="health-result__icon health-result__icon--ok" size={20} />
        <div>
          <StatusBadge tone="success">{health.result.data.status}</StatusBadge>
          <dl className="meta-list">
            <div>
              <dt>App</dt>
              <dd>{health.result.data.app}</dd>
            </div>
            <div>
              <dt>Version</dt>
              <dd>{health.result.data.version}</dd>
            </div>
            {health.result.requestId ? (
              <div>
                <dt>Request ID</dt>
                <dd>{health.result.requestId}</dd>
              </div>
            ) : null}
          </dl>
        </div>
      </div>
    );
  }

  if (health.error instanceof ApiClientError) {
    return (
      <div className="health-result">
        <AlertCircle aria-hidden="true" className="health-result__icon health-result__icon--error" size={20} />
        <div>
          <StatusBadge tone="danger">{health.error.code}</StatusBadge>
          <p className="error-message">{health.error.message}</p>
          {health.error.requestId ? <p className="request-id">Request ID: {health.error.requestId}</p> : null}
        </div>
      </div>
    );
  }

  return (
    <div className="health-result">
      <AlertCircle aria-hidden="true" className="health-result__icon health-result__icon--error" size={20} />
      <p className="error-message">{health.error.message}</p>
    </div>
  );
}

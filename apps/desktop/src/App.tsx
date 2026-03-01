import { useEffect, useState } from "react";
import { Button } from "@/components/ui/button";
import { LoaderCircle } from "lucide-react";

type HealthResponse = {
  status: string;
  service: string;
  version: string;
  time_utc: string;
  readiness: {
    observer_ready: boolean;
    db_ready: boolean;
    embedder_ready: boolean;
  };
};

const SIDECAR_URL = "http://127.0.0.1:8765/health";

export default function App() {
  const [health, setHealth] = useState<HealthResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  const fetchHealth = async () => {
    setLoading(true);
    setError(null);

    try {
      const response = await fetch(SIDECAR_URL, { method: "GET" });
      if (!response.ok) {
        throw new Error(`HTTP ${response.status}`);
      }
      const body = (await response.json()) as HealthResponse;
      setHealth(body);
    } catch (err) {
      setHealth(null);
      const raw = err instanceof Error ? err.message : "Unknown error";
      setError(
        `${raw}. Make sure sidecar is running on ${SIDECAR_URL} and allows local dev CORS.`
      );
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    void fetchHealth();
  }, []);

  return (
    <main className="mx-auto max-w-2xl p-5">
      <header className="mb-4 flex items-center justify-between border-b pb-3">
        <h1>Remnis</h1>
        <Button
          onClick={() => void fetchHealth()}
          disabled={loading}
          size="sm"
          className="w-[78px]"
        >
          {loading ? <LoaderCircle className="h-3.5 w-3.5 animate-spin" /> : "Refresh"}
        </Button>
      </header>

      <section className="space-y-2">
        {error && <p className="text-sm font-medium">Sidecar unavailable: {error}</p>}
        {!error && !health && <p className="text-sm">No data yet.</p>}
        {health && (
          <dl className="grid grid-cols-[140px_1fr] gap-x-3 gap-y-2 text-sm">
            <dt className="uppercase tracking-wide text-muted-foreground">Status</dt>
            <dd>{health.status}</dd>
            <dt className="uppercase tracking-wide text-muted-foreground">Service</dt>
            <dd>{health.service}</dd>
            <dt className="uppercase tracking-wide text-muted-foreground">Version</dt>
            <dd>{health.version}</dd>
            <dt className="uppercase tracking-wide text-muted-foreground">Time (UTC)</dt>
            <dd>{health.time_utc}</dd>
            <dt className="uppercase tracking-wide text-muted-foreground">Observer</dt>
            <dd>{health.readiness.observer_ready ? "ready" : "not ready"}</dd>
            <dt className="uppercase tracking-wide text-muted-foreground">Database</dt>
            <dd>{health.readiness.db_ready ? "ready" : "not ready"}</dd>
            <dt className="uppercase tracking-wide text-muted-foreground">Embedder</dt>
            <dd>{health.readiness.embedder_ready ? "ready" : "not ready"}</dd>
          </dl>
        )}
      </section>
    </main>
  );
}

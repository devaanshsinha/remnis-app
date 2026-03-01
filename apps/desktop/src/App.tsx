import { useEffect, useState } from "react";

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
    <main>
      <h1>Remnis</h1>
      <p>Health check</p>

      <button onClick={() => void fetchHealth()} disabled={loading}>
        {loading ? "Checking..." : "Check Sidecar /health"}
      </button>

      {error && <p className="error">Sidecar unavailable: {error}</p>}

      {health && (
        <>
          <p><strong>Status:</strong> {health.status}</p>
          <p><strong>Service:</strong> {health.service}</p>
          <p><strong>Version:</strong> {health.version}</p>
          <p><strong>Time (UTC):</strong> {health.time_utc}</p>
          <p>
            <strong>Readiness:</strong>
            {` observer=${String(health.readiness.observer_ready)}, db=${String(
              health.readiness.db_ready
            )}, embedder=${String(health.readiness.embedder_ready)}`}
          </p>
        </>
      )}
    </main>
  );
}

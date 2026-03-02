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

type EventItem = {
  id: string;
  timestamp_utc: string;
  app_name: string;
  window_title: string;
  file_path: string | null;
  context_text: string;
  source: "observer.active_window" | "observer.accessibility_text";
};

type EventsResponse = {
  limit: number;
  offset: number;
  total_estimate: number;
  results: EventItem[];
};

const SIDECAR_BASE_URL = "http://127.0.0.1:8765";
const SIDECAR_HEALTH_URL = `${SIDECAR_BASE_URL}/health`;
const SIDECAR_EVENTS_URL = `${SIDECAR_BASE_URL}/events?limit=25`;

export default function App() {
  const [health, setHealth] = useState<HealthResponse | null>(null);
  const [events, setEvents] = useState<EventItem[]>([]);
  const [eventTotal, setEventTotal] = useState(0);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  const fetchData = async () => {
    setLoading(true);
    setError(null);

    try {
      const [healthResponse, eventsResponse] = await Promise.all([
        fetch(SIDECAR_HEALTH_URL, { method: "GET" }),
        fetch(SIDECAR_EVENTS_URL, { method: "GET" }),
      ]);

      if (!healthResponse.ok) {
        throw new Error(`Health HTTP ${healthResponse.status}`);
      }
      if (!eventsResponse.ok) {
        throw new Error(`Events HTTP ${eventsResponse.status}`);
      }

      const healthBody = (await healthResponse.json()) as HealthResponse;
      const eventsBody = (await eventsResponse.json()) as EventsResponse;
      setHealth(healthBody);
      setEvents(eventsBody.results);
      setEventTotal(eventsBody.total_estimate);
    } catch (err) {
      setHealth(null);
      setEvents([]);
      setEventTotal(0);
      const raw = err instanceof Error ? err.message : "Unknown error";
      setError(
        `${raw}. Make sure sidecar is running on ${SIDECAR_BASE_URL} and allows local dev CORS.`
      );
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    void fetchData();
  }, []);

  return (
    <main className="mx-auto max-w-2xl p-5">
      <header className="mb-4 flex items-center justify-between border-b pb-3">
        <h1>Remnis</h1>
        <Button
          onClick={() => void fetchData()}
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

      <section className="mt-6 space-y-3">
        <div className="flex items-center justify-between border-b pb-2">
          <h2 className="text-sm uppercase tracking-wide text-muted-foreground">Recent Events</h2>
          <p className="text-xs text-muted-foreground">
            showing {events.length} of {eventTotal}
          </p>
        </div>
        {events.length === 0 && !error && <p className="text-sm">No events yet.</p>}
        {events.map((event) => (
          <article key={event.id} className="space-y-1 border-b pb-3">
            <p className="text-sm font-medium">{event.window_title}</p>
            <p className="text-xs text-muted-foreground">
              {event.app_name} · {event.source}
            </p>
            {event.file_path && <p className="text-xs break-all">{event.file_path}</p>}
            <p className="text-xs text-muted-foreground">{event.timestamp_utc}</p>
          </article>
        ))}
      </section>
    </main>
  );
}

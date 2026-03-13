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

type IndexStatusResponse = {
  embedder_ready: boolean;
  embedder_model_name: string;
  embedder_last_error: string | null;
  vector_store_ready: boolean;
  vector_store_last_error: string | null;
  indexed_event_count: number;
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

type SearchResult = {
  id: string;
  timestamp_utc: string;
  app_name: string;
  window_title: string;
  context_text: string;
  score: number;
  context_hash: string;
  source_version: string;
};

type SearchResponse = {
  query: string;
  mode: string;
  k: number;
  offset: number;
  total_estimate: number;
  results: SearchResult[];
};

const SIDECAR_BASE_URL = "http://127.0.0.1:8765";
const SIDECAR_HEALTH_URL = `${SIDECAR_BASE_URL}/health`;
const SIDECAR_INDEX_STATUS_URL = `${SIDECAR_BASE_URL}/index/status`;
const DEFAULT_LIMIT = 25;
const DEFAULT_SEARCH_K = 20;

const sourceOptions = [
  { label: "All", value: "" },
  { label: "Observer Window", value: "observer.active_window" },
  { label: "Browser Adapter", value: "observer.accessibility_text" },
] as const;

function toUtcIso(localDateTime: string): string | null {
  if (!localDateTime) {
    return null;
  }
  const parsed = new Date(localDateTime);
  if (Number.isNaN(parsed.getTime())) {
    return null;
  }
  return parsed.toISOString();
}

export default function App() {
  const [health, setHealth] = useState<HealthResponse | null>(null);
  const [indexStatus, setIndexStatus] = useState<IndexStatusResponse | null>(null);
  const [events, setEvents] = useState<EventItem[]>([]);
  const [eventTotal, setEventTotal] = useState(0);
  const [query, setQuery] = useState("");
  const [searchMode, setSearchMode] = useState<string | null>(null);
  const [searchResults, setSearchResults] = useState<SearchResult[]>([]);
  const [searchTotal, setSearchTotal] = useState(0);
  const [appFilter, setAppFilter] = useState("");
  const [sourceFilter, setSourceFilter] = useState<(typeof sourceOptions)[number]["value"]>("");
  const [fromTs, setFromTs] = useState("");
  const [toTs, setToTs] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  const buildEventsUrl = (overrides?: {
    appFilter?: string;
    sourceFilter?: (typeof sourceOptions)[number]["value"];
    fromTs?: string;
    toTs?: string;
  }) => {
    const effectiveAppFilter = overrides?.appFilter ?? appFilter;
    const effectiveSourceFilter = overrides?.sourceFilter ?? sourceFilter;
    const effectiveFromTs = overrides?.fromTs ?? fromTs;
    const effectiveToTs = overrides?.toTs ?? toTs;
    const params = new URLSearchParams();
    params.set("limit", String(DEFAULT_LIMIT));
    if (effectiveSourceFilter) {
      params.set("source", effectiveSourceFilter);
    }
    if (effectiveAppFilter.trim()) {
      params.set("app_name", effectiveAppFilter.trim());
    }
    const fromUtc = toUtcIso(effectiveFromTs);
    if (fromUtc) {
      params.set("from_ts", fromUtc);
    }
    const toUtc = toUtcIso(effectiveToTs);
    if (toUtc) {
      params.set("to_ts", toUtc);
    }
    return `${SIDECAR_BASE_URL}/events?${params.toString()}`;
  };

  const buildSearchUrl = (
    currentQuery: string,
    overrides?: {
      appFilter?: string;
      sourceFilter?: (typeof sourceOptions)[number]["value"];
      fromTs?: string;
      toTs?: string;
    }
  ) => {
    const trimmedQuery = currentQuery.trim();
    if (!trimmedQuery) {
      return null;
    }
    const effectiveAppFilter = overrides?.appFilter ?? appFilter;
    const effectiveSourceFilter = overrides?.sourceFilter ?? sourceFilter;
    const effectiveFromTs = overrides?.fromTs ?? fromTs;
    const effectiveToTs = overrides?.toTs ?? toTs;
    const params = new URLSearchParams();
    params.set("q", trimmedQuery);
    params.set("k", String(DEFAULT_SEARCH_K));
    if (effectiveSourceFilter) {
      params.set("source", effectiveSourceFilter);
    }
    if (effectiveAppFilter.trim()) {
      params.set("app_name", effectiveAppFilter.trim());
    }
    const fromUtc = toUtcIso(effectiveFromTs);
    if (fromUtc) {
      params.set("from_ts", fromUtc);
    }
    const toUtc = toUtcIso(effectiveToTs);
    if (toUtc) {
      params.set("to_ts", toUtc);
    }
    return `${SIDECAR_BASE_URL}/search?${params.toString()}`;
  };

  const fetchData = async (overrides?: {
    appFilter?: string;
    sourceFilter?: (typeof sourceOptions)[number]["value"];
    fromTs?: string;
    toTs?: string;
  }) => {
    setLoading(true);
    setError(null);

    try {
      const eventsUrl = buildEventsUrl(overrides);
      const searchUrl = buildSearchUrl(query, overrides);
      const requests: Promise<Response>[] = [
        fetch(SIDECAR_HEALTH_URL, { method: "GET" }),
        fetch(SIDECAR_INDEX_STATUS_URL, { method: "GET" }),
        fetch(eventsUrl, { method: "GET" }),
      ];
      if (searchUrl) {
        requests.push(fetch(searchUrl, { method: "GET" }));
      }
      const responses = await Promise.all(requests);
      const healthResponse = responses[0];
      const indexStatusResponse = responses[1];
      const eventsResponse = responses[2];
      const searchResponse = responses.length > 3 ? responses[3] : null;

      if (!healthResponse.ok) {
        throw new Error(`Health HTTP ${healthResponse.status}`);
      }
      if (!indexStatusResponse.ok) {
        throw new Error(`Index status HTTP ${indexStatusResponse.status}`);
      }
      if (!eventsResponse.ok) {
        throw new Error(`Events HTTP ${eventsResponse.status}`);
      }
      if (searchResponse && !searchResponse.ok) {
        throw new Error(`Search HTTP ${searchResponse.status}`);
      }

      const healthBody = (await healthResponse.json()) as HealthResponse;
      const indexStatusBody = (await indexStatusResponse.json()) as IndexStatusResponse;
      const eventsBody = (await eventsResponse.json()) as EventsResponse;
      setHealth(healthBody);
      setIndexStatus(indexStatusBody);
      setEvents(eventsBody.results);
      setEventTotal(eventsBody.total_estimate);
      if (searchResponse) {
        const searchBody = (await searchResponse.json()) as SearchResponse;
        setSearchMode(searchBody.mode);
        setSearchResults(searchBody.results);
        setSearchTotal(searchBody.total_estimate);
      } else {
        setSearchMode(null);
        setSearchResults([]);
        setSearchTotal(0);
      }
    } catch (err) {
      setHealth(null);
      setIndexStatus(null);
      setEvents([]);
      setEventTotal(0);
      setSearchMode(null);
      setSearchResults([]);
      setSearchTotal(0);
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
        {indexStatus && (
          <dl className="grid grid-cols-[140px_1fr] gap-x-3 gap-y-2 border-t pt-3 text-sm">
            <dt className="uppercase tracking-wide text-muted-foreground">Index Count</dt>
            <dd>{indexStatus.indexed_event_count}</dd>
            <dt className="uppercase tracking-wide text-muted-foreground">Embedder Model</dt>
            <dd>{indexStatus.embedder_model_name}</dd>
            <dt className="uppercase tracking-wide text-muted-foreground">Vector Store</dt>
            <dd>{indexStatus.vector_store_ready ? "ready" : "not ready"}</dd>
            <dt className="uppercase tracking-wide text-muted-foreground">Embedder Error</dt>
            <dd>{indexStatus.embedder_last_error ?? "none"}</dd>
            <dt className="uppercase tracking-wide text-muted-foreground">Vector Error</dt>
            <dd>{indexStatus.vector_store_last_error ?? "none"}</dd>
          </dl>
        )}
      </section>

      <section className="mt-6 space-y-3">
        <form
          className="flex gap-2 border-b pb-3"
          onSubmit={(event) => {
            event.preventDefault();
            void fetchData();
          }}
        >
          <input
            className="h-9 flex-1 rounded-md border px-2"
            placeholder="Search your context"
            value={query}
            onChange={(event) => setQuery(event.target.value)}
          />
          <Button type="submit" size="sm" disabled={loading}>
            Search
          </Button>
        </form>

        <form
          className="grid gap-2 border-b pb-3 text-sm sm:grid-cols-2"
          onSubmit={(event) => {
            event.preventDefault();
            void fetchData();
          }}
        >
          <input
            className="h-9 rounded-md border px-2"
            placeholder="Filter app name (e.g. Google Chrome)"
            value={appFilter}
            onChange={(event) => setAppFilter(event.target.value)}
          />
          <select
            className="h-9 rounded-md border px-2"
            value={sourceFilter}
            onChange={(event) =>
              setSourceFilter(event.target.value as (typeof sourceOptions)[number]["value"])
            }
          >
            {sourceOptions.map((option) => (
              <option key={option.value || "all"} value={option.value}>
                {option.label}
              </option>
            ))}
          </select>
          <input
            className="h-9 rounded-md border px-2"
            type="datetime-local"
            value={fromTs}
            onChange={(event) => setFromTs(event.target.value)}
          />
          <input
            className="h-9 rounded-md border px-2"
            type="datetime-local"
            value={toTs}
            onChange={(event) => setToTs(event.target.value)}
          />
          <Button type="submit" size="sm" disabled={loading}>
            Apply Filters
          </Button>
          <Button
            type="button"
            size="sm"
            variant="outline"
            disabled={loading}
            onClick={() => {
              setAppFilter("");
              setSourceFilter("");
              setFromTs("");
              setToTs("");
              void fetchData({
                appFilter: "",
                sourceFilter: "",
                fromTs: "",
                toTs: "",
              });
            }}
          >
            Clear Filters
          </Button>
        </form>

        {query.trim() && (
          <section className="space-y-3 border-b pb-3">
            <div className="flex items-center justify-between">
              <h2 className="text-sm uppercase tracking-wide text-muted-foreground">
                Search Results
              </h2>
              <p className="text-xs text-muted-foreground">
                {searchMode ?? "keyword_fallback"} · showing {searchResults.length} of {searchTotal}
              </p>
            </div>
            {searchResults.length === 0 && !error && <p className="text-sm">No matching events.</p>}
            {searchResults.map((result) => (
              <article key={result.id} className="space-y-1 border-b pb-3">
                <p className="text-sm font-medium">{result.window_title}</p>
                <p className="text-xs text-muted-foreground">
                  {result.app_name} · score {result.score.toFixed(2)}
                </p>
                <p className="text-xs">{result.context_text}</p>
                <p className="text-xs text-muted-foreground">{result.timestamp_utc}</p>
              </article>
            ))}
          </section>
        )}

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

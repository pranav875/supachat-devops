const API_BASE = process.env.NEXT_PUBLIC_API_URL ?? "/api";

export interface QueryRequest {
  query: string;
  session_id?: string;
}

export interface QueryResponse {
  summary: string;
  sql: string;
  columns: string[];
  rows: unknown[][];
  chart_type: "line" | "bar" | "pie" | "none";
  chart_data: Record<string, unknown>[];
  query_id: string;
  timestamp: string;
}

export interface HistoryRecord {
  query_id: string;
  session_id: string;
  nl_query: string;
  sql: string;
  summary: string;
  columns: string[];
  rows: unknown[][];
  chart_type: "line" | "bar" | "pie" | "none";
  chart_data: Record<string, unknown>[];
  timestamp: string;
  error: string | null;
}

export async function postQuery(request: QueryRequest): Promise<QueryResponse> {
  const res = await fetch(`${API_BASE}/query`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(request),
  });

  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(err.detail ?? "Query failed");
  }

  return res.json();
}

export async function getHistory(limit = 50): Promise<HistoryRecord[]> {
  const res = await fetch(`${API_BASE}/history?limit=${limit}`);
  if (!res.ok) throw new Error("Failed to fetch history");
  return res.json();
}

export async function deleteHistoryItem(queryId: string): Promise<void> {
  const res = await fetch(`${API_BASE}/history/${queryId}`, { method: "DELETE" });
  if (!res.ok) throw new Error("Failed to delete history item");
}

export async function clearHistory(): Promise<void> {
  const res = await fetch(`${API_BASE}/history`, { method: "DELETE" });
  if (!res.ok) throw new Error("Failed to clear history");
}

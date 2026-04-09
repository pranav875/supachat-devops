"use client";

import { useEffect, useState, useCallback } from "react";
import { getHistory, deleteHistoryItem, clearHistory, HistoryRecord } from "@/lib/api";

interface HistorySidebarProps {
  onSelect: (record: HistoryRecord) => void;
}

export default function HistorySidebar({ onSelect }: HistorySidebarProps) {
  const [history, setHistory] = useState<HistoryRecord[]>([]);
  const [loading, setLoading] = useState(true);

  const fetchHistory = useCallback(() => {
    getHistory()
      .then(setHistory)
      .catch(() => setHistory([]))
      .finally(() => setLoading(false));
  }, []);

  useEffect(() => {
    fetchHistory();
  }, [fetchHistory]);

  const handleDelete = async (e: React.MouseEvent, queryId: string) => {
    e.stopPropagation();
    await deleteHistoryItem(queryId).catch(() => { });
    setHistory((prev) => prev.filter((r) => r.query_id !== queryId));
  };

  const handleClearAll = async () => {
    await clearHistory().catch(() => { });
    setHistory([]);
  };

  return (
    <aside className="flex w-64 flex-col border-r border-zinc-200 bg-zinc-50 dark:border-zinc-700 dark:bg-zinc-900">
      <div className="flex items-center justify-between border-b border-zinc-200 px-4 py-3 dark:border-zinc-700">
        <h2 className="text-xs font-semibold uppercase tracking-wider text-zinc-500 dark:text-zinc-400">
          History
        </h2>
        {history.length > 0 && (
          <button
            onClick={handleClearAll}
            className="text-xs text-red-400 hover:text-red-600 dark:hover:text-red-300"
            title="Clear all history"
          >
            Clear all
          </button>
        )}
      </div>

      <div className="flex-1 overflow-y-auto">
        {loading && (
          <p className="px-4 py-3 text-xs text-zinc-400">Loading...</p>
        )}

        {!loading && history.length === 0 && (
          <p className="px-4 py-3 text-xs text-zinc-400">No history yet</p>
        )}

        {history.map((record) => (
          <div key={record.query_id} className="group relative">
            <button
              onClick={() => onSelect(record)}
              className="w-full px-4 py-3 text-left text-sm text-zinc-700 transition-colors hover:bg-zinc-100 dark:text-zinc-300 dark:hover:bg-zinc-800"
            >
              <p className="truncate pr-6 font-medium">{record.nl_query}</p>
              <p className="mt-0.5 text-xs text-zinc-400">
                {new Date(record.timestamp).toLocaleString()}
              </p>
            </button>
            <button
              onClick={(e) => handleDelete(e, record.query_id)}
              className="absolute right-2 top-3 text-zinc-400 hover:text-red-500"
              title="Delete"
              aria-label="Delete history item"
            >
              &#x2715;
            </button>
          </div>
        ))}
      </div>
    </aside>
  );
}

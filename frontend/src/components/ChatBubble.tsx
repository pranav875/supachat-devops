"use client";

import DataTable from "./DataTable";
import ChartPanel from "./ChartPanel";

interface ChatBubbleProps {
  role: "user" | "assistant";
  content: string;
  columns?: string[];
  rows?: unknown[][];
  chartType?: "line" | "bar" | "pie" | "none";
  chartData?: Record<string, unknown>[];
  isError?: boolean;
}

export default function ChatBubble({
  role,
  content,
  columns,
  rows,
  chartType,
  chartData,
  isError = false,
}: ChatBubbleProps) {
  const isUser = role === "user";

  return (
    <div className={`flex w-full ${isUser ? "justify-end" : "justify-start"}`}>
      <div
        className={`max-w-[85%] rounded-2xl px-4 py-3 text-sm ${
          isUser
            ? "bg-blue-600 text-white"
            : isError
            ? "border border-red-200 bg-red-50 text-red-700 dark:border-red-800 dark:bg-red-950 dark:text-red-300"
            : "bg-zinc-100 text-zinc-900 dark:bg-zinc-800 dark:text-zinc-100"
        }`}
      >
        <p className="whitespace-pre-wrap leading-relaxed">{content}</p>

        {!isUser && !isError && rows && rows.length > 0 && columns && (
          <DataTable columns={columns} rows={rows} />
        )}

        {!isUser && !isError && chartType && chartData && (
          <ChartPanel chartType={chartType} chartData={chartData} />
        )}
      </div>
    </div>
  );
}

"use client";

import { useEffect, useRef } from "react";
import ChatBubble from "./ChatBubble";

export interface Message {
  id: string;
  role: "user" | "assistant";
  content: string;
  columns?: string[];
  rows?: unknown[][];
  chartType?: "line" | "bar" | "pie" | "none";
  chartData?: Record<string, unknown>[];
  isError?: boolean;
}

interface ChatWindowProps {
  messages: Message[];
}

export default function ChatWindow({ messages }: ChatWindowProps) {
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  return (
    <div className="flex flex-1 flex-col gap-4 overflow-y-auto p-4">
      {messages.length === 0 && (
        <div className="flex flex-1 items-center justify-center">
          <p className="text-sm text-zinc-400">
            Ask a question about your blog analytics to get started.
          </p>
        </div>
      )}

      {messages.map((msg) => (
        <ChatBubble
          key={msg.id}
          role={msg.role}
          content={msg.content}
          columns={msg.columns}
          rows={msg.rows}
          chartType={msg.chartType}
          chartData={msg.chartData}
          isError={msg.isError}
        />
      ))}

      <div ref={bottomRef} />
    </div>
  );
}

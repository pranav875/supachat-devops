"use client";

import { useState, FormEvent } from "react";

interface ChatInputProps {
  onSubmit: (query: string) => void;
  isLoading?: boolean;
}

export default function ChatInput({ onSubmit, isLoading = false }: ChatInputProps) {
  const [value, setValue] = useState("");

  function handleSubmit(e: FormEvent) {
    e.preventDefault();
    const trimmed = value.trim();
    if (!trimmed || isLoading) return;
    onSubmit(trimmed);
    setValue("");
  }

  return (
    <form
      onSubmit={handleSubmit}
      className="flex items-center gap-2 border-t border-zinc-200 bg-white p-4 dark:border-zinc-700 dark:bg-zinc-900"
    >
      <input
        type="text"
        value={value}
        onChange={(e) => setValue(e.target.value)}
        disabled={isLoading}
        placeholder="Ask a question about your blog analytics..."
        className="flex-1 rounded-lg border border-zinc-300 bg-zinc-50 px-4 py-2 text-sm text-zinc-900 placeholder-zinc-400 focus:outline-none focus:ring-2 focus:ring-blue-500 disabled:opacity-50 dark:border-zinc-600 dark:bg-zinc-800 dark:text-zinc-100"
        aria-label="Query input"
      />
      <button
        type="submit"
        disabled={isLoading || !value.trim()}
        className="flex h-9 w-9 items-center justify-center rounded-lg bg-blue-600 text-white transition-colors hover:bg-blue-700 disabled:opacity-50"
        aria-label="Submit query"
      >
        {isLoading ? (
          <svg
            className="h-4 w-4 animate-spin"
            xmlns="http://www.w3.org/2000/svg"
            fill="none"
            viewBox="0 0 24 24"
            aria-hidden="true"
          >
            <circle
              className="opacity-25"
              cx="12"
              cy="12"
              r="10"
              stroke="currentColor"
              strokeWidth="4"
            />
            <path
              className="opacity-75"
              fill="currentColor"
              d="M4 12a8 8 0 018-8v4a4 4 0 00-4 4H4z"
            />
          </svg>
        ) : (
          <svg
            xmlns="http://www.w3.org/2000/svg"
            viewBox="0 0 24 24"
            fill="currentColor"
            className="h-4 w-4"
            aria-hidden="true"
          >
            <path d="M3.478 2.405a.75.75 0 00-.926.94l2.432 7.905H13.5a.75.75 0 010 1.5H4.984l-2.432 7.905a.75.75 0 00.926.94 60.519 60.519 0 0018.445-8.986.75.75 0 000-1.218A60.517 60.517 0 003.478 2.405z" />
          </svg>
        )}
      </button>
    </form>
  );
}

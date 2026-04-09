"use client";

import { useReducer, useCallback } from "react";
import { v4 as uuidv4 } from "uuid";
import ChatWindow, { Message } from "@/components/ChatWindow";
import ChatInput from "@/components/ChatInput";
import HistorySidebar from "@/components/HistorySidebar";
import { postQuery, HistoryRecord } from "@/lib/api";

interface ChatState {
  messages: Message[];
  isLoading: boolean;
}

type ChatAction =
  | { type: "ADD_MESSAGE"; message: Message }
  | { type: "SET_LOADING"; loading: boolean };

function chatReducer(state: ChatState, action: ChatAction): ChatState {
  switch (action.type) {
    case "ADD_MESSAGE":
      return { ...state, messages: [...state.messages, action.message] };
    case "SET_LOADING":
      return { ...state, isLoading: action.loading };
    default:
      return state;
  }
}

export default function Home() {
  const [state, dispatch] = useReducer(chatReducer, {
    messages: [],
    isLoading: false,
  });

  const handleSubmit = useCallback(async (query: string) => {
    dispatch({
      type: "ADD_MESSAGE",
      message: { id: uuidv4(), role: "user", content: query },
    });
    dispatch({ type: "SET_LOADING", loading: true });

    try {
      const result = await postQuery({ query });
      dispatch({
        type: "ADD_MESSAGE",
        message: {
          id: uuidv4(),
          role: "assistant",
          content: result.summary,
          columns: result.columns,
          rows: result.rows,
          chartType: result.chart_type,
          chartData: result.chart_data,
        },
      });
    } catch (err) {
      dispatch({
        type: "ADD_MESSAGE",
        message: {
          id: uuidv4(),
          role: "assistant",
          content: err instanceof Error ? err.message : "Something went wrong.",
          isError: true,
        },
      });
    } finally {
      dispatch({ type: "SET_LOADING", loading: false });
    }
  }, []);

  const handleHistorySelect = useCallback((record: HistoryRecord) => {
    dispatch({
      type: "ADD_MESSAGE",
      message: { id: uuidv4(), role: "user", content: record.nl_query },
    });
    dispatch({
      type: "ADD_MESSAGE",
      message: {
        id: uuidv4(),
        role: "assistant",
        content: record.summary,
        columns: record.columns,
        rows: record.rows,
        chartType: record.chart_type,
        chartData: record.chart_data,
        isError: !!record.error,
      },
    });
  }, []);

  return (
    <div className="flex h-screen overflow-hidden bg-white dark:bg-zinc-950">
      <HistorySidebar onSelect={handleHistorySelect} />

      <div className="flex flex-1 flex-col overflow-hidden">
        <header className="border-b border-zinc-200 px-6 py-4 dark:border-zinc-700">
          <h1 className="text-lg font-semibold text-zinc-900 dark:text-zinc-100">
            SupaChat
          </h1>
          <p className="text-xs text-zinc-500">Blog analytics, conversationally</p>
        </header>

        <ChatWindow messages={state.messages} />

        <ChatInput onSubmit={handleSubmit} isLoading={state.isLoading} />
      </div>
    </div>
  );
}

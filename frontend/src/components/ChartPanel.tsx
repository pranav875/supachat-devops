"use client";

import {
  LineChart,
  Line,
  BarChart,
  Bar,
  PieChart,
  Pie,
  Cell,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from "recharts";

interface ChartPanelProps {
  chartType: "line" | "bar" | "pie" | "none";
  chartData: Record<string, unknown>[];
}

const COLORS = ["#3b82f6", "#10b981", "#f59e0b", "#ef4444", "#8b5cf6", "#ec4899"];

export default function ChartPanel({ chartType, chartData }: ChartPanelProps) {
  if (chartType === "none" || !chartData.length) {
    return (
      <p className="mt-3 text-sm text-zinc-400 dark:text-zinc-500">
        No data to visualize
      </p>
    );
  }

  const dataKeys = Object.keys(chartData[0]).filter((k) => k !== "name");

  if (chartType === "line") {
    return (
      <div className="mt-3 h-64 w-full">
        <ResponsiveContainer width="100%" height="100%">
          <LineChart data={chartData} margin={{ top: 5, right: 20, left: 0, bottom: 5 }}>
            <CartesianGrid strokeDasharray="3 3" className="stroke-zinc-200 dark:stroke-zinc-700" />
            <XAxis dataKey="name" tick={{ fontSize: 12 }} />
            <YAxis tick={{ fontSize: 12 }} />
            <Tooltip />
            <Legend />
            {dataKeys.map((key, i) => (
              <Line
                key={key}
                type="monotone"
                dataKey={key}
                stroke={COLORS[i % COLORS.length]}
                dot={false}
                strokeWidth={2}
              />
            ))}
          </LineChart>
        </ResponsiveContainer>
      </div>
    );
  }

  if (chartType === "bar") {
    return (
      <div className="mt-3 h-64 w-full">
        <ResponsiveContainer width="100%" height="100%">
          <BarChart data={chartData} margin={{ top: 5, right: 20, left: 0, bottom: 5 }}>
            <CartesianGrid strokeDasharray="3 3" className="stroke-zinc-200 dark:stroke-zinc-700" />
            <XAxis dataKey="name" tick={{ fontSize: 12 }} />
            <YAxis tick={{ fontSize: 12 }} />
            <Tooltip />
            <Legend />
            {dataKeys.map((key, i) => (
              <Bar key={key} dataKey={key} fill={COLORS[i % COLORS.length]} />
            ))}
          </BarChart>
        </ResponsiveContainer>
      </div>
    );
  }

  if (chartType === "pie") {
    return (
      <div className="mt-3 h-64 w-full">
        <ResponsiveContainer width="100%" height="100%">
          <PieChart>
            <Pie
              data={chartData}
              dataKey="value"
              nameKey="name"
              cx="50%"
              cy="50%"
              outerRadius={90}
              label={({ name, percent }) =>
                `${name} ${((percent ?? 0) * 100).toFixed(0)}%`
              }
            >
              {chartData.map((_, i) => (
                <Cell key={i} fill={COLORS[i % COLORS.length]} />
              ))}
            </Pie>
            <Tooltip />
            <Legend />
          </PieChart>
        </ResponsiveContainer>
      </div>
    );
  }

  return null;
}

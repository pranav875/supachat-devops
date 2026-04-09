"use client";

import {
  createColumnHelper,
  flexRender,
  getCoreRowModel,
  getSortedRowModel,
  SortingState,
  useReactTable,
} from "@tanstack/react-table";
import { useState, useMemo } from "react";

interface DataTableProps {
  columns: string[];
  rows: unknown[][];
}

export default function DataTable({ columns, rows }: DataTableProps) {
  const [sorting, setSorting] = useState<SortingState>([]);

  const columnHelper = createColumnHelper<Record<string, unknown>>();

  const tableColumns = useMemo(
    () =>
      columns.map((col) =>
        columnHelper.accessor(col, {
          header: col,
          cell: (info) => String(info.getValue() ?? ""),
        })
      ),
    [columns, columnHelper]
  );

  const data = useMemo(
    () =>
      rows.map((row) =>
        Object.fromEntries(columns.map((col, i) => [col, row[i]]))
      ),
    [rows, columns]
  );

  const table = useReactTable({
    data,
    columns: tableColumns,
    state: { sorting },
    onSortingChange: setSorting,
    getCoreRowModel: getCoreRowModel(),
    getSortedRowModel: getSortedRowModel(),
  });

  if (!rows.length) return null;

  return (
    <div className="mt-3 overflow-x-auto rounded-lg border border-zinc-200 dark:border-zinc-700">
      <table className="min-w-full text-sm">
        <thead className="bg-zinc-50 dark:bg-zinc-800">
          {table.getHeaderGroups().map((headerGroup) => (
            <tr key={headerGroup.id}>
              {headerGroup.headers.map((header) => (
                <th
                  key={header.id}
                  onClick={header.column.getToggleSortingHandler()}
                  className="cursor-pointer select-none px-4 py-2 text-left font-medium text-zinc-600 hover:text-zinc-900 dark:text-zinc-400 dark:hover:text-zinc-100"
                  aria-sort={
                    header.column.getIsSorted() === "asc"
                      ? "ascending"
                      : header.column.getIsSorted() === "desc"
                      ? "descending"
                      : "none"
                  }
                >
                  <span className="flex items-center gap-1">
                    {flexRender(header.column.columnDef.header, header.getContext())}
                    {header.column.getIsSorted() === "asc" && " ↑"}
                    {header.column.getIsSorted() === "desc" && " ↓"}
                  </span>
                </th>
              ))}
            </tr>
          ))}
        </thead>
        <tbody>
          {table.getRowModel().rows.map((row, i) => (
            <tr
              key={row.id}
              className={
                i % 2 === 0
                  ? "bg-white dark:bg-zinc-900"
                  : "bg-zinc-50 dark:bg-zinc-800/50"
              }
            >
              {row.getVisibleCells().map((cell) => (
                <td
                  key={cell.id}
                  className="px-4 py-2 text-zinc-700 dark:text-zinc-300"
                >
                  {flexRender(cell.column.columnDef.cell, cell.getContext())}
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

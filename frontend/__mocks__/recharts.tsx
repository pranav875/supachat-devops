// Mock recharts to avoid SVG/canvas issues in jsdom
import React from 'react'

const mockComponent = (name: string) => {
  const Comp = ({ children, ...props }: Record<string, unknown>) =>
    React.createElement('div', { 'data-testid': name, ...props }, children as React.ReactNode)
  Comp.displayName = name
  return Comp
}

export const ResponsiveContainer = ({ children }: { children: React.ReactNode }) =>
  React.createElement('div', { 'data-testid': 'ResponsiveContainer' }, children)
export const LineChart = mockComponent('LineChart')
export const BarChart = mockComponent('BarChart')
export const PieChart = mockComponent('PieChart')
export const Line = mockComponent('Line')
export const Bar = mockComponent('Bar')
export const Pie = mockComponent('Pie')
export const Cell = mockComponent('Cell')
export const XAxis = mockComponent('XAxis')
export const YAxis = mockComponent('YAxis')
export const CartesianGrid = mockComponent('CartesianGrid')
export const Tooltip = mockComponent('Tooltip')
export const Legend = mockComponent('Legend')

import '@testing-library/jest-dom'
import { render, screen } from '@testing-library/react'
import ChartPanel from '../ChartPanel'

const lineData = [
  { name: '2024-01-01', views: 100 },
  { name: '2024-01-02', views: 150 },
]

const barData = [
  { name: 'AI', views: 300 },
  { name: 'Tech', views: 200 },
]

const pieData = [
  { name: 'AI', value: 60 },
  { name: 'Tech', value: 40 },
]

describe('ChartPanel', () => {
  it('renders "No data to visualize" when chartType is "none"', () => {
    render(<ChartPanel chartType="none" chartData={lineData} />)
    expect(screen.getByText('No data to visualize')).toBeInTheDocument()
  })

  it('renders "No data to visualize" when chartData is empty', () => {
    render(<ChartPanel chartType="line" chartData={[]} />)
    expect(screen.getByText('No data to visualize')).toBeInTheDocument()
  })

  it('renders a LineChart for chartType "line"', () => {
    render(<ChartPanel chartType="line" chartData={lineData} />)
    expect(screen.getByTestId('LineChart')).toBeInTheDocument()
  })

  it('does not render BarChart or PieChart for chartType "line"', () => {
    render(<ChartPanel chartType="line" chartData={lineData} />)
    expect(screen.queryByTestId('BarChart')).not.toBeInTheDocument()
    expect(screen.queryByTestId('PieChart')).not.toBeInTheDocument()
  })

  it('renders a BarChart for chartType "bar"', () => {
    render(<ChartPanel chartType="bar" chartData={barData} />)
    expect(screen.getByTestId('BarChart')).toBeInTheDocument()
  })

  it('does not render LineChart or PieChart for chartType "bar"', () => {
    render(<ChartPanel chartType="bar" chartData={barData} />)
    expect(screen.queryByTestId('LineChart')).not.toBeInTheDocument()
    expect(screen.queryByTestId('PieChart')).not.toBeInTheDocument()
  })

  it('renders a PieChart for chartType "pie"', () => {
    render(<ChartPanel chartType="pie" chartData={pieData} />)
    expect(screen.getByTestId('PieChart')).toBeInTheDocument()
  })

  it('does not render LineChart or BarChart for chartType "pie"', () => {
    render(<ChartPanel chartType="pie" chartData={pieData} />)
    expect(screen.queryByTestId('LineChart')).not.toBeInTheDocument()
    expect(screen.queryByTestId('BarChart')).not.toBeInTheDocument()
  })

  it('renders ResponsiveContainer for line chart', () => {
    render(<ChartPanel chartType="line" chartData={lineData} />)
    expect(screen.getByTestId('ResponsiveContainer')).toBeInTheDocument()
  })

  it('renders ResponsiveContainer for bar chart', () => {
    render(<ChartPanel chartType="bar" chartData={barData} />)
    expect(screen.getByTestId('ResponsiveContainer')).toBeInTheDocument()
  })

  it('renders ResponsiveContainer for pie chart', () => {
    render(<ChartPanel chartType="pie" chartData={pieData} />)
    expect(screen.getByTestId('ResponsiveContainer')).toBeInTheDocument()
  })
})

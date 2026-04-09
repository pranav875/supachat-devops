import '@testing-library/jest-dom'
import { render, screen } from '@testing-library/react'
import ChatBubble from '../ChatBubble'

const lineData = [{ name: '2024-01-01', views: 100 }]

describe('ChatBubble', () => {
  it('renders the message content', () => {
    render(<ChatBubble role="user" content="Hello world" />)
    expect(screen.getByText('Hello world')).toBeInTheDocument()
  })

  it('renders error styling when isError is true', () => {
    const { container } = render(
      <ChatBubble role="assistant" content="Something went wrong" isError />
    )
    const bubble = container.querySelector('.text-red-700, .text-red-300')
    expect(bubble).toBeInTheDocument()
  })

  it('renders error message text', () => {
    render(<ChatBubble role="assistant" content="Something went wrong" isError />)
    expect(screen.getByText('Something went wrong')).toBeInTheDocument()
  })

  it('does not render DataTable or ChartPanel when isError is true', () => {
    render(
      <ChatBubble
        role="assistant"
        content="Error"
        isError
        columns={['col']}
        rows={[['val']]}
        chartType="bar"
        chartData={[{ name: 'x', value: 1 }]}
      />
    )
    expect(screen.queryByRole('table')).not.toBeInTheDocument()
    expect(screen.queryByTestId('BarChart')).not.toBeInTheDocument()
  })

  it('renders DataTable when rows and columns are provided for assistant', () => {
    render(
      <ChatBubble
        role="assistant"
        content="Here are results"
        columns={['title', 'views']}
        rows={[['Article A', 100]]}
      />
    )
    expect(screen.getByRole('table')).toBeInTheDocument()
    expect(screen.getByText('Article A')).toBeInTheDocument()
  })

  it('does not render DataTable when rows is empty', () => {
    render(
      <ChatBubble
        role="assistant"
        content="No results"
        columns={['title']}
        rows={[]}
      />
    )
    expect(screen.queryByRole('table')).not.toBeInTheDocument()
  })

  it('renders ChartPanel when chartType and chartData are provided', () => {
    render(
      <ChatBubble
        role="assistant"
        content="Here is a chart"
        chartType="line"
        chartData={lineData}
      />
    )
    expect(screen.getByTestId('LineChart')).toBeInTheDocument()
  })

  it('does not render ChartPanel for user role', () => {
    render(
      <ChatBubble
        role="user"
        content="My question"
        chartType="line"
        chartData={lineData}
      />
    )
    expect(screen.queryByTestId('LineChart')).not.toBeInTheDocument()
  })

  it('renders "No data to visualize" when chartType is "none"', () => {
    render(
      <ChatBubble
        role="assistant"
        content="No chart"
        chartType="none"
        chartData={[]}
      />
    )
    expect(screen.getByText('No data to visualize')).toBeInTheDocument()
  })

  it('aligns user bubble to the right', () => {
    const { container } = render(<ChatBubble role="user" content="Hi" />)
    expect(container.firstChild).toHaveClass('justify-end')
  })

  it('aligns assistant bubble to the left', () => {
    const { container } = render(<ChatBubble role="assistant" content="Hi" />)
    expect(container.firstChild).toHaveClass('justify-start')
  })
})

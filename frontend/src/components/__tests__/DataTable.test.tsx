import '@testing-library/jest-dom'
import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import DataTable from '../DataTable'

const columns = ['title', 'views']
const rows = [
  ['Article A', 100],
  ['Article B', 50],
  ['Article C', 200],
]

describe('DataTable', () => {
  it('renders column headers', () => {
    render(<DataTable columns={columns} rows={rows} />)
    expect(screen.getByText('title')).toBeInTheDocument()
    expect(screen.getByText('views')).toBeInTheDocument()
  })

  it('renders all rows', () => {
    render(<DataTable columns={columns} rows={rows} />)
    expect(screen.getByText('Article A')).toBeInTheDocument()
    expect(screen.getByText('Article B')).toBeInTheDocument()
    expect(screen.getByText('Article C')).toBeInTheDocument()
  })

  it('renders nothing when rows is empty', () => {
    const { container } = render(<DataTable columns={columns} rows={[]} />)
    expect(container.firstChild).toBeNull()
  })

  it('sorts the table when a column header is clicked', async () => {
    render(<DataTable columns={columns} rows={rows} />)
    const viewsHeader = screen.getByText('views')
    // Before sort: original order A=100, B=50, C=200
    const beforeCells = screen.getAllByRole('cell')
    const beforeTitles = beforeCells.filter((_, i) => i % 2 === 0).map((c) => c.textContent)
    expect(beforeTitles).toEqual(['Article A', 'Article B', 'Article C'])

    await userEvent.click(viewsHeader)
    // After one click the order changes (asc or desc depending on TanStack default)
    const afterCells = screen.getAllByRole('cell')
    const afterTitles = afterCells.filter((_, i) => i % 2 === 0).map((c) => c.textContent)
    // Order must differ from original
    expect(afterTitles).not.toEqual(['Article A', 'Article B', 'Article C'])
  })

  it('reverses sort order when column header is clicked a second time', async () => {
    render(<DataTable columns={columns} rows={rows} />)
    const viewsHeader = screen.getByText('views')
    await userEvent.click(viewsHeader)
    const firstClickCells = screen.getAllByRole('cell')
    const firstClickTitles = firstClickCells.filter((_, i) => i % 2 === 0).map((c) => c.textContent)

    await userEvent.click(viewsHeader)
    const secondClickCells = screen.getAllByRole('cell')
    const secondClickTitles = secondClickCells.filter((_, i) => i % 2 === 0).map((c) => c.textContent)

    expect(secondClickTitles).not.toEqual(firstClickTitles)
  })

  it('sets aria-sort attribute on sorted column', async () => {
    render(<DataTable columns={columns} rows={rows} />)
    const viewsHeader = screen.getByRole('columnheader', { name: /views/i })
    expect(viewsHeader).toHaveAttribute('aria-sort', 'none')
    await userEvent.click(viewsHeader)
    // After first click it should be either ascending or descending
    const sortAfterFirst = viewsHeader.getAttribute('aria-sort')
    expect(['ascending', 'descending']).toContain(sortAfterFirst)
    await userEvent.click(viewsHeader)
    const sortAfterSecond = viewsHeader.getAttribute('aria-sort')
    // Should be the opposite direction
    expect(sortAfterSecond).not.toBe(sortAfterFirst)
    expect(['ascending', 'descending']).toContain(sortAfterSecond)
  })
})
